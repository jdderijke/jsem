#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog_Pandas multiple dps.py
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
from enum import Enum

import sqlite3
# import urllib3
# from bs4 import BeautifulSoup
# import json
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

CWD=(os.path.dirname(os.path.realpath(__file__)))
DBFILE = "/Database/JSEM.db"

class DataSelection(Enum):
	All = 1
	_Last50 = -1
	_10min = 600
	_30min = 1800
	_1hr = 3600
	_2hr = 7200
	_6hr = 21600
	_12hr = 43200 
	_24hr = 86400
	_48hr = 172800
	Hour = 2
	Day = 3
	Week = 4
	Month = 5
	Year = 6


def Calculate_Period(data_selection=None, re_timestamp=None):
	'''
	This routine returns the START and END timestamps for the data_selection period selected 
	referenced from the re_timestamp provided or NOW is nothing is provided
	It return None, None if no timestamps can be calculated
	'''
	try:
		if data_selection is None: raise ValueError
		ts_now = time.time() if re_timestamp is None else int(re_timestamp)
		dt_now = datetime.fromtimestamp(ts_now)
		
		if data_selection in [DataSelection.All, DataSelection._Last50]:
			# no timestamps here
			return None,None
		elif data_selection in [DataSelection._48hr,DataSelection._24hr,DataSelection._12hr,
								DataSelection._6hr,DataSelection._2hr,DataSelection.Hour,
								DataSelection._10min, DataSelection._30min, DataSelection._1hr]:
			start_ts = ts_now - data_selection.value
			end_ts = ts_now
		elif data_selection == DataSelection.Day: 
			start_ts = int(datetime.timestamp(dt_now.replace(hour=0,minute=0,second=0)))
			end_ts = int(datetime.timestamp(dt_now.replace(hour=0,minute=0,second=0) + relativedelta(days=1))) - 1
		elif data_selection == DataSelection.Week:
			weekday = dt_now.weekday()
			weekday = weekday + 1 # correct weekday for sunday being the first day of the week rather than monday
			if weekday == 7: weekday = 0
			sunday_thisweek = dt_now.replace(hour=0,minute=0,second=0) - relativedelta(days=weekday)
			sunday_nextweek = sunday_thisweek + relativedelta(days=7)
			start_ts = int(datetime.timestamp(sunday_thisweek))
			end_ts = int(datetime.timestamp(sunday_nextweek)) - 1
		elif data_selection == DataSelection.Month: 
			start_ts = int(datetime.timestamp(dt_now.replace(day=1,hour=0,minute=0,second=0)))
			end_ts = int(datetime.timestamp(dt_now.replace(day=1,hour=0,minute=0,second=0) + relativedelta(months=1))) - 1
		elif data_selection == DataSelection.Year: 
			start_ts = int(datetime.timestamp(dt_now.replace(month=1,day=1,hour=0,minute=0,second=0)))
			end_ts = int(datetime.timestamp(dt_now.replace(month=1,day=1,hour=0,minute=0,second=0) + relativedelta(years=1))) - 1
		
		return start_ts, end_ts
	except Exception as err:
		print(str(err))


# def get_df_from_database(datapoints=[], maxrows=None, data_selection=DataSelection.Day, selected_enddate=datetime.now()):
def get_df_from_database(dpIDs=[], maxrows=None, data_selection=DataSelection.Day, selected_enddate=datetime.now()):
	
	CONN=sqlite3.connect(CWD+DBFILE, uri=True)
	try:
		if data_selection == DataSelection.All:
			# NOG DOEN: Bepaal het min(timestamp) en het max(timestamp) van alle DP's die opgehaald moeten worden
			query = "SELECT min(timestamp), max(timestamp) FROM 'Values' WHERE datapointID IN (%s)" % (",".join([str(x) for x in dpIDs]))
			print ('query: ' + query)
			data = CONN.execute(query)
			result = data.fetchone()
			starttimestamp, endtimestamp = result[0], result[1]
		else:
			starttimestamp, endtimestamp = Calculate_Period(data_selection=data_selection, re_timestamp=int(datetime.timestamp(selected_enddate)))

		# endtimestamp is de laatste timestamp BINNEN het bereik, we corrigeren hem naar de eerste BUITEN het bereik
		endtimestamp +=1
		filter_str = "AND timestamp >= %s AND timestamp < %s" % (str(starttimestamp), str(endtimestamp))
		print ("Aantal uren: %s" % ((endtimestamp - starttimestamp)/3600))

		if maxrows is not None:
			maxrows = int(maxrows)
			groupby_str = "GROUP BY timestamp * %s / (%s - %s)" % (maxrows, endtimestamp, starttimestamp)
		else:
			groupby_str = ""
			
		merge_df = pd.DataFrame({'timestamp': [int(starttimestamp + x*(endtimestamp-starttimestamp)/maxrows) for x in range(maxrows)]})
		merge_df = merge_df.astype({"timestamp":int})
		# print (merge_df)

		for dpID in dpIDs:
			query = "SELECT timestamp, value FROM 'Values' WHERE datapointID=%s %s %s ORDER BY timestamp" % (dpID, filter_str, groupby_str)
			print (query)
			# Get the data for this datapoint in a dataframe
			dp_df = pd.read_sql_query(query, CONN)
			dp_df = dp_df.rename(columns={'value':dpID})
			# dp_df = dp_df.drop(columns=['ID', 'datapointID'])
			# dp_df = epex_df.astype({dpID: dp.datatype, "timestamp":int})
			dp_df = dp_df.astype({"timestamp":int})
			# print (dp_df)
			
			# merge the data
			# merge_df = pd.merge_asof(merge_df, dp_df, on="timestamp", direction="backward")
			merge_df = pd.merge_asof(merge_df, dp_df, on="timestamp", direction="forward")
			print (merge_df)
			
			# input ("Any key...")
	except Exception as err:
		print (str(err))
	finally:
		CONN.close()


def main(args):
	# Set the Pandas print rows maximum to ALL, so all rows will be printed
	pd.set_option('display.max_rows', None)
	
	while True:
		dpID_str = input("Geef een datapointIDs op gescheiden door komma: ")
		maxrows = int(input("Geef het aantal resultaat rijen op: "))
		
		# print (dpID_str.strip().split(","))
		
		dpIDs = [int(x) for x in dpID_str.strip().split(",")]
		get_df_from_database(dpIDs, maxrows, DataSelection.All, datetime.now())
	
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
