#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Calculate dayly costs.py
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
import os
import sys
if __name__ == "__main__":
	__main__.logfilename = "General.log"
	__main__.backupcount = 3

# print (sys.path)
import os
from operator import itemgetter
from Common_Enums import *
from LogRoutines import Logger
from Config import DAYAHEAD_PRICES, ENVIRONMENT, LOGFILELOCATION, Loglevel, DB_RETRIES, DB_WAITBETWEENRETRIES, BTW_PERC

from JSEM_Commons import cursor_to_dict
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
from DB_Routines import get_value_from_database, store_value_in_database

CWD=(os.path.dirname(os.path.realpath(__file__)))
DBFILE = "/Database/JSEM.db"

# We need the ID's for the datapoints we use in the calculation
epex_data = 214
leba_data = 370
tot_use1 = 4
tot_use2 = 5
tot_ret1 = 6
tot_ret2 = 7
gas = 43

E_Energiebelasting = 242
E_Inkoopkosten = 268
E_netbeheer = 245
E_Leveringskosten = 246
E_Verm_Energiebelasting = 269
G_Energiebelasting = 372
G_Inkoopkosten = 373
G_netbeheer = 374
G_Leveringskosten = 375

stroomkosten_dag = 243
stroomkosten_uur = 257
stroomkosten_maand = 244
stroomkosten_jaar = 290

gaskosten_uur = 376
gaskosten_dag = 285
gaskosten_maand = 286
gaskosten_jaar = 291

stroomopbrengst_uur = 287
stroomopbrengst_dag = 288
stroomopbrengst_maand = 289
stroomopbrengst_jaar = 292

def load_settings():
	E_var, E_dag, G_var, G_dag = 0.0, 0.0, 0.0, 0.0
	
	# get the fixed prices for this calculation
	E_var = (
				 get_value_from_database(dpID=E_Energiebelasting) + 
				 get_value_from_database(dpID=E_Inkoopkosten)
				 )

	E_dag =  (
				  get_value_from_database(dpID=E_netbeheer) + 
				  get_value_from_database(dpID=E_Leveringskosten) + 
				  get_value_from_database(dpID=E_Verm_Energiebelasting)
				  )
	G_var = (
				  get_value_from_database(dpID=G_Energiebelasting) + 
				  get_value_from_database(dpID=G_Inkoopkosten) 
				)
				
	G_dag = (
				  get_value_from_database(dpID=G_netbeheer) + 
				  get_value_from_database(dpID=G_Leveringskosten)
					)
	# print ('dagopslag = %s' % round(E_dag,3))
	Settings= 	{"electricity":	{	'result':[stroomkosten_uur, stroomkosten_dag, stroomkosten_maand, stroomkosten_jaar], 
									'price':epex_data, 
									'dpIDs':[tot_use1, tot_use2], 
									'var':E_var, 
									'dag':E_dag},
				"gas":			{	'result':[gaskosten_uur, gaskosten_dag, gaskosten_maand, gaskosten_jaar],
									'price':leba_data, 
									'dpIDs':[gas], 
									'var':G_var, 
									'dag':G_dag},
				"teruglevering":{	'result':[stroomopbrengst_uur, stroomopbrengst_dag, stroomopbrengst_maand, stroomopbrengst_jaar], 
									'price':epex_data, 
									'dpIDs':[tot_ret1, tot_ret2], 
									'var':E_var, 
									'dag':0}
				}



	return Settings



def calculate_hourly_cost(target_hour = datetime.now(), category="electricity", store_results=True, setting=None):
	try:
		# Get the proper datetime and timestamp info
		begin_dt = target_hour.replace(minute=0, second=0, microsecond=0)
		if begin_dt > datetime.now(): return None, None, None
		begin_ts = int(begin_dt.timestamp())
		
		end_dt = begin_dt + relativedelta(hours=1)
		end_dt = min(end_dt, datetime.now())
		end_ts = int(end_dt.timestamp())
		
		# get the fixed costs for this commodity,
		if setting is None: 
			allsettings = load_settings()
			if category.lower() in allsettings: 
				setting = allsettings[category.lower()]
			else:
				Logger.error('Illegal argument category: %s' % category)
				return None, None, None

		# Get the pricing for this commodity, default to 0.0 if we have no price
		price = get_value_from_database(dpID=setting['price'], ts=begin_ts, tolerance=60)
		price = float(price) if price else 0.0
		
		# get the usage for that hour
		use_begin, use_end = 0.0, 0.0
		for dpID in setting['dpIDs']:
			# tmp1 = get_value_from_database(dpID=dpID, ts=begin_ts, tolerance=1800)
			# tmp2 = get_value_from_database(dpID=dpID, ts=end_ts, tolerance=1800)
			tmp1 = get_value_from_database(dpID=dpID, ts=begin_ts)
			tmp2 = get_value_from_database(dpID=dpID, ts=end_ts)
			if tmp1 is None or tmp2 is None: 
				Logger.warning('dpID %s-- Problems retrieving historical data, beginstand = %s, eindstand = %s' % (dpID, tmp1, tmp2))
				return None, None, None
			use_begin += tmp1
			use_end += tmp2
			# print('%s-- begin = %s, end = %s' % (dpID, tmp1, tmp2))
			
		verbruik = round(use_end - use_begin, 4)
		
		# calculate the total price, including fixed costs in euro per hour, PAS OP....prices zijn excl BTW
		
		variabel = round((verbruik * setting['var'])/100, 4)
		vast = round((setting['dag']/24), 4)
		consumption = round(((verbruik * price)/100)*(1+BTW_PERC/100), 4)
		hour_total = round(consumption + variabel + vast, 2)
			
		# the hourly use is always written with the timestamp of the START of the hour
		if store_results: store_value_in_database([(setting['result'][0], begin_ts, hour_total)])
		return hour_total, begin_ts, {'consumption':consumption,'variabel':variabel,'vast':vast,'verbruik':verbruik}

	except Exception as err:
		Logger.exception(str(err))
		return None, None, None
	
	

def calculate_daily_cost(target_day = datetime.now(), category="electricity", recalc_all=False, store_results=True, setting=None):
	'''
	We need to calculate per hour because the EPX price differs per hour, or we can just add the earlier caLculated hourly results
	'''
	try:
		# Get the proper datetime and timestamp info
		begin_dt = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
		if begin_dt > datetime.now(): return None, None, None
		begin_ts = int(begin_dt.timestamp())
		hour_ts = begin_ts
		
		end_dt = begin_dt + relativedelta(days=1)
		end_dt = min(end_dt, datetime.now())
		end_ts = int(end_dt.timestamp())
		
		# get the fixed costs,
		if setting is None: 
			allsettings = load_settings()
			if category.lower() in allsettings: 
				setting = allsettings[category.lower()]
			else:
				Logger.error('Illegal argument category: %s' % category)
				return None, None, None

		# initialise
		day_total, consumption, variabel, vast, verbruik = 0.0, 0.0, 0.0, 0.0, 0.0
		
		# for every hour in the target day
		while hour_ts < end_ts:
			if recalc_all: 
				# Recalculate all hourly costs and add the hourly totals to the day totals
				target_hour = datetime.fromtimestamp(hour_ts)
				hour_total, _, specs = calculate_hourly_cost(target_hour, category=category, store_results=store_results, setting=setting)
				if hour_total is None: 
					Logger.warning('No hourly cost calculated for hour %s' % target_hour)
				else:
					# add it to the day_total for today
					day_total += hour_total
					consumption += specs['consumption']
					variabel += specs['variabel']
					vast += specs['vast']
					verbruik += specs['verbruik']
			else:
				# add (earlier calculated) hourly costs (stored in DB), this way NO detail specs can be returned, just the total
				hour_total = get_value_from_database(dpID=setting['result'][0], ts=hour_ts, tolerance=60)
				if hour_total is not None: day_total += hour_total
				
			hour_ts += 60*60
			
		if store_results: store_value_in_database([(setting['result'][1], begin_ts, round(day_total,2))])
		if recalc_all:
			return day_total, begin_ts, {'consumption':round(consumption,4), 'variabel':round(variabel,4), 'vast':round(vast,4), 'verbruik':round(verbruik,4)}
		else:
			return day_total, begin_ts, {'consumption':None, 'variabel':None, 'vast':None, 'verbruik':None}
	except Exception as err:
		Logger.exception(str(err))
		return None, None, None



def calculate_monthly_cost(target_month = datetime.now(), category="electricity", recalc_all=False, store_results=True, setting=None):
	'''
	We need to calculate per hour because the EPX price differs per hour, or we can just add the earlier caLculated hourly results
	'''
	try:
		# Get the proper datetime and timestamp info
		begin_dt = target_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
		if begin_dt > datetime.now(): return None, None, None
		begin_ts = int(begin_dt.timestamp())
		day_ts = begin_ts
		
		end_dt = begin_dt + relativedelta(months=1)
		end_dt = min(end_dt, datetime.now())
		end_ts = int(end_dt.timestamp())

		# get the fixed costs,
		if setting is None: 
			allsettings = load_settings()
			if category.lower() in allsettings: 
				setting = allsettings[category.lower()]
			else:
				Logger.error('Illegal argument category: %s' % category)
				return None, None, None

		# initialise
		month_total, consumption, variabel, vast, verbruik = 0.0, 0.0, 0.0, 0.0, 0.0
		
		# for every day in the target range
		while day_ts < end_ts:
			target_day = datetime.fromtimestamp(day_ts)

			if recalc_all: 
				# Recalculate all daily and hourly costs and add the daily and hourly totals to the month totals
				day_total, day_ts, specs = calculate_daily_cost(target_day, category=category, recalc_all=recalc_all, 
																				store_results=store_results, setting=setting)
				if day_total is None:
					Logger.warning('No daily cost calculated for day %s' % target_day)
				else:
					# add it to the month_total for this month
					month_total += day_total
					consumption += specs['consumption']
					variabel += specs['variabel']
					vast += specs['vast']
					verbruik += specs['verbruik']
			else:
				# add (earlier calculated) daily costs (stored in DB), this way NO detail specs can be returned, just the total
				day_total = get_value_from_database(dpID=setting['result'][1], ts=day_ts, tolerance=60)
				if day_total is not None: month_total += day_total
				
			day_ts += 24*60*60 
			
		if store_results: store_value_in_database([(setting['result'][2], begin_ts, round(month_total,2))])
		if recalc_all:
			return month_total, begin_ts, {'consumption':round(consumption,4), 'variabel':round(variabel,4), 'vast':round(vast,4), 'verbruik':round(verbruik,4)}
		else:
			return month_total, begin_ts, {'consumption':None, 'variabel':None, 'vast':None, 'verbruik':None}
	except Exception as err:
		Logger.exception(str(err))
		return None, None, None



def main(*args):
	import readline
	try:
		while True:
			start_date: datetime = datetime.now()
			end_date: datetime = datetime.now()
			
			# end_date: datetime = datetime.now()
			startdate_str = input("Target FIRST date (if not %s) :" % start_date.strftime("%Y-%m-%d"))
			enddate_str = input("Target LAST date (if not %s) :" % start_date.strftime("%Y-%m-%d"))
			
			if startdate_str: start_date = datetime.strptime(startdate_str, "%Y-%m-%d")
			if enddate_str: end_date = datetime.strptime(enddate_str, "%Y-%m-%d")
			
			category = 'all'
			category_str = input('Which category (if not all)? ((E)lectricity | (G)as| (T)eruglevering | (A)ll')
			if category_str: category = category_str
			
			target_date = start_date
			while target_date.date() <= end_date.date():
				if category.lower() in ['e', 'electricity', 'a', 'all']:
					print(calculate_daily_cost(start_date, category='electricity', recalc_all=True, store_results=True))
				if category.lower() in ['g', 'gas', 'a', 'all']:
					print(calculate_daily_cost(start_date, category='gas', recalc_all=True, store_results=True))
				if category.lower() in ['t', 'teruglevering', 'a', 'all']:
					print(calculate_daily_cost(start_date, category='teruglevering', recalc_all=True, store_results=True))
					
				target_date = target_date + relativedelta(days=1)
				
			
			# print(calculate_monthly_cost(start_date, category=category, recalc_all=True, store_results=True))

			# print(calculate_hourly_cost(datetime.now().replace(hour=hour), category=category))
			
			# print(calculate_monthly_cost(datetime.now(), recalc_all=False, store_results=False))
	except KeyboardInterrupt as err:
		print('')
		input('Program terminated by user, hit any key....')
		
	return 0





if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
