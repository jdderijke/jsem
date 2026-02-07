
import __main__
from pathlib import Path

from common_utils import get_newest_file, normalize_data

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


# print(tflite_runtime.__version__)

def predict_heatingpower(store_in_db=False, **kwargs):
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
		# To make sure the whole dataframe is logged in the logfile... change the display settings of Pandas
		pd.set_option('display.max_columns', None)
		pd.set_option('display.width', 1000)
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
		Logger.info(f'---Calculated temp correction = {correction}, (over last {frcst_tempcorr_backlook} '
					f'hours after applying a timeshift of {frcst_timeshift} hours on the frcst)')


		# ===================== CREATE THE INPUT DATA SET AND APPLY CORRECTIONS =======================================
		# Het model is getraind met thermostaat setting en buitentemp_act, we maken een inputset met deze kolommen....
		startdate = datetime.now().replace(minute=0,second=0,microsecond=0)
		data_df = get_df_from_database(dpIDs=[frcst_temp], selected_startdate=startdate, add_datetime_column=True)
		
		# Logger.info(f'---the power predictions will be base on the following frcst:...\n{data_df}\n')

		
		# roomtemp_setp = get_value_from_database(dpID=DayTempSetpoint_52)
		roomtemp_setp = 19.0				# Tijdelijk, zolang de thermostaat nog niet is aangesloten
		data_df['roomtemp_setp'] = roomtemp_setp
		Logger.info(f'---Now making a power consumption prediction based on a thermostat setting of {roomtemp_setp}')
		
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
		# Logger.info(f'---the input dataset for the power predictions are:...\n{data_df}\n')

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
		
		Logger.info(f'---the resulting power predictions are:...\n{results_df}\n')
		
		if store_in_db:
			Logger.info('---saving power predictions in JSEM DB')
			# save het resultaat in frcst_power
			store_df = pd.DataFrame()
			store_df['timestamp'] = results_df['timestamp']
			store_df['value'] = results_df['frcst_power']
			store_df['table'] = 'Values'
			store_df['datapointID'] = frcst_power
			store_df_in_database(store_df[['table', 'datapointID', 'timestamp', 'value']])
			Logger.info('---frcst_power stored in the database...')
		
		pd.reset_option('display.max_columns')
		return results_df
	except Exception as err:
		Logger.exception (str(err))


from Calculate_costs import load_settings
def optimizer(data_df: pd.DataFrame, pph: int):
	"""
	Calculates an optimal sequence of start and stop commands for the heatpump based on the epex market information and
	the forecasted power consumption of the house, including system losses.
	:param data_df: 	A dataframe containing the columns: timestamp, epex_info and frcst_power
						with a 1 hour step between the timestamps
	:param pph: Number indicating in how many parts every hour may be split when calculating the optimal
						run schedule of the heatpump
	:return: 			A dataframe containing the columns of the data_df dataframe added with the columns
						period, buf_cap, hp_run and hp_cost containing the period number, the buffer capacity at the end
						of each period (kWh) and the cost based on epex_info and fixed additions for every period.
	"""

	# Initialize and gather current buffer levels and boundaries
	buf_init = get_value_from_database(dpID=Act_Energy_Buf)
	buf_min  = get_value_from_database(dpID=Min_Energy_Buf)
	buf_max  = get_value_from_database(dpID=Max_Energy_Buf)
	buf_loss = get_value_from_database(dpID=Loss_Buffervat) / pph
	hp_power = HP_POWER / pph
	hp_usage = HP_USAGE / pph
	
	# Get the fixed additions to the epex price for the cost calculations
	fixed_cost = load_settings()
	kwh_opslag = fixed_cost["electricity"]['var']
	dag_opslag = fixed_cost["electricity"]['dag']

	Logger.info(f'---Started optimizer: act(init) buffer={buf_init}, buf_min={buf_min}, buf_max={buf_max}')
	Logger.info(f'---The length of the HP_plan will be {len(data_df)} hours, with a switching pph if {round(1 / pph, 2)} hours')
	Logger.info(f'---Used EPEX and Power_Frcst data: \n{data_df}\n')

	try:
		# Dataframe preparation
		timestamps = data_df['timestamp'].values.tolist()
		
		# The power forecast as well as the epex prices (for now) are PER HOUR. We need to convert them to the required pph.
		step = int(3600 / pph)
		new_ts = [x for y in timestamps for x in range(y, y + 3600, step)]
		new_df = pd.DataFrame({'timestamp': new_ts, 'datetime': [datetime.fromtimestamp(x) for x in new_ts]})
		
		data_df = new_df.merge(data_df[['timestamp', 'epex_info', 'frcst_power']], how='outer', on='timestamp')
		data_df['epex_info'] = data_df['epex_info'].ffill()
		data_df['frcst_power'] = data_df['frcst_power'].ffill() / pph
		
		# add some extra columns to store the results in
		data_df['period'] = [x for x in range(len(data_df))]
		# column for storing buffer capacity at the END of a period
		data_df['buf_cap'] = [None for x in range(len(data_df))]
		# column to indicate if the HP should run IN a period
		data_df['hp_runs'] = [0 for x in range(len(data_df))]
		# column for the costs of running the HP per period
		data_df['hp_cost'] = [0.0 for x in range(len(data_df))]
		data_df = data_df.astype({'period':int, 'buf_cap':float, 'hp_runs':int, 'hp_cost':float})
		
		period = 0  # The current active step/period
		prev_buf_cap = buf_init  # buffer capacity at the end of the previous step/period
		
		# iterate through all periods
		for period in range(len(data_df)):
			# Calculate the new buffer capacity at the end of this period if we do NOT run the HP
			data_df.at[period,'buf_cap'] = prev_buf_cap - data_df.at[period, 'frcst_power'] - buf_loss
			# would this be sufficient?
			if data_df.at[period,'buf_cap'] < buf_min:
				# No it will not... now look back what could be the EARLIEST period to replenish
				first_possible = period
				while first_possible >= 0:
					if data_df.at[first_possible,'buf_cap'] + hp_power > buf_max:
						break
					first_possible -= 1
				# coming out of the while loop we actually have the last impossible period, add 1 for the first possible period
				first_possible += 1
				# Slice the epex list for the periods that allow a replenishment, and find the cheapest period
				sub_list_epex = data_df.iloc[first_possible:period + 1]['epex_info'].values.tolist()
				# make a sorted list with the indexes of the cheapest moments in that epex list
				cheapest = sorted(range(len(sub_list_epex)), key=sub_list_epex.__getitem__)
				for index_min in cheapest:
					# now iterate through this sorted list (from cheap to more expensive)
					# and find the first period where the HP is not already planned to run
					if data_df.at[first_possible + index_min,'hp_runs'] == 0:
						data_df.at[first_possible + index_min,'hp_runs'] = 1
						# Add the energy we are adding in all periods following until we reach the period where we currently are
						for teller in range(first_possible + index_min, period + 1):
							data_df.at[teller,'buf_cap'] += hp_power
						data_df.at[first_possible + index_min,'hp_cost'] = (data_df.at[first_possible + index_min,'epex_info'] + kwh_opslag)  * hp_usage
						break
			prev_buf_cap = data_df.at[period,'buf_cap']
			
		data_df = data_df.round({'buf_cap':2, 'hp_cost':2})
		Logger.info(f'---A new optimized run_plan was made ending on: {data_df.iloc[-1]["datetime"]}')
		Logger.info(f'---# of periods: {len(data_df)}')
		Logger.info(f'---Total costs : {data_df["hp_cost"].sum()}')
		starts = (data_df['hp_runs'] & (data_df['hp_runs'] != data_df['hp_runs'].shift(1))).sum()
		Logger.info(f'---# of  starts: {starts}')
		return data_df
	except Exception as err:
		Logger.exception(err)

def make_hp_plan(power_forecast:pd.DataFrame=None, pph=4, store_in_db:bool=False):
	"""
	Creates a start-stop plan for the heatpump, optimized for costs and with a granularity (switching frequency) of maximal
	pph periods per hour. Setting pph too high may result in a nervous heatpump behaviour leading to manu start-stop sequences..
	It will get the epex prices from the DB from now till as far as available, either by prediction or by actual epex market data
	:param power_forecast: 		A dataframe with at least the columns timestamp and frcst_power containing the predicted
								heating power consumption of the house excluding system losses.
								The timestamp must have a stepsize of 1 hour
	:param pph: 				Periods Per Hour, a setting to force the optimizer to use a higher granularity then is available
								in the epex_info and/or frcst_power.
	:param store_in_db: 		Optionally store the plan in the database in order for the JSEM rule to implement it
	:return:
	"""
	from DB_Routines import store_value_in_database, get_value_from_database, get_df_from_database
	from JSEM_Commons import get_all_epexinfo
	
	# To make sure the whole dataframe is logged in the logfile... change the display settings of Pandas
	pd.set_option('display.max_columns', None)
	pd.set_option('display.width', 1000)

	now = datetime.now()
	begin = now.replace(minute=0, second=0)

	if power_forecast is not None:
		power_df = power_forecast
		Logger.info('---power_frcst passed as argument')
		# Logger.info(f'\n{power_df}\n')
	else:
		# build a dataframe met alle data nodig om een plan te berekenen
		power_df = get_df_from_database(dpIDs=[frcst_power], selected_startdate=begin, add_datetime_column=True)
		Logger.info('---power_frcst retrieved from database')
		# Logger.info(f'\n{power_df}\n')

	epex_df = get_all_epexinfo(start_dt=begin)
	data_df = epex_df.merge(power_df[['timestamp','frcst_power']], how='left', on='timestamp')
	plan_df = optimizer(data_df, pph)
	

	if store_in_db:
		Logger.info("---Store HP plan in JSEM DB")
		# save hp_plan en frcst_buffer_energie
		store_df = pd.DataFrame()
		store_df['timestamp'] = plan_df['timestamp']
		store_df['value'] = plan_df['hp_runs'].astype(int)
		store_df['table'] = 'Values'
		store_df['datapointID'] = hp_plan
		store_df_in_database(store_df[['table', 'datapointID', 'timestamp', 'value']])
		Logger.info('---hp_plan stored in the database...')
		
		store_df = pd.DataFrame()
		store_df['timestamp'] = plan_df['timestamp']
		store_df['value'] = plan_df['buf_cap']
		store_df['table'] = 'Values'
		store_df['datapointID'] = frcst_buffer_energie
		# skip hour=0 to avoid overwriting the previous forecast for the current hour buffer capacity with the actual
		# to avoid actuals and frcst buffer capacity for the current hour always to be 100% match
		store_df_in_database(store_df[1:][['table', 'datapointID', 'timestamp', 'value']])
		Logger.info('---frcst_buffer_energie stored in the database...')

	pd.reset_option('display.max_columns')
	return plan_df



def main(*args, **kwargs):
	try:
		Logger.info("predict_heatingpower started started by user....")
		power_forecast = predict_heatingpower(store_in_db=True)
		Logger.info("make_hp_plan started started by user....")
		make_hp_plan(power_forecast=power_forecast, pph=4, store_in_db=False)

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

