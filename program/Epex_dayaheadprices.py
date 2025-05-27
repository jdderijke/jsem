#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Epex_dayaheadprices.py
#  
#  Copyright 2022  <pi@raspberrypi>
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

If you want to run a script as a normal user: crontab -e,  en dan regel toevoegen:
0 16 * * * /usr/bin/python3 /home/pi/Desktop/slimmemeter-rpi/Epex_dayaheadprices.py delivery_date=tomorrow make_csv=True datapointID=214

If you want to run your script as root: sudo crontab -e en dan dezelfde regel invoegen

'''
import __main__
if __name__ == "__main__":
	 __main__.logfilename = "EPEX.log"
	 __main__.backupcount = 3
import os
import sys

# print (sys.path)
import os
from LogRoutines import Logger
from Config import DAYAHEAD_PRICES, CHROMEDRIVER_LOCATION, ENVIRONMENT, LOGFILELOCATION, Loglevel
# from Common_Enums import *
import sqlite3

import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from Common_Routines import Waitkey

CWD=(os.path.dirname(os.path.realpath(__file__)))
DBFILE = "/Database/JSEM.db"

def get_epex_dayaheadprices(*args, **kwargs):
	# initisalise datastructure and constants
	
	day_ahead = {
				'Hours':[],
				'Buy_Volume':[], 
				'Sell_Volume':[], 
				'Volume':[], 
				'Price':[]
				}
	key_list = list(day_ahead.keys())
	
	
	# day_ahead = [[],
				 # [],
				 # [],
				 # [],
				 # []]
	result_data = None
	driver = None

	try:
		# check and read arguments
		make_csv = bool(kwargs.get("make_csv", False))
		
		# de epexspot website heeft alleen de dayahead prijzen van gisteren, vandaag en morgen.....waarbij de laatste dus pas savonds stabiel is.
		delivery_arg = kwargs.get("delivery_date", 'tomorrow')
		try:
			if type(delivery_arg) == datetime:
				deliv_datestr = delivery_arg.strftime("%Y-%m-%d")
				deliv_date = delivery_arg
			elif type(delivery_arg) == str and delivery_arg.lower()=='today':
				deliv_datestr = datetime.now().strftime("%Y-%m-%d")
				deliv_date = datetime.now()
			elif type(delivery_arg) == str and delivery_arg.lower()=='tomorrow':
				deliv_datestr = (datetime.now() + relativedelta(days=1)).strftime("%Y-%m-%d")
				deliv_date = datetime.now() + relativedelta(days=1)
			elif type(delivery_arg) == str:
				deliv_date = datetime.strptime(delivery_arg, "%Y-%m-%d")
				deliv_datestr = delivery_arg
		except:
			raise Exception("get_epex_dayaheadprices -- Argument delivery_date has to be datetime or valid datestring: yyyy-mm-dd, or TODAY | TOMORROW")
			
		trading_date = deliv_date - relativedelta(days=1)
		trade_datestr = trading_date.strftime("%Y-%m-%d")
		Logger.info("Downloading EPEX data for delivery date " + str(deliv_datestr) + " and trading date " + str(trade_datestr))
		# print ('make_csv', make_csv)
		# print ('deliv_datestr',deliv_datestr)
		# print ('trade_datestr',trade_datestr)
		# Waitkey()
		# Build the URL with these dates
		URL = "https://www.epexspot.com/en/market-data?data_mode=table&modality=Auction&sub_modality=DayAhead&market_area=NL&product=60&delivery_date=%s&trading_date=%s" % (deliv_datestr, trade_datestr)
	
		chrome_options = Options()
		#chrome_options.add_argument("--disable-extensions")
		#chrome_options.add_argument("--disable-gpu")
		#chrome_options.add_argument("--no-sandbox") # linux only
		chrome_options.add_argument("--headless")
		# chrome_options.headless = True # also works
		# driver = webdriver.Chrome(CHROMEDRIVER_LOCATION)
		driver = webdriver.Chrome(CHROMEDRIVER_LOCATION, options=chrome_options)
		# get the data from the webpage
		driver.get(URL)
		content = driver.page_source
		# and feed it to BeautifulSoup to reconstruct the hierarchy
		soup = BeautifulSoup(content, features="lxml")
		# first get the hours
		fc = soup.find('div', class_="fixed-column js-table-times")
		for header in fc.find_all('li', class_="child"):
			# print(header.text)
			day_ahead['Hours'].append(int(header.text.split("-")[0].strip()))
			
		# print(day_ahead['Hours'])
		# Waitkey()
		
		# now find the data we are looking for
		# op de website van epexspot staat de tabel in de DIV class 'js-table-values'
		a = soup.find('div', class_="js-table-values")
		# binnen deze DIV staan meerdere TR (tablerow??) entries die allen class='child' of class='child impair' hebben
		# print ("key_list = ", key_list)
		for b in a.find_all('tr', class_='child'):
			# Binnen iedere tablerow (TR) staan 4 datapunten (TD), buy volume, sell volume, volume en price. de text van deze TD entries moeten we hebben
			for teller,entry in enumerate(b.find_all('td'), start=1):
				# data wel even ontdoen van duizendtal separators, en als text opslaan
				day_ahead[key_list[teller]].append(entry.text.replace(",",""))
				
		day_ahead["Buy_Volume"] = [round(float(x)*1000,1) for x in day_ahead["Buy_Volume"]]
		day_ahead["Sell_Volume"] = [round(float(x)*1000,1) for x in day_ahead["Sell_Volume"]]
		day_ahead["Volume"] = [round(float(x)*1000,1) for x in day_ahead["Volume"]]
		day_ahead["Price"] = [round(float(x)/10.0, 2) for x in day_ahead["Price"]]
		print(day_ahead)
		Waitkey()
		
		if make_csv:
			outdir = CWD + DAYAHEAD_PRICES
			outname = deliv_datestr + '.csv'
			if not os.path.exists(outdir):
				os.mkdir(outdir)
			fullname = os.path.join(outdir, outname)    

			Logger.info ("Generating CSV file..." + fullname)
			df = pd.DataFrame(day_ahead)
			
			df.to_csv(fullname, index=False, encoding='utf-8')
		
		day_ahead['Date']=deliv_datestr
		result_data = day_ahead
		
		Logger.info("Succesfully downloaded EPEX data from epexspot....")
	except Exception as err:
		Logger.exception ("ERROR downloading data from epexspot..." + str(err))
	finally:
		if driver != None: driver.quit() 
		return result_data


def store_epex_dayaheadprices(*args, **kwargs):
	from DB_Routines import store_value_in_database
	try:
		# bijzondere situatie hier... we gaan hier nu de epex data ophalen voor zowel vandaag, als morgen
		dpID = kwargs.get('datapointID', None)
		if dpID == None: raise Exception ("No valid datapoint ID")
				 
		today_epex_data = kwargs.get('data', None)
		if today_epex_data == None: raise Exception ("No epex data")
		today = datetime.strptime(today_epex_data['Date'], "%Y-%m-%d")
		
		if len(today_epex_data["Hours"]) not in [23,24,25]:
			# 23 en 25 komen voor bij wintertijd en zomertijd overgangen
			raise Exception ("Did not find correct amount of entries in epex_data" + str(today))
		# print (today)
		# print (today_epex_data)
		# Waitkey()
			
		
		# bereken de correcte timestamps, in de dict staan de uren 0 - 23 onder 'Hours'
		Logger.info("Converting hours into Timestamps")
		# today_epex_data['Hours'] = [todaystamp + 3600*x for x in today_epex_data['Hours']]
		today_epex_data['Hours'] = [int(datetime.timestamp(today.replace(hour=x,minute=0,second=0,microsecond=0))) for x in today_epex_data['Hours']]
		
		# print ('timestamp in db :', today_epex_data['Hours'])
		# Waitkey()
		
		# We moeten een list van tuples maken met (timestamp, value) waarden
		Logger.info("Constructing Timestamp-Value pairs")
		dpID_timestamp_values = list(zip([dpID for x in today_epex_data['Hours']], today_epex_data['Hours'], today_epex_data['Price']))
		# print (dpID_timestamp_values)
		# Waitkey()
		
		Logger.info("Storing data in DB in datapointID " + str(dpID))
		store_value_in_database(dpID_timestamp_values = dpID_timestamp_values)
		Logger.info("Stored..... ")
		return True
	except Exception as err:
		Logger.exception(str(err))
	

def main(*args, **kwargs):
	# print (kwargs)
	# Waitkey()
	try:
		if len(kwargs) != 0:
			# er zijn argumenten met de commandline meegegeven, dus automatisch script
			delivery_date = kwargs.get('delivery_date', None)
			make_csv = (kwargs.get("make_csv", "False") == "True")
			dpID = kwargs.get('datapointID', None)
			result = get_epex_dayaheadprices(delivery_date=delivery_date, make_csv=make_csv)
			store_epex_dayaheadprices(datapointID=dpID, data=result)
	
		else:
			# er zijn geen argumenten met de commandline meegeven...dus interactief
			while True:
				try:
					datestr = input("Voor welke datum wilt u de epex dayahead prijzen downloaden? (jjjj-mm-dd):")
					date_selected = datetime.strptime(datestr, "%Y-%m-%d")
					print ("getting data .....")
					break
				except KeyboardInterrupt:
					break
				except:
					print ("Verkeerder formaat!!! Moet zijn jjjj-mm-dd, dus bijvoorbeeld 2022-12-23....")
					
				
			result = get_epex_dayaheadprices(delivery_date=date_selected, make_csv=True)
			# print(result)
			opslaan = input("Wilt u de gegevens opslaan in de database (epex_data datapoint, ID=214)? j/n:")
			if opslaan.lower() == "j":
				store_epex_dayaheadprices(datapointID=214, data=result)
	except Exception as err:
		Logger.exception (str(err))
	finally:
		logging.shutdown()



# def store_value_in_database(datapointID=None, timestamp_values=[]):
	# '''
	# timestamp_values is a list of tuples (timestamp, value)
	# Stores the value, with a timestamp in the Values table, under the DatapointID.
	# '''
	# if timestamp_values==[]: return
	# if datapointID is None: return
	
	# values_string = ""
	# # Values worden in de DB ALTIJD als TEXT opgeslagen. Bij het terughalen uit de DB moet dus een type conversie plaatsvinden
	# for entry in timestamp_values:
		# # timestamp_values is a list of tuples (timestamp, value)
		# values_string += "(%s,%s,'%s')," % (datapointID, entry[0], entry[1])
	# values_string = values_string.rstrip(",")
	# query = "INSERT INTO 'Values' (datapointID, timestamp, value) VALUES %s" % (values_string)
	
	# for teller in range(3):
		# try:
			# CONN=sqlite3.connect(CWD+DBFILE)
			# CONN.execute(query)
			# CONN.commit()
			# # Logger.debug('Query executed: %s' % query)
			# break
		# except Exception as err:
			# Logger.warning("Store failed....reconnecting, attempt " + str(teller+1) + " -- " + str(err))
			# Logger.warning("Query: " + query)
			# try:
				# CONN.close()
			# except:
				# pass
			# if (teller + 1) == DB_RETRIES:
				# raise Exception ("Store failed, max retries exceeded...")
			# else:
				# time.sleep(0.5)



if __name__ == '__main__':
	# python Epex_dayaheadprices.py foo bar hello=world 'with spaces'='a value'
	# sys.argv[0] is de naam van het script (in dit geval dus Epex_dayaheadprices.py)
	# sys.argv[1] .. sys.argv[n] zijn de argumenten daarna, gescheiden door spatie
	# met een truck (zie onder) kunnen we kwargs eruit destileren en met args en kwargs verdergaan
	sys.exit(main(sys.argv[0], **dict(arg.split('=') for arg in sys.argv[1:]))) # kwargs
