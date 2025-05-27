#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog tflite inference.py
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
	 __main__.logfilename = "TFLite_Inference.log"
	 __main__.backupcount = 2
import os
import sys

import logging
from LogRoutines import Logger
from Config import LOGFILELOCATION, Loglevel

import tflite_runtime
import tflite_runtime.interpreter as tflite

from Holidaychecks import is_school_holiday, is_public_holiday
import sqlite3
# import pickle
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from pandas.api.types import is_numeric_dtype
import numpy as np
import time
import select
import errno
from DB_Routines import store_value_in_database, get_value_from_database
from DB_Routines import store_df_in_database, get_df_from_database
from Config import DBFILE
from Common_Data import CWD
from Config import TFLITE_MODELS
from Common_Routines import get_newest_file


print(tflite_runtime.__version__)

frcst_temp=273
frcst_wind=274
frcst_richting=275
frcst_bewolking=278
frcst_zoninstraling=279
epex_pred=334

weather_dpIDs = [frcst_temp,frcst_wind,frcst_richting,frcst_bewolking,frcst_zoninstraling]

def normalize_data(df):
	# Normalizes all numerical data in a dataframe, shifts each column by its mean and scales it by its stddev
	def shift_and_scale(col):
		if is_numeric_dtype(col):
			col = col - means[col.name]
			if stddevs[col.name]!=0.0: 
				col = col / stddevs[col.name]
		return col
		
	# first get the mean and stddev of each numeric column in the dataframe
	means = {}
	stddevs = {}
	for col in df.columns:
		if is_numeric_dtype(df[col]):
			means[col] = df[col].mean()
			stddevs[col] = df[col].std()
	# now shift the data by the mean per columns and scale by the stddev per columns
	result_df = df.apply(lambda x: shift_and_scale(x), axis=0)
	return result_df



def predict_epex(running_standalone=False, **kwargs):
	msg = kwargs.get('msg',None)
	if msg: Logger.info("message passed to routine: %s" % msg)
	#--------------------------internal routines----------------
	def model_inference(row, interpr, input_index, output_index):
		# print(row)
		input_data = np.array([row.values],dtype=np.float32)
		# input_data = [row.values]
		# print(input_data)
		# input('Any key')
		interpr.set_tensor(input_index, input_data)
		interpr.invoke()
		output_data = interpr.get_tensor(output_index)
		# print(output_data[0][0])
		# input('Any key')
		return np.squeeze(output_data)
	#---------------------------end internal routines------------
	
	try:
		# startdate = datetime.now().replace(hour=0, minute=0,second=0,microsecond=0) + relativedelta(days=1)
		startdate = datetime.now().replace(hour=0, minute=0,second=0,microsecond=0)
		
		weather_df = get_df_from_database(dpIDs=weather_dpIDs, selected_startdate=startdate, add_datetime_column=True)
	
		weather_df = weather_df.dropna()
		weather_df = weather_df.rename(columns={	'frcst_temp':'temp',
													'frcst_wind':'wind',
													'frcst_richting':'richting',
													'frcst_bewolking':'bewolking',
													'frcst_zoninstraling':'zoninstraling'})
													
		weather_df = weather_df.astype({'temp':float, 'wind':float, 'richting':float, 'bewolking':float, 'zoninstraling':float})
		Logger.info('Gathered all meteo data...')
		
		# now also add hod (hour of day) and dow/doy(day of week/year) and phol(public holiday) and shol (school holiday)
		weather_df['hod'] = [x.hour for x in weather_df['datetime']]
		weather_df['dow'] = [x.weekday() for x in weather_df['datetime']]
		weather_df['doy'] = [x.timetuple().tm_yday for x in weather_df['datetime']]
		weather_df['phol'] = [is_public_holiday(x) for x in weather_df['datetime']]
		weather_df['shol'] = [is_school_holiday(x) for x in weather_df['datetime']]	
		Logger.info('Expanded data with calender and holiday data...')
		
		# prepare a dataframe for the results
		results_df = weather_df[['timestamp','datetime']]
		# now reshuffle the columns to be in line with what the model expects
		weather_df = weather_df[['hod','dow','doy','phol','shol','temp','wind','richting','bewolking','zoninstraling']]
		# now normalize the data the same way the training set was normalized
		weather_df = normalize_data(weather_df)
		Logger.info('Normalized data...')
		# print(weather_df)
		# print(weather_df.dtypes)
		# input('Any key')
		
		model_file = get_newest_file(TFLITE_MODELS + "/*.tflite")
		Logger.info('Loading the latest TFLite model file: %s ...' % model_file)
		Logger.info('...and setting up the Interpreter...')
		interpreter = tflite.Interpreter(model_path=model_file)
		interpreter.allocate_tensors()
		
		# Get input and output tensors.
		input_details = interpreter.get_input_details()
		# print(input_details)
		# input('Any key')
		
		output_details = interpreter.get_output_details()
		# print(output_details)
		# input('Any key')
		
		Logger.info('Running inference on the input data and predicting epex prices...')
		results_df['epex_pred'] = weather_df.apply(lambda x: model_inference(x, interpreter, input_details[0]['index'], output_details[0]['index']), axis=1)
		
		print(results_df)
		print(results_df.dtypes)
		input('Any key')
		
		Logger.info('Saving precictions in JSEM DB')
		
		# save het plan in ev_plan
		results_df['table'] = 'Values'
		results_df['datapointID'] = epex_pred
		results_df = results_df.rename(columns={'epex_pred':'value'})
		store_df_in_database(results_df[['table', 'datapointID', 'timestamp', 'value']])
		Logger.info('New Epex Predictions calculated and succesfully stored in the database...')
		
		
		#------------------------------------- old stuff -------------------------------
		# # # Test the model on random input data.
		# # input_shape = input_details[0]['shape']
		# # # print(input_shape)
		# # # input('Any key')
	
		# # # input_data = np.array([[1.0,1.1,1.2,1.3,1.4,1.0,1.1,1.2,1.3,1.4]],dtype=np.float32)
		# # # input_data = np.array(np.random.random_sample(input_shape), dtype=np.float32)
		# # input_data = 
		# # # print(input_details[0]['index'])
		# # # input('Any key')
		# # interpreter.set_tensor(input_details[0]['index'], input_data)
		
		# # interpreter.invoke()
		
		# # # The function `get_tensor()` returns a copy of the tensor data.
		# # # Use `tensor()` in order to get a pointer to the tensor.
		# # output_data = interpreter.get_tensor(output_details[0]['index'])
		# # print(output_data)
		return 0
	except Exception as err:
		Logger.exception (str(err))
	finally:
		logging.shutdown()


def main(args):
	pd.set_option('display.min_rows', 100)
	pd.set_option('display.max_rows', 100)
	predict_epex(running_standalone=True, msg="Interactief via editor")


if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
