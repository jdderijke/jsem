#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  epexdata download.py
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
	 __main__.logfilename = "EPEX.log"
	 __main__.backupcount = 3
import os
import sys

# print (sys.path)
import os
import logging
from LogRoutines import Logger
import urllib3
from bs4 import BeautifulSoup
import json

#  CHROMEDRIVER_LOCATION,
from Config import DAYAHEAD_PRICES,ENVIRONMENT, LOGFILELOCATION, Loglevel
from JSEM_Commons import Waitkey
import pandas as pd
from DB_Routines import get_df_from_database, store_df_in_database
from datetime import date, datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from Datapoint_IDs import *
import pytz
# import locale


CWD=(os.path.dirname(os.path.realpath(__file__)))

# url = https://api.energyzero.nl/v1/energyprices?&fromDate=2023-02-05T23:00:00+00:00&tillDate=2023-02-06T22:59:59+00:00&interval=4&usageType=3&inclBtw=true

# url = "https://mijn.easyenergy.com/nl/api/tariff/getapxtariffs?startTimestamp=2023-07-17T22%3A00%3A00.000Z&endTimestamp=2023-07-18T22%3A00%3A00.000Z&includeVat=false"
# url = "https://mijn.easyenergy.com/nl/api/tariff/getlebatariffs?startTimestamp=2020-04-29T22%3A00%3A00.000Z&endTimestamp=2020-04-30T22%3A00%3A00.000Z&includeVat=false"

HEADERS = {'electricity': 'getapxtariffs', 'gas':'getlebatariffs'}
PROVIDERS = ['energyzero', 'easyenergy']

def get_epex_leba_data	(
						header="getapxtariffs", 
						provider="easyenergy",
						start_date=datetime.now(), 
						end_date=datetime.now(), 
						incl_vat=False, 
						make_csv=True, 
						store_in_db=True, 
						use_remote_JSEM_DB=False, 
						host=None, 
						port=None
						):
	try:
		if header == HEADERS['electricity']:
			data_column_header = 'epex_data'
			usageType = 1
			dpID = epex_data
		elif header == HEADERS['gas']:
			data_column_header = 'leba_data'
			usageType = 4
			dpID = leba_data
		else: raise Exception('Invalid header...%s' % header)
		

		local_tz = datetime.now(timezone.utc).astimezone().tzinfo
		# Set start_date to 00:00:00 and the end_date to 00:00:00 and convert to UTC
		utc_start_date: datetime = datetime(
											start_date.year,
											start_date.month,
											start_date.day,
											0,
											0,
											0,
											tzinfo=local_tz,
											).astimezone(timezone.utc)
											
		utc_end_date: datetime = datetime(
										end_date.year,
										end_date.month,
										end_date.day,
										0,
										0,
										0,
										tzinfo=local_tz,
										).astimezone(timezone.utc) + timedelta(days=1)
									
		startTimestamp = utc_start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
		endTimestamp = utc_end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
		includeVat = str(incl_vat).lower()

		if provider == "easyenergy":
			url = "https://mijn.easyenergy.com/nl/api/tariff/%s?startTimestamp=%s&endTimestamp=%s&includeVat=%s" % \
					(header, startTimestamp, endTimestamp, includeVat)
		elif provider == "energyzero":
			url = "https://api.energyzero.nl/v1/energyprices?&fromDate=%s&tillDate=%s&interval=4&usageType=%s&inclBtw=%s" % \
					(startTimestamp, endTimestamp, usageType, includeVat)
		Logger.info(f'URL: {url}')
		
		http = urllib3.PoolManager()
		response = http.request('GET', url)
		soup = BeautifulSoup(response.data, "html.parser")
		json_data = json.loads(soup.text)
		df = pd.DataFrame(json_data)
		
		# print(df)
		# Waitkey()
		
		if df.empty:
			raise Exception("No data was downloaded, maybe the site is late with publishing the data....")
		if len(df) < 23:
			raise Exception(f"Incorrect number of datarows ({len(df)}) was downloaded....")
		
		if provider == "energyzero":
			# Extract the info form the 'Prices' column
			df["TariffUsage"] = [x['price'] for x in df['Prices'].values]
			df["Timestamp"] = [x['readingDate'] for x in df['Prices'].values]

		df = df.rename(columns={"Timestamp":"UTC_datetime", "TariffUsage":data_column_header})
		
		df[data_column_header] = df[data_column_header] * 100.0
		df = df.round({data_column_header:2})
		
		df["timestamp"]=[int(datetime.strptime(x,"%Y-%m-%dT%H:%M:%S%z").timestamp()) for x in df["UTC_datetime"].values]
		df["datetime"] = [datetime.fromtimestamp(x) for x in df["timestamp"].values]
		
		df = df[['timestamp', 'datetime', data_column_header]]
		Logger.info(f'Succesfully downloaded {len(df)} records from: %s' % provider)
		# print(df)
		# input('Any key..')
		
		if store_in_db:
			tmp_df = df[['timestamp',data_column_header]]
			tmp_df['datapointID'] = dpID
			tmp_df['table'] = 'Values'
			tmp_df = tmp_df[['table','datapointID','timestamp',data_column_header]]
			tmp_df = tmp_df.rename(columns={data_column_header:'value'})
			Logger.info('Saving data in JSEM database:')
			store_df_in_database(df=tmp_df)
			Logger.info('Saving data in database finished:')
			
		if make_csv:
			filename = '%s-%s %s-%s.csv' % \
				(data_column_header, 'inclBTW' if incl_vat else 'exclBTW', 
				start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
			outdir = DAYAHEAD_PRICES
			if not os.path.exists(outdir): os.mkdir(outdir)
			fullname = os.path.join(outdir, filename)  
			Logger.info ("Saving csv file as %s" % fullname)  
			# input("Any key")
			df.to_csv(fullname, index=False, encoding='utf-8')
			Logger.info('Saving csv file finished:')
		
		return True
	except Exception as err:
		Logger.error(f"Failed: {err}")
		return False

def conv_2_dt(input_date):
	try:
		if type(input_date) == datetime:
			result = input_date
		elif type(input_date) == str and input_date.lower()=='today':
			result = datetime.now()
		elif type(input_date) == str and input_date.lower()=='tomorrow':
			result = datetime.now() + relativedelta(days=1)
		elif type(input_date) == str:
			result = datetime.strptime(input_date, "%Y-%m-%d")
	except:
		Logger.error("%s-- Argument input_date has to be datetime or valid datestring: yyyy-mm-dd, or TODAY or TOMORROW" % input_date)
		result = datetime.now()
	finally:
		return result


def main(*args, **kwargs):
	try:
		if len(kwargs) != 0:
			Logger.info('Started from CLI or Crontab, not interactive.....')
			# er zijn argumenten met de commandline meegegeven, dus automatisch script
			mode = kwargs.get('mode', "electricity").lower()
			Logger.info('Mode = %s .... ' % mode)
			if mode not in HEADERS:
				Logger.error('%s --Illegal mode... should be electricity or gas' % mode)
				return
			header = HEADERS[mode]
			
			start_date = kwargs.get('start_date', datetime.now())
			start_date = conv_2_dt(start_date)
			start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

			end_date = kwargs.get('end_date', None)
			if end_date is None: end_date = datetime(2099,12,31,0,0,0)
			end_date = conv_2_dt(end_date)
			end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
			
			make_csv = (kwargs.get("make_csv", "False") == "True")
			store_in_db = (kwargs.get("store_in_db", "True") == "True")
			incl_vat = (kwargs.get("incl_vat", "False") == "True")
			Logger.info('Get_epex_leba_data called with start_date: %s, end_date: %s, make_csv: %s, store_in_db: %s, incl_vat: %s' %
							(start_date,end_date,make_csv,store_in_db,incl_vat))

			for provider in PROVIDERS:
				if get_epex_leba_data(	header=header, provider=provider, start_date=start_date, end_date=end_date, 
										make_csv=make_csv, store_in_db=store_in_db, incl_vat=incl_vat):
					break

	
		else:
			# er zijn geen argumenten met de commandline meegeven...dus interactief
			Logger.info('Started from editor, interactive.....')
			header = HEADERS['electricity']
			if input('Electricity (E) or Gas (G) prices (default E) : ').lower()=='g': header = HEADERS['gas']
			
			start_date: datetime = datetime.now()
			end_date: datetime = datetime(2099,12,31,0,0,0)
			startdate_str = input("Start date (if not %s) :" % start_date.strftime("%Y-%m-%d"))
			if startdate_str: start_date = datetime.strptime(startdate_str, "%Y-%m-%d")
			
			enddate_str = input("End date (if not %s) :" % end_date.strftime("%Y-%m-%d"))
			if enddate_str: end_date = datetime.strptime(enddate_str, "%Y-%m-%d")
			
			for provider in PROVIDERS:
				if get_epex_leba_data(	header=header, provider=provider, start_date=start_date, end_date=end_date, 
										make_csv=True, store_in_db=True, incl_vat=False):
					break
										 

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
