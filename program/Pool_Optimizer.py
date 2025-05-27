#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Pool_Optimizer.py
#  
#  Copyright 2023  <pi@raspberrypi>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import __main__
if __name__ == "__main__":
	 __main__.logfilename = "Pool_Optimzer.log"
	 __main__.backupcount = 2
import os
import sys

# print (sys.path)
import os
import logging
from LogRoutines import Logger

from Config import LOGFILELOCATION, Loglevel
from Config import DEFAULT_FILTERHOURS, POOL_WIDTH, POOL_LENGTH, POOL_DEPTH, POOL_TOPLAYER

from Config import DBFILE
from Common_Data import DATAPOINTS_ID, DATAPOINTS_NAME

# from Common_Enums import *
import sqlite3
# import urllib3
# from bs4 import BeautifulSoup
# import json
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
	
	
# dpIDs
epex_data = 214	# Datapoint ID of the Epex data
epex_pred = 334
frcst_zoninstraling = 279
frcst_wind = 274
AC_Power = 296
pool_filter_pump=314
pool_use_timer=315
pool_times=316
pool_setpoint_filterhours=317
pool_plan_time=318
pool_loadbal_prio=319
pool_epex_grens=320
pool_plan=322
pool_actual_filterhours=323
pool_use_strategy=329
pool_use_solarflush=330
pool_solar_absorption=331
pool_solarflush_dt=332
pool_overrule=348
pool_timerplan=349

pool_slottime = 1.0/6.0		# hours
pool_length = 12.0			# meter
pool_width = 5.0			# meter
pool_depth = 1.8			# meter
pool_toplayer = 0.1			# meter
pool_pump_capacity = 20		# m3/hour
pool_opp = pool_length * pool_width
pool_inhoud = pool_length * pool_width * pool_depth				# m3
pool_toplayer_inhoud = pool_length * pool_width * pool_toplayer	# m3

# voor de flushtime wordt ervan uitgegaan dat de pomp voor slechts 50% oppervlaktewater uit de toplayer trekt, de rest
# zou dan uit de bodem aansluiting of stofzuiger aansluiting komen
pool_flushtime = (pool_toplayer_inhoud / pool_pump_capacity) * 2	# in hours
# het aantal slots wat nodig is om de toplayer volledig door te spoelen is dan
pool_flushslots = int(pool_flushtime / pool_slottime)

Wh_per_m3_degree = 1161.1	# Wh/m3 C, aantal wattuur om 1 m3 1 graad te verwarmen


def make_timer_plan(running_standalone=False, **kwargs):
	'''
	Maakt een plan (AAN/UIT) voor de komende 7 dagen, startend NU, gebaseerd op de timerstring informatie
	'''
	from DB_Routines import store_df_in_database, get_df_from_database, get_value_from_database
	
	msg = kwargs.get('msg',None)
	if msg: Logger.info("message passed to routine: %s" % msg)
	
	# from DB_Routines import store_value_in_database, get_value_from_database

	days_ahead = 7
	planhours = days_ahead*24 + (24 - datetime.now().hour)
	
	# maak een leader dataframe met alle timestamps over de gehele plan periode
	timerplan_df = pd.DataFrame()
	start_ts = int(datetime.timestamp(datetime.now().replace(minute=0,second=0)))
	timerplan_df['timestamp'] = [start_ts + (3600*x) for x in range(planhours)]
	timerplan_df['datetime'] = [datetime.fromtimestamp(x) for x in timerplan_df['timestamp'].values]
	timerplan_df['timerplan'] = np.nan
	# print('timestamp leader')
	# print(timerplan_df)
	# input('Any key...')
	
	
	# get the latest times string
	
	if pool_times in DATAPOINTS_ID: times_str = DATAPOINTS_ID[pool_times].value
	else: times_str = get_value_from_database(dpID=pool_times)
	# times_str = "0:aan|6:uit|15:aan|16:uit|22:aan"

	times = times_str.split("|")
	for dag in range (days_ahead + 1):
		daily_df = pd.DataFrame()
		start_ts = int(datetime.timestamp(datetime.now().replace(hour=0,minute=0,second=0) + relativedelta(days=dag)))
		daily_df['timestamp'] = [start_ts + (3600 *x) for x in range(24)]
		daily_df['plan'] = 0
		
		
		prev_hour = None
		for time in times:
			hour = int(time.split(":")[0])
			if prev_hour and hour < prev_hour: raise Exception
			
			if time.split(":")[1].upper() in ["AAN", "ON", "1"]:
				daily_df['plan'][hour:] = 1
			elif time.split(":")[1].upper() in ["UIT", "OFF", "0"]:
				daily_df['plan'][hour:] = 0
			else:
				raise Exception
			prev_hour = hour
			# print('daily ontwikkeling')
			# print(daily_df)
			# input('Any key...')
			
		# timerplan_df = pd.merge_asof(timerplan_df, daily_df, on="timestamp", direction="backward", tolerance=1)
		timerplan_df = timerplan_df.merge(daily_df, how='left', left_on='timestamp', right_on='timestamp')
		timerplan_df['timerplan'] = timerplan_df[['timerplan','plan']].any(axis='columns')
		timerplan_df = timerplan_df.drop(columns=['plan'])
		# print('timerplan ontwikkeling')
		# print(timerplan_df)
		# input('Any key...')
	
	
	timerplan_df['timerplan'] = timerplan_df['timerplan'].astype(int)
	# save het plan in timerplan
	
	timerplan_df['table'] = 'Values'
	timerplan_df['datapointID'] = pool_timerplan
	timerplan_df = timerplan_df.rename(columns={'timerplan':'value'})
	store_df_in_database(timerplan_df[['table', 'datapointID', 'timestamp', 'value']])
	Logger.info('New pool timerplan stored in the database...')


def make_pool_plan(running_standalone=False, **kwargs):
	from DB_Routines import store_df_in_database, get_df_from_database, get_value_from_database
	from Common_Routines import get_all_epexinfo
	import math
	'''
	Calculates a 10-minute plan for the full 24 hour of the plandate.
	If solarflush is enabled it calculates how many flushes need to happen and when they are scheduled to happen.
	For the remaining filterhours (including the positive or negative carry_overs from previouw days) it finds the cheapest
	epex_prices for the plandate and schedules the filterpump accordingly.
	This optimizer runs ONLY ONCE per day, shortly after midnight so that the new epex prices are available AND the actual pumphours 
	are known for the previous day.
	'''
	
	# Set the Pandas print rows maximum to ALL, so all rows will be printed
	pd.set_option('display.max_rows', 200)
	
	msg = kwargs.get('msg',None)
	if msg: Logger.info("message passed to routine: %s" % msg)
	
	# First, get the actual optimizer settings, when running in stand_alone mode DATAPOINTS_ID will be empty
	if pool_actual_filterhours in DATAPOINTS_ID: act_filterhours = DATAPOINTS_ID[pool_actual_filterhours].value
	else: act_filterhours = get_value_from_database(dpID=pool_actual_filterhours)
		
	if pool_plan_time in DATAPOINTS_ID: plan_time = DATAPOINTS_ID[pool_plan_time].value
	else: plan_time = get_value_from_database(dpID=pool_plan_time)

	if pool_setpoint_filterhours in DATAPOINTS_ID: sp_filterhours = DATAPOINTS_ID[pool_setpoint_filterhours].value
	else: sp_filterhours = get_value_from_database(dpID=pool_setpoint_filterhours)

	if pool_use_solarflush in DATAPOINTS_ID: use_solarflush = DATAPOINTS_ID[pool_use_solarflush].value
	else: use_solarflush = get_value_from_database(dpID=pool_use_solarflush)

	Logger.info ("loaded settings plan_time: %s, sp_filterhours: %s, act_filterhours: %s, use_solarflush: %s" % 
						(plan_time, sp_filterhours, act_filterhours, use_solarflush))
						
	# Calculate the running balance: The sum of: (the actual filerhours for a given day MINUS the setpoint filterhours for that day)
	# look a maximum of plan_time back for this balancing
	#
	# TODO
														
	# first get a plan, make a timestamp leaderframe first (10 minute intervals), at least 1 week into the future from now for every hour
	# vandaag beginnen, dit uur nog meenemen
	plan_df = pd.DataFrame()
	plan_df_start_ts = int(datetime.now().replace(minute=0,second=0).timestamp())
	plan_df_end_ts = plan_df_start_ts + (7*24*60*60)
	plan_df['timestamp'] = [int(x) for x in range(plan_df_start_ts, plan_df_end_ts, 60*10)]
	plan_df['timestamp'] = plan_df['timestamp'].astype(int) 
	plan_df['datetime'] = [datetime.fromtimestamp(x) for x in plan_df['timestamp'].values]


	# Haal alle epex data en pred op, vandaag beginnen, de hele dag nog meenemen
	epex_df = get_all_epexinfo(start_dt=datetime.now().replace(minute=0,second=0), plan_hours=plan_time)
	plan_time = len(epex_df)
	# de epex_df is in uur stappen, we willen 10min stappen hebben, we gaan nieuwe timestamp en datetime columns maken
	epex_df = epex_df.drop(columns=['datetime'])
	tenmin_df = pd.DataFrame()
	tenmin_df['timestamp'] = [x for x in range(epex_df['timestamp'].min(), epex_df['timestamp'].max()+3600, 60*10)]
	tenmin_df['timestamp'] = tenmin_df['timestamp'].astype(int) 
	tenmin_df['datetime'] = [datetime.fromtimestamp(x) for x in tenmin_df['timestamp'].values]
	epex_df = pd.merge_asof(tenmin_df, epex_df[['timestamp','epex_info']], on="timestamp", direction="backward", tolerance=3600-10)
	epex_df['pool_plan'] = 0
	# print('epex opgerekt in 10 min timestamps')
	# print(epex_df)
	# input('Any key...')
	
	# now sort everything on ascending epex_data
	epex_df = epex_df.sort_values(by=['epex_info','timestamp'], ascending=True, ignore_index=True)
	# print(epex_df)
	# input('Any key...')

	# bepaal het aantal filterhours over de planperiode
	totalfilterhours = (sp_filterhours / 24) * plan_time
	if totalfilterhours <= 0.0: totalfilterhours = 0.0
	Logger.info ("Het aantal filterhours over de plan periode is %s" % totalfilterhours)
	
	ten_min_slots =  math.ceil((totalfilterhours * 60)/10)
	
	Logger.info ("Het aantal 10_min slots die hiervoor nodig zijn is %s" % ten_min_slots)
	
	if ten_min_slots > len(epex_df):
		Logger.info("Niet genoeg epex_info aanwezig of plan_time om plan volledig in te plannen...")
		ten_min_slots=len(epex_df)
	
	col_idx = epex_df.columns.get_loc('pool_plan')
	# iat and iloc accesses a row based on its integer position, not its label or index
	for x in range(ten_min_slots): epex_df.iat[x,col_idx] = 1
	
	epex_df = epex_df.sort_values(by=['timestamp'], ascending=True, ignore_index=True)
	
	# Join nu het plan in de plan_df
	# met een outer join/merge worden de rijen allemaal gecombineerd van beide dataframes, NaN voor missende values
	plan_df = pd.merge(plan_df, epex_df[['timestamp','pool_plan']], how='outer', on=['timestamp','timestamp'])
	# en werk de NaN entries weg en fix de datatype
	plan_df['pool_plan'] = plan_df['pool_plan'].replace(np.nan, 0)
	plan_df['pool_plan'] = plan_df['pool_plan'].astype(int)
	# print(plan_df)
	# input('Any key...')
	
	# save het plan in pool_plan
	plan_df['table'] = 'Values'
	plan_df['datapointID'] = pool_plan
	plan_df = plan_df.rename(columns={'pool_plan':'value'})
	store_df_in_database(plan_df[['table', 'datapointID', 'timestamp', 'value']])
	Logger.info('New pool plan stored in the database...')
	
	# Log the results
	# Make a readable layout of the poolplan for the logfile
	plan_df = plan_df[(plan_df['value']==1)]
	Logger.info('Filtering will take place in the following hours ...')
	Logger.info("Datum:uur       00      10      20      30      40      50")
	prtline = None
	uur = None
	for teller, row in plan_df.iterrows():
		if row.datetime.hour != uur:
			if prtline: Logger.info(prtline) 
			prtline = str(row.datetime.date()) + ":{:2d} ".format(row.datetime.hour)
			uur = row.datetime.hour
		prtline += "  {:5s} ".format(str(row.value))
	Logger.info(prtline)
	Logger.info('Pool_Optimizer finished successfully')
		
		
	
def main(*args, **kwargs):
	from Common_Routines import get_input
	# pd.set_option('display.min_rows', 100)
	# pd.set_option('display.max_rows', 100)
	
	try:
		if len(kwargs) != 0:
			Logger.info("Pool_Optimizer started from crontab or CLI command")
			# er zijn argumenten met de commandline meegegeven, dus automatisch script
			
			if kwargs.get("strategy", "").lower()=="timer":
				Logger.info ("Calculating pool_plan with epex strategy...")
				make_timer_plan(running_standalone=True, msg="via crontab of CLI")
			elif kwargs.get("strategy", "").lower()=="epex":
				Logger.info ("Calculating pool_timerplan...")
				make_pool_plan(running_standalone=True, msg="via crontab of CLI")
			else:
				Logger.info("No valid crontab or cli argument passed... should be: strategy=epex or strategy=timer")
			
		else:
			# er zijn geen argumenten met de commandline meegeven...dus interactief
			Logger.info("Pool_Optimizer started from editor.....")
			while True:
				if get_input("Voor welke strategie wilt u een poolplan maken? t(imer) of e(pex) : ", "e").lower()=='t': 
					make_timer_plan(running_standalone=True, msg="interactief via editor")
				else:
					make_pool_plan(running_standalone=True, msg="interactief via editor")
					
	except Exception as err:
		Logger.exception(str(err))
	finally:
		logging.shutdown()



if __name__ == '__main__':
	# python Pool_Optimizer.py foo bar hello=world 'with spaces'='a value'
	# sys.argv[0] is de naam van het script (in dit geval dus Pool_Optimizer.py)
	# sys.argv[1] .. sys.argv[n] zijn de argumenten daarna, gescheiden door spatie
	# met een truck (zie onder) kunnen we kwargs eruit destileren en met args en kwargs verdergaan
	sys.exit(main(sys.argv[0], **dict(arg.split('=') for arg in sys.argv[1:]))) # kwargs

