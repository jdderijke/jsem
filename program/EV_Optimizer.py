#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  EV_Optimizer.py
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
	 __main__.logfilename = "EV_Optimzer.log"
	 __main__.backupcount = 2
import os
import sys

# print (sys.path)
import os
import logging
from LogRoutines import Logger
from Config import LOGFILELOCATION, Loglevel
from Config import DBFILE
from Common_Routines import get_input, get_newest_file
from Common_Data import DATAPOINTS_NAME, DATAPOINTS_ID
from operator import itemgetter
from Datapoint_IDs import *

# from Common_Enums import *
import sqlite3
# import urllib3
# from bs4 import BeautifulSoup
# import json
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
# import Common_Data
from Common_Data import DATAPOINTS_NAME, DATAPOINTS_ID

import math

epex_data 			= 214		# epex_data
epex_pred 			= 334		# epex predictie

# EV_act_kmrange		= 335
EV_default_kmrange	= 336
EV_kwh_per_km		= 337
EV_min_kmrange		= 338
EV_min_laadtijd		= 339
EV_norm_laadtijd	= 350
EV_batt_cap			= 341
EV_charge_cap		= 342
# EV_plan				= 343

# the following is for testing purposes only
class dumdp(object):
	def __init__(self, value, *args, **kwargs):
		self.value = value

# EV_dps = [
		# (ev_act_kmrange, dumdp(226)),
		# (EV_default_kmrange, dumdp(150)),
		# (EV_kwh_per_km, dumdp(0.155)),
		# (EV_min_kmrange, dumdp(175)),
		# (EV_min_laadtijd, dumdp(24)),
		# (EV_norm_laadtijd, dumdp(72)),
		# (EV_batt_cap, dumdp(70)),
		# (EV_charge_cap, dumdp(10.7))
		# ]	



'''
The EV optimizer runs
- every time a car gets connected,
- after the new epex_data is available for the next day (dayahead prices)
- when the user changes data in de EV settings

It loads the epex_data (max till 23:00 hour next day) and appends this if possible with epex_pred data to a max of 48 hours 
beyond epex_data. So the max epex info will be from the moment the EV_optimizer runs till 72 hours past the coming midnight
the min epex info will be 24 hours past the coming midnight
- It uses the ev_act_kmrange from a setting (EV_default_kmrange), can be adjusted by the user.
- It uses a EV_min_kmrange (setting:user input) wich will be reached within EV_min_laadtijd
- It uses a max period (till fully charged) which is smaller or equal to the length of the epex_info available or the EV_norm_laadtijd

It will:
_Find the cheapest way to fully charge the car within the max period
-create an ev_plan (on/off) to control the charger in 1 hr intervals (epex and predictions dont change faster then 1 hour)

'''

	
def clr_ev_plan(running_standalone=False, **kwargs):
	from DB_Routines import store_df_in_database

	msg = kwargs.get('msg',None)
	if msg: Logger.info("message passed to routine: %s" % msg)

	# first get a plan, make a timestamp leaderframe first, at least 1 week into the future from now for every hour
	plan_df = pd.DataFrame()
	plan_df_start_ts = int(datetime.now().replace(minute=0,second=0).timestamp())
	plan_df_end_ts = plan_df_start_ts + (7*24*60*60)
	plan_df['timestamp'] = [int(x) for x in range(plan_df_start_ts, plan_df_end_ts, 60*60)]
	plan_df['timestamp'] = plan_df['timestamp'].astype(int) 
	plan_df['datetime'] = [datetime.fromtimestamp(x) for x in plan_df['timestamp'].values]
	plan_df['ev_plan'] = 0

	# save het cleared plan in ev_plan
	plan_df['table'] = 'Values'
	plan_df['datapointID'] = ev_plan
	plan_df = plan_df.rename(columns={'ev_plan':'value'})
	store_df_in_database(plan_df[['table', 'datapointID', 'timestamp', 'value']])
	Logger.info('EV charging plan cleared in the database...')
	
	# Trigger an update of the plan if it happens to be on any live chart....
	if ev_plan in DATAPOINTS_ID: DATAPOINTS_ID[ev_plan].value = DATAPOINTS_ID[ev_plan].value
	

def make_ev_plan(running_standalone=False, **kwargs):
	from DB_Routines import get_value_from_database, store_df_in_database
	from Common_Routines import get_all_epexinfo
	
	msg = kwargs.get('msg',None)
	if msg: Logger.info("message passed to routine: %s" % msg)

	
	# First, get the actual optimizer settings, when running in stand_alone mode DATAPOINTS_ID will be empty
	if EV_norm_laadtijd in DATAPOINTS_ID: norm_laadtijd = DATAPOINTS_ID[EV_norm_laadtijd].value
	else: norm_laadtijd = get_value_from_database(dpID=EV_norm_laadtijd)

	if EV_min_laadtijd in DATAPOINTS_ID: min_laadtijd = DATAPOINTS_ID[EV_min_laadtijd].value
	else: min_laadtijd = get_value_from_database(dpID=EV_min_laadtijd)

	if ev_act_kmrange in DATAPOINTS_ID: act_kmrange = DATAPOINTS_ID[ev_act_kmrange].value
	else: act_kmrange = get_value_from_database(dpID=ev_act_kmrange)

	if EV_min_kmrange in DATAPOINTS_ID: min_kmrange = DATAPOINTS_ID[EV_min_kmrange].value
	else: min_kmrange = get_value_from_database(dpID=EV_min_kmrange)

	if EV_kwh_per_km in DATAPOINTS_ID: kwh_per_km = DATAPOINTS_ID[EV_kwh_per_km].value
	else: kwh_per_km = get_value_from_database(dpID=EV_kwh_per_km)

	if EV_charge_cap in DATAPOINTS_ID: charge_cap = DATAPOINTS_ID[EV_charge_cap].value
	else: charge_cap = get_value_from_database(dpID=EV_charge_cap)

	if EV_batt_cap in DATAPOINTS_ID: batt_cap = DATAPOINTS_ID[EV_batt_cap].value
	else: batt_cap = get_value_from_database(dpID=EV_batt_cap)

	Logger.info ("loaded settings norm_laadtijd: %s, min_laadtijd: %s, act_kmrange: %s" % 
						(norm_laadtijd, min_laadtijd, act_kmrange))
	Logger.info ("loaded settings min_kmrange: %s, kwh_per_km: %s, charge_cap: %s, batt_cap: %s" % 
						(min_kmrange, kwh_per_km, charge_cap, batt_cap))

	# first get a plan, make a timestamp leaderframe first, at least 1 week into the future from now for every hour
	plan_df = pd.DataFrame()
	plan_df_start_ts = int(datetime.now().replace(minute=0,second=0).timestamp())
	plan_df_end_ts = plan_df_start_ts + (7*24*60*60)
	plan_df['timestamp'] = [int(x) for x in range(plan_df_start_ts, plan_df_end_ts, 60*60)]
	plan_df['timestamp'] = plan_df['timestamp'].astype(int) 
	plan_df['datetime'] = [datetime.fromtimestamp(x) for x in plan_df['timestamp'].values]

	epex_df = get_all_epexinfo(start_dt=datetime.now(), plan_hours=norm_laadtijd)

	kort_ts = plan_df_start_ts + (min_laadtijd * 60*60)
	
	Logger.info('Laadplan op basis van een act_kmrange van %s km' % act_kmrange)
	# We bepalen nu HOEVEEL we totaal moeten laden (in Kwh) = batt_cap - act_km*kwh_per_km
	total_kwh = batt_cap - (act_kmrange * kwh_per_km)
	Logger.info('Total kwh te laden: %s' % total_kwh)

	# en hoeveel we minimaal moeten laden binnen de min tijd = min_km*kwh_per_km - act_km*kwh_per_km
	min_kwh = min_kmrange * kwh_per_km - act_kmrange * kwh_per_km
	# als dat negatief is dan zitten we nog genoeg vol...meer dan het minimum dus kortladen niet nodig
	if min_kwh <= 0.0: min_kwh = 0.0
	Logger.info('Minimaal kwh te laden: %s' % min_kwh)
	
	# we kijken nu eerst hoe we binnen de minimum tijd het minimum het beste kunnen laden
	kort_df = epex_df[epex_df['timestamp'] <= kort_ts].sort_values(by=['epex_info'], ascending=True)
	kort_df['kort_plan'] = 0
	# bereken aantal uren nodig voor minimale range
	min_hours = math.ceil(min_kwh / charge_cap)
	Logger.info('Minimaal hours for min kwh te laden: %s' % min_hours)
	if min_hours > len(kort_df):
		Logger.info("Niet genoeg epex_info aanwezig om zelfs korte termijn plan volledig in te plannen...")
		min_hours=len(kort_df)
	
	col_idx = kort_df.columns.get_loc('kort_plan')
	# iat and iloc accesses a row based on its integer position, not its label or index
	for x in range(min_hours): kort_df.iat[x,col_idx] = 1

	kort_df = kort_df.sort_values(by=['timestamp'], ascending=True)
	# met een outer join/merge worden de rijen allemaal gecombineerd van beide dataframes, NaN voor missende values
	epex_df = pd.merge(epex_df, kort_df[['timestamp','kort_plan']], how='outer', on=['timestamp','timestamp'])
	
	# deze lading trekken we af van wat we in totaal moesten laden, en het restant boeken we zo gunstig mogelijk over de
	# gehele periode...
	total_kwh = total_kwh - min_kwh
	Logger.info('Restant kwh te laden: %s' % total_kwh)
	# we creeren eerst een set met de reeds gebruikte uren eruit gehaald...
	norm_df = epex_df[epex_df['kort_plan'] != 1].sort_values(by=['epex_info'], ascending=True)
	norm_df['norm_plan'] = 0
	# en berekenen hoeveel uren we nog moeten laden
	norm_hours = math.ceil(total_kwh /charge_cap)
	Logger.info('Uren om de rest te laden: %s' % norm_hours)
	if norm_hours > len(norm_df):
		Logger.info("Niet genoeg epex_info aanwezig om plan volledig in te plannen...")
		norm_hours=len(norm_df)
	col_idx = norm_df.columns.get_loc('norm_plan')
	# iat and iloc accesses a row based on its integer position, not its label or index
	for x in range(norm_hours): norm_df.iat[x,col_idx] = 1

	norm_df = norm_df.sort_values(by=['timestamp'], ascending=True)
	# met een outer join/merge worden de rijen allemaal gecombineerd van beide dataframes, NaN voor missende values
	epex_df = pd.merge(epex_df, norm_df[['timestamp','norm_plan']], how='outer', on=['timestamp','timestamp'])
	
	# en maak een nieuwe kolom die beide plannen combineert
	epex_df['ev_plan'] = ((epex_df['kort_plan']==1) | (epex_df['norm_plan']==1)).astype(int)
	# print('epex_df met korte en lange termijn plan erin gemerged')
	# print (epex_df)
	# input('Any key')
	
	# Join nu het plan in de plan_df
	# met een outer join/merge worden de rijen allemaal gecombineerd van beide dataframes, NaN voor missende values
	plan_df = pd.merge(plan_df, epex_df[['timestamp','ev_plan']], how='outer', on=['timestamp','timestamp'])
	# en werk de NaN entries weg en fix de datatype
	plan_df['ev_plan'] = plan_df['ev_plan'].replace(np.nan, 0)
	plan_df['ev_plan'] = plan_df['ev_plan'].astype(int)
	# print('plan_df met epex_df erin gemerged')
	# print (plan_df)
	# input('Any key')
	
	
	# save het plan in ev_plan
	plan_df['table'] = 'Values'
	plan_df['datapointID'] = ev_plan
	plan_df = plan_df.rename(columns={'ev_plan':'value'})
	store_df_in_database(plan_df[['table', 'datapointID', 'timestamp', 'value']])
	Logger.info('New EV charging plan stored in the database...')
	
	# Trigger an update of the plan if it happens to be on any live chart....
	if ev_plan in DATAPOINTS_ID: DATAPOINTS_ID[ev_plan].value = DATAPOINTS_ID[ev_plan].value
	
	# Log the results
	plan_df = plan_df[(plan_df['value']==1)]
	Logger.info('Charging will take place in the following hours ...')
	for index, row in plan_df.iterrows():
		Logger.info('%s' % row.datetime)
	Logger.info('EV_Optimizer finished successfully')
	
def main(args):

	# Set the Pandas print rows maximum to ALL, so all rows will be printed
	pd.set_option('display.max_rows', None)
	
	# # make the plan
	# clr_ev_plan(running_standalone=True, msg="Interactief via editor")
	make_ev_plan(running_standalone=True, msg="Interactief via editor")
	# get_all_epexinfo(datetime.now(), 2)
	
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
