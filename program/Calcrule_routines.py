#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Calcrule_routines.py
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
	__main__.backupcount = 5

# print (sys.path)
from LogRoutines import Logger

from Datapoint_IDs import *

import Common_Data
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from DB_Routines import store_value_in_database, get_value_from_database, get_df_from_database
from LogRoutines import Logger
# from EV_Optimizer import make_plan, clr_plan
from EV_Optimizer import make_ev_plan, clr_ev_plan

def mode3_state_change(new_state:str, old_state:str):
	# print('mode3_state_change called: new_state %s, old_state %s' % (new_state, old_state))
	dp=Common_Data.DATAPOINTS_ID
	if new_state in ['B1', 'B2', 'C1', 'C2', 'D1', 'D2'] and old_state in ['A','E','F']:
		Logger.info('A car was connected to the charging station...')
		# remember the current energy counter
		dp[start_session_energy].value = dp[total_energy].value
		
		# copy the default kmrange into the act_kmrange 
		Logger.info('ev_act_kmrange was: %s and is replaced by EV_default_kmrange: %s' % 
						(dp[ev_act_kmrange].value, dp[EV_default_kmrange].value))
		dp[ev_act_kmrange].value = dp[EV_default_kmrange].value
		make_ev_plan(msg='car connected, creating charging plan')
		
	elif new_state in ['A','E','F'] and old_state in ['B1', 'B2', 'C1', 'C2', 'D1', 'D2']:
		Logger.info('A car was dis-connected from the charging station...')
		clr_ev_plan(msg='car disconnected, plan cleared')
		
	return new_state


tot_use1_ID=4
tot_use2_ID=5
tot_ret1_ID=6
tot_ret2_ID=7
gasID=43

e_verbruik_dag=249
e_terug_dag=251
e_verbruik_mnd=255
e_terug_mnd=256

gas_verbruik_dag=253
gas_verbruik_mnd=284


tot_use1_ID=4
tot_use2_ID=5
tot_ret1_ID=6
tot_ret2_ID=7
e_verbruik_dag=249
e_terug_dag=251

def get_daily_gas(target_day = datetime.now(), store_results=False):
	try:
		begin_ts = int(datetime.timestamp(target_day.replace(hour=0, minute=0, second=0, microsecond=0)))
		end_ts = begin_ts + 24*60*60
		
		# get the usage for that day
		use_begin = get_value_from_database(dpID=gasID, ts=begin_ts)
		use_end =  get_value_from_database(dpID=gasID, ts=end_ts)
			
		use_total = use_end - use_begin

		if store_results: store_value_in_database([(gas_verbruik_dag, begin_ts, round(use_total,4))])

		return use_total, begin_ts
	except Exception as err:
		return None, None
	finally:
		pass


def get_monthly_gas(target_day = datetime.now(), store_results=False):
	try:
		begin_dt = target_day.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
		end_dt = begin_dt + relativedelta(months=1)
		
		begin_ts = int(datetime.timestamp(begin_dt))
		end_ts = int(datetime.timestamp(end_dt))
		
		# get the usage for that month
		use_begin = get_value_from_database(dpID=gasID, ts=begin_ts)
		use_end =  get_value_from_database(dpID=gasID, ts=end_ts)
			
		use_total = use_end - use_begin

		if store_results: store_value_in_database([(gas_verbruik_mnd, begin_ts, round(use_total,4))])

		return use_total, begin_ts
	except Exception as err:
		return None, None
	finally:
		pass




def get_daily_use(target_day = datetime.now(), store_results=False):
	try:
		begin_ts = int(datetime.timestamp(target_day.replace(hour=0, minute=0, second=0, microsecond=0)))
		end_ts = begin_ts + 24*60*60
		
		# get the usage for that day
		use_begin = 0.0
		use_end = 0.0
		for tot_use_ID in [tot_use1_ID, tot_use2_ID]:
			tmp1 = get_value_from_database(dpID=tot_use_ID, ts=begin_ts)
			use_begin += tmp1
			tmp2 = get_value_from_database(dpID=tot_use_ID, ts=end_ts)
			use_end += tmp2
			# print('%s-- begin = %s, end = %s' % (tot_use_ID, tmp1, tmp2))
			
		use_total = use_end - use_begin
		
		if store_results: store_value_in_database([(e_verbruik_dag, begin_ts, round(use_total,3))])

		return use_total, begin_ts
	except Exception as err:
		return None, None
	finally:
		pass
		
		
def get_monthly_use(target_day = datetime.now(), store_results=False):
	try:
		begin_dt = target_day.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
		end_dt = begin_dt + relativedelta(months=1)
		
		begin_ts = int(datetime.timestamp(begin_dt))
		end_ts = int(datetime.timestamp(end_dt))
		
		# get the usage for that month
		use_begin = 0.0
		use_end = 0.0
		for tot_use_ID in [tot_use1_ID, tot_use2_ID]:
			use_begin += get_value_from_database(dpID=tot_use_ID, ts=begin_ts)
			use_end +=  get_value_from_database(dpID=tot_use_ID, ts=end_ts)
			
		# print('hour: %s, use beginstand = %s' % (target_hour.hour, use_begin))
		# print('hour: %s, use eindstand = %s' % (target_hour.hour, use_end))
		use_total = use_end - use_begin

		if store_results: store_value_in_database([(e_verbruik_mnd, begin_ts, round(use_total,3))])

		return use_total, begin_ts
	except Exception as err:
		return None, None
	finally:
		pass
		



	
def get_daily_return(target_day = datetime.now(), store_results=False):
	try:
		begin_ts = int(datetime.timestamp(target_day.replace(hour=0, minute=0, second=0, microsecond=0)))
		end_ts = begin_ts + 24*60*60
		
		# get the returns for that day
		return_begin = 0.0
		return_end = 0.0
		for tot_return_ID in [tot_ret1_ID, tot_ret2_ID]:
			return_begin += get_value_from_database(dpID=tot_return_ID, ts=begin_ts)
			return_end +=  get_value_from_database(dpID=tot_return_ID, ts=end_ts)
			
		return_total = return_end - return_begin

		if store_results: store_value_in_database([(e_terug_dag, begin_ts, round(return_total,3))])

		return return_total, begin_ts
	except Exception as err:
		return None, None
	finally:
		pass


def get_monthly_return(target_day = datetime.now(), store_results=False):
	try:
		begin_dt = target_day.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
		end_dt = begin_dt + relativedelta(months=1)
		
		begin_ts = int(datetime.timestamp(begin_dt))
		end_ts = int(datetime.timestamp(end_dt))
		
		# get the returns for that month
		return_begin = 0.0
		return_end = 0.0
		for tot_return_ID in [tot_ret1_ID, tot_ret2_ID]:
			return_begin += get_value_from_database(dpID=tot_return_ID, ts=begin_ts)
			return_end +=  get_value_from_database(dpID=tot_return_ID, ts=end_ts)
			
		return_total = return_end - return_begin

		if store_results: store_value_in_database([(e_terug_mnd, begin_ts, round(return_total,3))])

		return return_total, begin_ts
	except Exception as err:
		return None, None
	finally:
		pass





	
def main(args):
	import readline
	try:
		while True:
			start_date: datetime = datetime.now()
			# end_date: datetime = datetime.now()
			startdate_str = input("Target date (if not %s) :" % start_date.strftime("%Y-%m-%d"))
			if startdate_str: start_date = datetime.strptime(startdate_str, "%Y-%m-%d")
			# enddate_str = input("End date (if not %s) :" % end_date.strftime("%Y-%m-%d"))
			# if enddate_str: end_date = datetime.strptime(enddate_str, "%Y-%m-%d")
			print(get_daily_use(start_date, store_results=False))
	except KeyboardInterrupt as err:
		print('')
		input('Program terminated by user, hit any key....')
		
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
