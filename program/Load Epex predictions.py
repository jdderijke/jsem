#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Load Epex predictions.py
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
	 __main__.logfilename = "Load_Predictions.log"
	 __main__.backupcount = 2
import os
import sys

# print (sys.path)
import os
import logging
from LogRoutines import Logger
from Config import LOGFILELOCATION, Loglevel, PREDICTIONS
from Config import LOOK_BACK_DAYS, CONFIDENCE_LEVEL, MINIMUM_VALID_SAMPLES, HEATCURVE, THERMOSTAT, TEMP_CORRECTION, POWERSTATS, MAX_DEVIATION

from Config import METEOSERVER_FORECASTS, METEOSERVER_KEY, METEOSERVER_URL, METEOSERVER_DEFAULT_LOCATION
from Config import DBFILE
from Common_Data import CWD
from Common_Routines import cursor_to_dict, get_input, get_newest_file
from Common_Data import DATAPOINTS_NAME, DATAPOINTS_ID
from Datapoint_IDs import *

from operator import itemgetter

# from Common_Enums import *
import sqlite3
# import urllib3
# from bs4 import BeautifulSoup
# import json
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta


epex_data = 214		# epex_data
epex_pred = 334		# epex_pred

frcst_temp = 273	# frcst_temp
Act_Energy_Buf = 87	# Act_Energy_Buf
frcst_buffer_energie = 280
frcst_power = 281
hp_plan = 282
hp_plan_costs = 283


def main(args):
	from DB_Routines import store_value_in_database, get_value_from_database
	

	stored_predictions = get_newest_file(CWD+PREDICTIONS+"/*.csv")
	if stored_predictions is None:
		Logger.error("No saved stored_predictions csv file was found in %s" % CWD+PREDICTIONS)
		return None
	Logger.info("Loading predictions from file: %s" % stored_predictions)
	pred_df = pd.read_csv(stored_predictions)
	
	print(pred_df)
	input("Any key...")

	Logger.info("Store predictions in database: %s" % (CWD+DBFILE))
	dpID_timestamp_values = []
	for index, row in pred_df.iterrows():
		dpID_timestamp_values.append((epex_pred, row['timestamp'], row['epex_pred']))

	print(dpID_timestamp_values)
	input("Any key...")

	store_value_in_database(dpID_timestamp_values=dpID_timestamp_values)
	Logger.info("Predictions stored..")
		
	
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
