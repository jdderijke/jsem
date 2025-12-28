#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  JSON to CSV downloader.py
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
'''
see https://www.edureka.co/blog/web-scraping-with-python/
see https://stackoverflow.com/questions/53657215/running-selenium-with-headless-chrome-webdriver

Opmwerking:
Dit script wordt geautomatiseerd gerind door crontab...maar pas op dat je hem niet als root user uit laat voeren
want daar kan de chrome browser niet tegen en dan crasht het script.

If you want to run a script as a normal user: crontab -e,  en dan regel toevoegen (2 maal per dag):
45 11 * * * /usr/bin/python3 /home/pi/Desktop/slimmemeter-rpi/MeteoServer_Forecast.py pc=8141PR make_csv=True
45 23 * * * /usr/bin/python3 /home/pi/Desktop/slimmemeter-rpi/MeteoServer_Forecast.py pc=8141PR make_csv=True

(If you want to run your script as root: sudo crontab -e en dan dezelfde regels invoegen)

'''
import os
import sys
import __main__
CWD=(os.path.dirname(os.path.realpath(__file__)))
if __name__ == "__main__":
	logfilename = os.path.basename(__main__.__file__)
	logfilename = logfilename.split('.')[0] + '.log'
	__main__.logfilename = logfilename
	__main__.backupcount = 5

	print(sys.path)
	
from LogRoutines import Logger
from enum import Enum

from Config import LOGFILELOCATION, Loglevel
from Config import METEOSERVER_FORECASTS, METEOSERVER_KEY, METEOSERVER_URL, METEOSERVER_DEFAULT_LOCATION, METEOSERVER_DEFAULT_PC
# from Common_Enums import *
import sqlite3

import urllib3
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime
from DB_Routines import store_df_in_database
from Datapoint_IDs import *

meteofields = dict(
					temp=(frcst_temp, float),
					winds=(frcst_wind, float),
					windr=(frcst_richting, float),
					neersl=(frcst_neerslag, float),
					luchtd=(frcst_luchtdruk, float),
					tw=(frcst_bewolking, float),
					gr_w=(frcst_zoninstraling, float),
					icoon=(frcst_icoon, 'string'))
					
	
def get_meteoserver_forecast(	location=None,
								make_csv=True, 
								store_in_db=False, 
								use_remote_JSEM_DB=False, 
								host=None, 
								port=None,
								**kwargs):

	# check and read arguments
	msg = kwargs.get('msg',None)
	if msg: Logger.info(f'message passed to routine: {msg}')
	
	if location and ".json" in location:
		Logger.info("Retrieving forecast from JSON file: %s" % json_file)
		with open(json_file, 'r') as read_file:
			json_data = json.load(read_file)
		found_location = json_data["plaatsnaam"][0]["plaats"]
		Logger.info("Forecast succesfully retrieved from file %s, for location %s" % (json_file, found_location))

	else:
		if location and location[0:4].isdecimal(): 
			# postcode eerst
			pc = location.replace(" ", "").upper()[0:6]
			url = METEOSERVER_URL % ("pc="+pc, METEOSERVER_KEY)
			Logger.info("Retrieving forecast for postcode: %s" % pc)
		elif location: 
			url = METEOSERVER_URL % ("locatie="+location, METEOSERVER_KEY)
			Logger.info("Retrieving forecast for location: %s" % location)
		else:
			pc = METEOSERVER_DEFAULT_PC
			url = METEOSERVER_URL % ("pc="+pc, METEOSERVER_KEY)
			Logger.info("No valid postcode or locatie, using default postcode: %s" % pc)
		Logger.info("Retrieving forecast using URL: %s" % url)
		
		http = urllib3.PoolManager()
		response = http.request('GET', url)
		soup = BeautifulSoup(response.data, "html.parser")
		json_data = json.loads(soup.text)
		Logger.info("Forecast succesfully downloaded and converted")

	found_location = json_data["plaatsnaam"][0]["plaats"]
	meteo_data = pd.DataFrame(json_data["data"])
	
	# Store the CSV file as pure as possible from the original data, before any columns are dropped or renamed
	if make_csv:
		# Haal de tijd informatie uit de EERSTE timestamp in de JSON data
		now = datetime.fromtimestamp(int(json_data["data"][0]["tijd"]))
		outdir = METEOSERVER_FORECASTS
		csvname = found_location
		outname = now.strftime("%Y%m%d%H%M_Forecast_") + csvname + '.csv'
		if not os.path.exists(outdir): os.mkdir(outdir)
		fullname = os.path.join(outdir, outname)    

		Logger.info ("Generating CSV file...%s" % fullname)
		meteo_data.to_csv(fullname, index=False, encoding='utf-8')
		Logger.info ("CSV file generated")


	meteo_data["timestamp"] = meteo_data["tijd"].astype(int)
	# only keep de necessary columns
	meteo_data = meteo_data[['timestamp'] + [x for x in meteofields.keys()]]

	# and force the datatypes
	meteo_data = meteo_data.astype({k:v[1] for k,v in meteofields.items()})
	

	if store_in_db:
		Logger.info('Storing forecast to JSEM database:')
		for col in meteo_data:
			if col=='timestamp': continue
			tmp_df = meteo_data[['timestamp', col]].copy()
			tmp_df['datapointID'] = meteofields[col][0]
			tmp_df['table'] = 'Values'
			tmp_df = tmp_df[['table','datapointID','timestamp',col]]
			tmp_df = tmp_df.rename(columns={col:'value'})
			
			store_df_in_database(df=tmp_df, use_remote_JSEM_DB=use_remote_JSEM_DB, host=host, port=port)
		
		Logger.info(f'Succesfully loaded {len(meteo_data)} records for {len(meteo_data.columns)-1} fields in the JSEM database...')
		
	return meteo_data



def main(*args, **kwargs):
	# print (kwargs)
	# Waitkey()
	max_retries = 3
	try:
		if len(kwargs) != 0:
			Logger.info("MeteoServer_Forecast started from crontab or CLI command")
			# er zijn argumenten met de commandline meegegeven, dus automatisch script
			
			location = kwargs.get('location', None)
			make_csv = kwargs.get("make_csv", '').lower()=='true'
			store_in_db = kwargs.get("store_in_db", '').lower()=='true'
			Logger.info(f'CLI args where: location={location}, make_csv={make_csv}, store_in_db={store_in_db}...')
			
			for retry in range(max_retries):
				try:
					Logger.info(f'Attempt {retry+1}')
					result = get_meteoserver_forecast(	msg='From crontab or CLI...',
														location=location, 
														make_csv=make_csv,
														store_in_db=store_in_db) 
					break
				except Exception as err:
					Logger.exception(f'Problem downloading: {err}')
					

		else:
			# er zijn geen argumenten met de commandline meegeven...dus interactief
			Logger.info("MeteoServer_Forecast started in interactive mode")
			select = input("Geef de naam van file (incl .json) of de postcode of de plaatsnaam op, (8141PR): ")
			make_csv = (input("Wilt u de resultaten ook als .csv file opslaan? (J/n)").lower() in ["j", ""])
			store_in_db = (input("Wilt u de resultaten als Forecast opslaan in de JSEM database? (J/n)").lower() in ["j", ""])
			
			# print ("getting forecast for location: %s, pc: %s, file: %s, and make_csv: %s" % (location, pc, json_file, make_csv))
			result = get_meteoserver_forecast(	msg='From interactive session...',
												location=select, 
												make_csv=make_csv,
												store_in_db=store_in_db) 
	except KeyboardInterrupt:
		Logger.error ("Cancelled from keyboard....")
	except Exception as err:
		Logger.exception (str(err))






if __name__ == '__main__':
	# python Epex_dayaheadprices.py foo bar hello=world 'with spaces'='a value'
	# sys.argv[0] is de naam van het script (in dit geval dus Epex_dayaheadprices.py)
	# sys.argv[1] .. sys.argv[n] zijn de argumenten daarna, gescheiden door spatie
	# met een truck (zie onder) kunnen we kwargs eruit destileren en met args en kwargs verdergaan
	sys.exit(main(sys.argv[0], **dict(arg.split('=') for arg in sys.argv[1:]))) # kwargs

