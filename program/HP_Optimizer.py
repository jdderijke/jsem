#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog Panda with sqlite3.py
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
from pathlib import Path

from Common_Utils import get_newest_file, normalize_data

if __name__ == "__main__":
	 __main__.logfilename = "HP_Optimzer.log"
	 __main__.backupcount = 24
import os
import sys

# print (sys.path)
import logging
from LogRoutines import Logger
from Config import LOGFILELOCATION, Loglevel, HP_POWER, HP_USAGE
from Config import LOOK_BACK_DAYS, CONFIDENCE_LEVEL, MINIMUM_VALID_SAMPLES, HEATCURVE, THERMOSTAT, TEMP_CORRECTION, POWERSTATS, MAX_DEVIATION

from Config import METEOSERVER_FORECASTS, METEOSERVER_KEY, METEOSERVER_URL, METEOSERVER_DEFAULT_LOCATION
from Config import DBFILE
from Config import TFLITE_MODELS, frcst_timeshift, frcst_tempcorr_backlook
from Datapoint_IDs import *

# from JSEM_Commons import cursor_to_dict, get_input, get_newest_file
from Common_Data import DATAPOINTS_NAME, DATAPOINTS_ID
from Common_Enums import Aggregation, DatabaseGrouping, DataSelection

from operator import itemgetter

# from Common_Enums import *
import sqlite3
# import urllib3
# from bs4 import BeautifulSoup
import json
import pandas as pd
from pandas.api.types import is_numeric_dtype
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

import tflite_runtime
import tflite_runtime.interpreter as tflite

from Holidaychecks import is_school_holiday, is_public_holiday
import time
import select
import errno
from DB_Routines import store_value_in_database, get_value_from_database
from DB_Routines import store_df_in_database, get_df_from_database
# from JSEM_Commons import get_newest_file, normalize_data


print(tflite_runtime.__version__)



def predict_heatingpower(**kwargs):
	'''
	This routine predicts the heating_power consumption of the house taken from the buffer (Act_Power_01)
	For now this only works for positive power consumptions (heating), not for negative consumption (cooling)
	The routine is normally called as part of the HP optimizer.
	There is however a huge discrepoancy between the frcst_temp retrieved from the meteo dataset and the measured outside temperature
	(BuitenTemperatuur1, measured by the heat pump),
	This model uses the frcst_temp from the meteo dataset and DayTempSetpoint_52 (thermostat setting) as 
	training parameters and thus must be loaded at inference as well. The result is a predicted power consumption (frcst_power) which is fed 
	into the database...
	The result of inference on this model therefore is a power_frcst for Act_Power_01 that can be used by the HP_optimizer
	'''
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
		
	
	try:
		
		# ===================== PREPARE AND INITIALIZE ============================================
		model_file = get_newest_file(TFLITE_MODELS, "*_power_predictor.tflite")

		
		# ===================== CORRECTIONS ON THE INPUT DATA ============================================
		# We beginnen 6 uur geleden, halen de frcst_temp en de werkelijke temp op
		# de frcst_temp is alleen per uur en per hele graden beschikbaar, terwijl de BuitenTemperatuur_act veel vaker en veel nauwkeuriger
		# gemeten is. Door nu datagrouping per uur te doen en dan de mean aggregation te doen worden alle datapunten EERST gegroepeerd en 
		# ge-aggregeerd alvorens ze worden gemerged met het eerste datapunt (frcst_temp in dit geval...)
		startdate = datetime.now().replace(minute=0,second=0,microsecond=0) - relativedelta(hours=frcst_tempcorr_backlook)
		corr_df = get_df_from_database(dpIDs=[frcst_temp, BuitenTemperatuur_act],
											selected_startdate=startdate,
											selected_enddate=datetime.now().replace(minute=0,second=0,microsecond=0),
											datagrouping=DatabaseGrouping.Hour, 
											aggregation=Aggregation.Mean,
											add_datetime_column=True)
		
		corr_df['frcst_temp'] = corr_df['frcst_temp'].shift(frcst_timeshift)			# Move the forecast x hours earlier (-) or later (+)
		corr_df = corr_df.dropna()
		# bereken de gemiddelde afwijking tussen de forecast en de uur-gemiddelde metingen van de afgelopen 6 uur....
		corr_df['diff'] = corr_df['BuitenTemperatuur_act'] - corr_df['frcst_temp']
		correction = corr_df['diff'].sum() / len(corr_df)
		correction = round(correction, 1)
		Logger.info(f'Calculated temp correction = {correction}, (over last {frcst_tempcorr_backlook} '
					f'hours after applying a timeshift of {frcst_timeshift} hours on the frcst)')


		# ===================== CREATE THE INPUT DATA SET AND APPLY CORRECTIONS =======================================
		# Het model is getraind met thermostaat setting en buitentemp_act, we maken een inputset met deze kolommen....
		startdate = datetime.now().replace(minute=0,second=0,microsecond=0)
		data_df = get_df_from_database(dpIDs=[frcst_temp], selected_startdate=startdate, add_datetime_column=True)
		
		# roomtemp_setp = get_value_from_database(dpID=DayTempSetpoint_52)
		roomtemp_setp = 19.0				# Tijdelijk, zolang de thermostaat nog niet is aangesloten
		data_df['roomtemp_setp'] = roomtemp_setp
		Logger.info(f'Now making a power consumption prediction based on a thermostat setting of {roomtemp_setp}')
		
		# here we can apply the shift and make the calculated corrections to the frcst_temp
		data_df['frcst_temp'] = data_df['frcst_temp'].shift(frcst_timeshift)			# Move the forecast x hours earlier (-) or later (+)
		data_df = data_df.dropna()
		# creer nu een buitentemp kolom gebaseerd op de eerder bepaalde correctie t.o.v. de frcst
		data_df['BuitenTemperatuur_act'] = data_df['frcst_temp'] + correction
		Logger.info(f'---timeshift ({frcst_timeshift}) and temp correction ({correction}) applied over future buitentemp_act')


		# ===================== PREPARE THE RESULT SET ============================================
		# prepare a dataframe for the results based on the timestamps of the data_df
		results_df = data_df[['timestamp','datetime']]
		# for inference only keep columns that are needed
		data_df = data_df[['BuitenTemperatuur_act', 'roomtemp_setp']]
		# convert the whole dataframe (all the columns left) to float) and normalize the set
		data_df = data_df.astype(float)
		
		
		# ===================== NORMALIZE THE INPUT DATA ============================================
		normalization_settings_file = model_file.replace('.tflite','.json')
		if os.path.isfile(normalization_settings_file):
			Logger.info(f'---normalization settings file found: {normalization_settings_file}')
			# We have a settings file for normalization... so normalize the data, first opening and converting JSON file
			with open(normalization_settings_file) as json_file:
				normalization_settings = json.load(json_file)

			data_df,_ = normalize_data(data_df, normalize='mean_std', settings=normalization_settings)
			Logger.info(f'---data normalized using settings {normalization_settings}')


			
		# ===================== LOAD AND PREPARE THE INTERPRETER  ============================================
		interpreter = tflite.Interpreter(model_path=model_file)
		Logger.info('---loaded TFLite model file: %s into interpreter...' % model_file)
		
		interpreter.allocate_tensors()
		# Get input and output tensors.
		input_details = interpreter.get_input_details()
		# print(input_details)
		# input('Any key')
		output_details = interpreter.get_output_details()
		# print(output_details)
		# input('Any key')
		Logger.info('---tensors allocated, input and output details defined...')
		
		Logger.info('---running inference on the input data and predicting frcst_power...')
		results_df['frcst_power'] = data_df.apply(lambda x: model_inference(x, interpreter, input_details[0]['index'], output_details[0]['index']), axis=1)
		
		Logger.info('---saving power predictions in JSEM DB')
		
		# save het resultaat in frcst_power
		results_df['table'] = 'Values'
		results_df['datapointID'] = frcst_power
		results_df = results_df.rename(columns={'frcst_power':'value'})
		store_df_in_database(results_df[['table', 'datapointID', 'timestamp', 'value']])
		Logger.info('---new frcst_power Predictions calculated and succesfully stored in the database...')
		
		return 0
	except Exception as err:
		Logger.exception (str(err))



class optimizer_settings(object):
	def __init__(self, bufcap_start, buf_min, buf_max, hp_power, hp_usage, kwh_opslag, dag_opslag):
		self.bufcap_start = bufcap_start
		self.buf_min = buf_min
		self.buf_max = buf_max
		self.kwh_opslag = kwh_opslag
		self.dag_opslag = dag_opslag
		self.hp_power = hp_power
		self.hp_usage = hp_usage
		
	def __str__(self):
		return (f'''
				bufcap_start:{self.bufcap_start}, 
				buf_min:{self.buf_min}, 
				buf_max:{self.buf_max}, 
				kwh_opslag:{self.kwh_opslag}, 
				dag_opslag:{self.dag_opslag}, 
				hp_power:{self.hp_power}, 
				hp_usage:{self.hp_usage}
				''')


def optimizer(row, settings, data_df):
	'''
	Uiteindelijk hoeven we alleen voor het uur NU te bepalen of we gaan draaien of niet.
	Als dan de kwh_usage voor het komende uur hoger is dan wat er in het buffer zit (incl minimum eis), dan MOETEN we wel draaien
	Als we zouden draaien en daardoor zou (incl kwh_usage) het buffer boven het maximum uitkomen, dan mogen we NIET draaien.
	Verder, kijken we of er een laagste prijspunt in de toekomst is die ook lager dan nu is, zo nee, dan draaien maar
	ZO ja, kunnen we dat punt bereiken met de huidige buffer? Als dat zo is, dan wachten we op dat punt, dus niet draaien nu
	Als we dat punt niet kunnen bereiken, kunnen we dan het één na laagste punt wat nog steeds lager is dan nu bereiken? etc. etc.
	'''
	# print(f'settings = {settings}')
	# input('any key')
	
	# We noteren welk uur dit is en we vullen de start buffer capaciteit (berekend in de vorige row) in
	cur_hour = row['uur']
	row['buf_cap'] = settings.bufcap_start
	
	if row['frcst_power'] > row['buf_cap'] - settings.buf_min:
		# Als dan de frcst_power voor het komende uur hoger is dan wat er in het buffer zit (incl minimum eis), dan MOETEN we wel draaien
		row['draaien'] = True
	elif row['buf_cap'] + HP_POWER - row['frcst_power'] > settings.buf_max:
		# Als we zouden draaien en daardoor zou (incl kwh_usage) het buffer boven het maximum uitkomen, dan mogen we NIET draaien.
		row['draaien'] = False
	else:
		# Verder, kijken we of er een laagste prijspunt in de toekomst is hiervoor sorteren we het restant van de data_df in oplopende epex_prijs
		sorted_df = data_df[cur_hour:].sort_values(by=['epex_info'], ascending=[True])
		# ZO ja, kunnen we dat punt bereiken met de huidige buffer? Als dat zo is, dan wachten we op dat punt, dus niet draaien nu
		# Als we dat punt niet kunnen bereiken, kunnen we dan het één na laagste punt wat nog steeds lager is dan nu bereiken? etc. etc.
		for index, cheap_row in sorted_df.iterrows():
			cheap_hour = cheap_row['uur'] 
			if cheap_hour == cur_hour and cur_hour != (len(data_df) - 1):
				# We zijn bij het zoeken naar goedkope uren dit huidige uur tegen gekomen. Dat is natuurlijk altijd zo als we 
				# in het laatste uur zitten, in dat geval hoeft hij niet aan...anders wel
				row['draaien'] = True
				break
			# we tellen nu het verbruik op van alle uren tussen NU en de toekomstige cheaper_fit, als we dat kunnen halen... dan gaan we NIET aan
			if data_df[cur_hour:cheap_hour]['frcst_power'].sum() <= row['buf_cap'] - settings.buf_min:
				# UIT, we kunnen het goedkoopste tijdstip halen met ons huidige buffer en wachten dus daarop
				row['draaien'] = False
				break
			else:
				# We halen deze toekomstige cheaper fit niet... misschien de iets minder goedkope wel...
				pass
				
	# do some admin
	if cur_hour < (len(data_df) - 1):
		# Calculate the new initial buf_cap forthe next hour and store in the settings object
		if row['draaien']:
			settings.bufcap_start = row['buf_cap'] + settings.hp_power - row['frcst_power']
		else:
			settings.bufcap_start = row['buf_cap'] - row['frcst_power']
			
	# Now Calculate the cost for this hour
	row['cost'] = (settings.hp_usage * (row['epex_info'] + settings.kwh_opslag))/100.00 if row['draaien'] else 0.00
	return row


def maxgetal_met_aantalbits(b):
	return (1 << b) - 1

def recalc_bufcap(df, buf_init, buf_min, buf_max):
	'''
	recalculates the buffer capacity column in the dataframe
	return the recalculated dataframe AND and indicator if this dataframe is within specifications and boundaries
	'''
	df.loc[0,'buf_cap'] = buf_init
	# recalculate the buffer capacity column in the dataframe
	for step in range(len(df) - 1):
		if df.loc[step,'hp_plan']: 	df.loc[step+1,'buf_cap'] = df.loc[step,'buf_cap'] + df.loc[step,'hp_pwr'] - df.loc[step,'frcst_power']
		else: 						df.loc[step+1,'buf_cap'] = df.loc[step,'buf_cap'] - df.loc[step,'frcst_power']
	# See which rows are outside of the set boundaries... if any
	invalids = df[(df['buf_cap'] < buf_min) | (df['buf_cap'] > buf_max)]
	# return the recalculated dataframe AND and indicator if this dataframe is within specifications and boundaries
	return df, len(invalids)==0
	
	
def getnext_getal(getal, maxbits):
	'''
	returned het eerstvolgende getal met exact hetzelfde aantal gezette bits als het startgetal
	'''
	max_getal = maxgetal_met_aantalbits(maxbits)
	bitcount = format(getal, f'0{maxbits}b').count('1')
	for next_getal in range(getal+1 , max_getal+1):
		if format(next_getal, f'0{maxbits}b').count('1') == bitcount: 
			return next_getal

def make_hp_plan(store_plan=False):
	'''
	This routine makes a plan for the heatpump based on the frcst_power data stored in the database
	It will get the epex prices from the DB from now till as far as available (max 24 hours)
	It will store the resulting hp_plan in the DB per hour. 
	'''
	from DB_Routines import store_value_in_database, get_value_from_database, get_df_from_database
	from JSEM_Commons import get_all_epexinfo
	from Calculate_costs import load_settings
		
	now = datetime.now()
	begin = now.replace(minute=0, second=0)
	timestamp = int(datetime.timestamp(begin))
	
	# First, get the CURRENT (begin of the hour) content of the buffer, and the CURRENT min and max levels
	buf_init = get_value_from_database(dpID=Act_Energy_Buf, ts=timestamp)
	buf_min  = get_value_from_database(dpID=Min_Energy_Buf)
	buf_max  = get_value_from_database(dpID=Max_Energy_Buf)
	
	buf_loss = get_value_from_database(dpID=Loss_Buffervat, ts=timestamp)
	# Flow50_maxtemp = get_value_from_database(dpID=FlowTempMax_50, ts=timestamp)
	# buf_reftemp = get_value_from_database(dpID=Ref_Energy_Temp, ts=timestamp)
	
	
	# # Get the values for the last 2 hours for Act_Power_01 and their timestamps in a dataframe
	# Logger.info('Calculating new minimum and maximum buffer levels...')
	# Act_Power_df = get_df_from_database(dpIDs=[Act_Power_01], dataselection=DataSelection._2hr, dataselection_date=begin, add_datetime_column=True)
	#
	# if len(Act_Power_df) > 0:
	# 	# Calculate the AVERAGE hourly power consumption (incl losses) over the last 2 hours or shorter if no longer period is available.
	# 	# Set buf_min to be 1.5 times the calculated minimal hourly consumption
	# 	buf_min = (Act_Power_df['Act_Power_01'].mean() + buf_loss) * 1.5
	# 	buf_min = round(buf_min, 2)
	# else:
	# 	# But.....If we cant get a decent average then we default to a safe value for the buf_min.
	# 	Logger.warning(f'Unable to determine average powerconsumption over last 2 hours... using default value for Min_Energy_Buf')
	# 	buf_min = 6.0	# kWh
	#
	# # and update the DB value for Min_Energy_Buf
	# store_value_in_database(dpID_timestamp_values=[(Min_Energy_Buf, timestamp, buf_min)])
	# # syntax: store_value_in_database(dpID_timestamp_values)  -> dpID_timestamp_values is a list of tuples (datapointID, timestamp, value)
	#
	# Logger.info(f'New Min_Energy_Buf = {buf_min} Kwh, New Max_Energy_Buf = {buf_max}, both are stored in database')
	# # input('Any key')
	




	# build a dataframe met alle data nodig om een plan te berekenen
	power_df = get_df_from_database(dpIDs=[frcst_power], selected_startdate=begin, add_datetime_column=True)
	epex_df = get_all_epexinfo()
	# merge de power data tegen de epex data, gebruik de epex data als leading
	data_df = epex_df.merge(power_df[['timestamp','frcst_power']], how='left', on='timestamp')
	# voeg wat extra kolommen toe
	data_df['uur'] = [x for x in range(len(data_df))]
	# We maken ook een list waarin we de buffer nivos kunnen opslaan, te beginnen met buf_init
	data_df['buf_cap'] = [None for x in range(len(data_df))]
	# En we maken een draaien lijst die aangeeft of we moeten draaien (per uur)
	data_df['draaien'] = [False for x in range(len(data_df))]
	# En ook een cost lijst voor de kosten (per uur)
	data_df['cost'] = [0.0 for x in range(len(data_df))]
	
	# Get the fixed additions to the epex price for the cost calculations
	fixed_cost = load_settings()
	kwh_opslag = fixed_cost["electricity"]['var']
	dag_opslag = fixed_cost["electricity"]['dag']
	
	# door alle optimizer instellingen in een settings object te stoppen kunnen we o.a. de buf_cap by-reference meenemen en dus iedere cycle updaten
	opt_settings = optimizer_settings(bufcap_start=buf_init, buf_min=buf_min, buf_max=buf_max, 
										hp_power=HP_POWER, hp_usage = HP_USAGE,
										kwh_opslag=kwh_opslag, dag_opslag=dag_opslag)

	Logger.info(f'Started optimizer: act(init) buffer={buf_init}, buf_min={buf_min}, buf_max={buf_max}')
	Logger.info(f'The length of the HP_plan will be {len(data_df)} hours')
	# Logger.info(f'Used data: \n{data_df}\n')

	# optimize the dataframe using the row_based optimizer, data_df becomes a plan_df
	plan_df = data_df.apply(lambda x: optimizer(x, opt_settings, data_df), axis=1)
	plan_df = plan_df.round({'frcst_power':2, 'buf_cap':2, 'cost':2})

	# To make sure the whole dataframe is logged in the logfile... change the display settings of Pandas
	pd.set_option('display.max_columns', None)
	pd.set_option('display.width',1000)
	Logger.info(f'The resulting plan is: \n{plan_df}\n')
	pd.reset_option('display.max_columns')
	
	if store_plan:
		Logger.info(f"Store HP plan in database: {DBFILE}")
		
		# save hp_plan, hp_plan_costs en frcst_buffer_energie
		plan_df['table'] = 'Values'
		plan_df['datapointID'] = hp_plan
		plan_df['value'] = plan_df['draaien'].astype(int)
		store_df_in_database(plan_df[['table', 'datapointID', 'timestamp', 'value']])
		Logger.info('hp_plan stored in the database...')
		
		# plan_df['datapointID'] = hp_plan_costs
		# plan_df['value'] = plan_df['cost']
		# store_df_in_database(plan_df[['table', 'datapointID', 'timestamp', 'value']])
		# Logger.info('hp_plan_costs stored in the database...')
		
		plan_df['datapointID'] = frcst_buffer_energie
		plan_df['value'] = plan_df['buf_cap']
		# skip hour=0 to avoid overwriting the previous forecast for the current hour buffer capacity with the actual
		# to avoid actuals and frcst buffer capacity for the current hour always to be 100% match
		store_df_in_database(plan_df[1:][['table', 'datapointID', 'timestamp', 'value']])
		Logger.info('frcst_buffer_energie stored in the database...')

	return



def main(*args, **kwargs):
	try:
		Logger.info("HP_Optimizer started....")
		# er zijn argumenten met de commandline meegegeven, dus automatisch script
		predict_heatingpower(msg='Ran as preparation for HP_Optimizer...')
		make_hp_plan(store_plan=True)

	except KeyboardInterrupt:
		Logger.error ("Cancelled from keyboard....")
	except Exception as err:
		Logger.exception (str(err))
	finally:
		logging.shutdown()


if __name__ == '__main__':
	# python Epex_dayaheadprices.py foo bar hello=world 'with spaces'='a value'
	# sys.argv[0] is de naam van het script (in dit geval dus Epex_dayaheadprices.py)
	# sys.argv[1] .. sys.argv[n] zijn de argumenten daarna, gescheiden door spatie
	# met een truck (zie onder) kunnen we kwargs eruit destileren en met args en kwargs verdergaan
	sys.exit(main(sys.argv[0], **dict(arg.split('=') for arg in sys.argv[1:]))) # kwargs

