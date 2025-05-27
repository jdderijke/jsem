#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Meteoserver tools.py
#  
#  Copyright 2024 jandirk <jandirk@linux-develop>
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
import os
import sys
import __main__
CWD=(os.path.dirname(os.path.realpath(__file__)))
if __name__ == "__main__":
	logfilename = os.path.basename(__main__.__file__)
	logfilename = CWD + "/Logs/" + logfilename.split('.')[0] + '.log'
	__main__.logfilename = logfilename
	__main__.backupcount = 0
	# sys.path.append('/home/jandirk/Projects/Tensorflow/Common_TF_Routines')
	# sys.path.append('/home/jandirk/Projects/Tensorflow/Common')
	print(sys.path)
	
from LogRoutines import Logger

import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import math
from time import sleep
from Common_Routines import get_files
from DB_Routines import get_df_from_database, store_df_in_database
from Datapoint_IDs import *

				
def update_meteo_fields(meteofields={}, csv_path=CWD + "*.csv", use_remote_JSEM_DB=False, host='', port=0):
	'''
	Reads and loads all meteofiles from the meteoserver_dir that fit the criterium
	Keeps only the LATEST forecast for a specific timestamp (hour).
	
	Adds all keynames (keys) of the meteofields dictionary (if found in the meteoserver CSV files) to the JSEM database under the
	datapointID and datatype as listed in the dictionary under that key.
	 
	The receiving datapoints must first manually be created in the JSEM db!!! This program ONLY populates them
	
	This program can use a remote JSEM database, to enable set use_remote_JSEM_DB to True and specify Host en Port args
	
	'''
	Logger.info(f'Looking for files in: ..{csv_path.lstrip(CWD)}')
	all_frcst_files = get_files(path=csv_path, option='all')
	Logger.info(f'gathered {len(all_frcst_files)} filenames that fit the criterium')
	
	meteo_data = pd.concat(map(pd.read_csv, all_frcst_files))
	Logger.info(f'loaded and concatenated csv files, total {len(meteo_data)} records')

	meteo_data["timestamp"] = meteo_data["tijd"].astype(int)
							
	# sort by timestamp and offset to get the last forecast for a specific timestamp
	meteo_data = meteo_data.sort_values(by=['timestamp','offset'], ascending=[True, False])
	
	# Use only the latest forecast for a specific timestamp, throw away the rest
	meteo_data = meteo_data.groupby('timestamp').agg({k:'last' for k in meteofields.keys()}).reset_index()
	Logger.info(f'Only keep the LATEST forecast for a specific timestamp, remaining {len(meteo_data)} records')
														
	# # add a datetime column for readability
	# meteo_data["datetime"] = [datetime.fromtimestamp(x) for x in meteo_data["timestamp"].values]

	# only keep de necessary columns
	meteo_data = meteo_data[['timestamp'] + [x for x in meteofields.keys()]]

	# and force the datatypes
	meteo_data = meteo_data.astype({k:v[1] for k,v in meteofields.items()})
	
	# the column names are still not the JSEM column names, but DB store happens on Datapoint ID, not name
	# print(meteo_data)
	# meteo_data.dtypes
	
	for col in meteo_data:
		if col=='timestamp': continue
		tmp_df = meteo_data[['timestamp', col]].copy()
		tmp_df['datapointID'] = meteofields[col][0]
		tmp_df['table'] = 'Values'
		tmp_df = tmp_df[['table','datapointID','timestamp',col]]
		tmp_df = tmp_df.rename(columns={col:'value'})
		
		store_df_in_database(df=tmp_df, use_remote_JSEM_DB=use_remote_JSEM_DB, host=host, port=port)
	
	Logger.info(f'Succesfully loaded {len(meteo_data)} records for {len(meteo_data.columns)-1} fields in the JSEM database...')

	


meteofiles = CWD + '/MeteoServerForecasts/*_Veldhoek.csv'

meteofields = dict(
					temp=(frcst_temp, float),
					winds=(frcst_wind, float),
					windr=(frcst_richting, float),
					neersl=(frcst_neerslag, float),
					luchtd=(frcst_luchtdruk, float),
					tw=(frcst_bewolking, float),
					gr_w=(frcst_zoninstraling, float),
					icoon=(frcst_icoon, 'string'))


# HOST = '192.168.178.220'	# The server's hostname or IP address
# PORT = 65432				# The port used by the server
HOST = ''					# The server's hostname or IP address
PORT = 0					# The port used by the server
REMOTE_JSEM_DB = False

def main(args):
	print(update_meteo_fields.__doc__)
	print('Meteofields loading: meteofieldname:(DatapointID, datatype)')
	print()
	print(meteofields)
	print()
	print('If this field definition is not OK... stop this program and edit the meteofields dictionary first...')
	print()
	print(f'Program is set to run on remote_JSEM_database: {REMOTE_JSEM_DB}')
	print()
	print()
	input('any key, or cntrl C to quit')
	
	Logger.info(f'Running update_meteo_fields program: remote JSEM db:{REMOTE_JSEM_DB}, host:{HOST}, port:{PORT}')
	Logger.info(f'Running update_meteo_fields program: meteofields:{meteofields}')
	update_meteo_fields(meteofields=meteofields, csv_path=meteofiles, use_remote_JSEM_DB=REMOTE_JSEM_DB, host=HOST, port=PORT)
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
