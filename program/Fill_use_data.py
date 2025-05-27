#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Fill_use_data.py
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
	 __main__.logfilename = "FILL_USE_DATA.log"
	 __main__.backupcount = 3


# print (sys.path)
import os
from LogRoutines import Logger
from Config import DAYAHEAD_PRICES, CHROMEDRIVER_LOCATION, ENVIRONMENT, LOGFILELOCATION, Loglevel
from Common_Routines import cursor_to_dict
# from Common_Enums import *
import sqlite3

import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler

from Common_Enums import *
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

CWD=(os.path.dirname(os.path.realpath(__file__)))
DBFILE = "/Database/JSEM.db"


tot_use1_ID=4
tot_use2_ID=5
tot_ret1_ID=6
tot_ret2_ID=7
gasID=43

e_verbruik_dag=249
e_terug_dag=251
gas_verbruik_dag=253
e_verbruik_mnd=255

def main(args):
	'''
	Deze routine vult de database waarden van de datapoints
	"e_verbruik_dag"
	"e_verbruik_dagbegin"
	"e_terug_dag"
	"e_terug_dagbegin"
	"gas_verbruik_dag"
	"gas_verbruik_dagbegin"
	"e_verbruik_mnd"
	"e_verbruik_mndbegin"
	Door in de bestaande Values van de datapoints
	tot_use1
	tot_use2
	tot_ret1
	tot_ret2
	op te halen aan het einde van iedere dag en daarmee de database te vullen.
	'''
	start_str = input('Geef de EERSTE datum die meegenomen moet worden (dd-mm-YYYY): ')
	eind_str = input('geef de LAATSTE datum die meegenomen moet worden (dd-mm-YYYY): ')
	
	# We bepalen de eerste seconde van de VOLGENDE dag
	start_ts = int(datetime.strptime(start_str, "%d-%m-%Y").replace(hour=0,minute=0,second=0).timestamp())
	eind_ts = int(datetime.strptime(eind_str, "%d-%m-%Y").replace(hour=0,minute=0,second=0).timestamp())
	
	this_ts = start_ts
	# last_ts is een dag eerder
	last_ts = this_ts - (24*60*60)
	CONN=sqlite3.connect(CWD+DBFILE)
	# timestamp_values is a list of tuples (datapointID, timestamp, value)
	timestamp_values=[]
	last_tot_use=None
	last_tot_ret=None
	last_gas=None
	while this_ts <= eind_ts:
		# structure of result is: {'ID': 2264426, 'datapointID': 90, 'timestamp': 1670108398, 'value': '38.94'}
		# ----------------------- total use ---------------------------------
		query = "SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp >= %s AND timestamp < %s ORDER BY timestamp DESC LIMIT 1" % (tot_use1_ID, last_ts, this_ts)
		# print (query)
		data=CONN.execute(query)
		result = cursor_to_dict(data, output=Dictionary.of_values)
		tot_use1 = float(result['value'])

		query = "SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp >= %s AND timestamp < %s ORDER BY timestamp DESC LIMIT 1" % (tot_use2_ID, last_ts, this_ts)
		# print (query)
		data=CONN.execute(query)
		result = cursor_to_dict(data, output=Dictionary.of_values)
		tot_use2 = float(result['value'])
		
		timestamp_values.append((e_verbruik_dagbegin, this_ts, round((tot_use1+tot_use2),3)))
		if last_tot_use is not None: timestamp_values.append((e_verbruik_dag, last_ts, round((tot_use1 + tot_use2 - last_tot_use),3)))
		last_tot_use = tot_use1 + tot_use2
		
		# ------------------------ total return --------------------------------
		query = "SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp >= %s AND timestamp < %s ORDER BY timestamp DESC LIMIT 1" % (tot_ret1_ID, last_ts, this_ts)
		# print (query)
		data=CONN.execute(query)
		result = cursor_to_dict(data, output=Dictionary.of_values)
		tot_ret1 = float(result['value'])

		query = "SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp >= %s AND timestamp < %s ORDER BY timestamp DESC LIMIT 1" % (tot_ret2_ID, last_ts, this_ts)
		# print (query)
		data=CONN.execute(query)
		result = cursor_to_dict(data, output=Dictionary.of_values)
		tot_ret2 = float(result['value'])
		
		timestamp_values.append((e_terug_dagbegin, this_ts, round((tot_ret1 + tot_ret2),3)))
		if last_tot_ret is not None: timestamp_values.append((e_terug_dag, last_ts, round((tot_ret1 + tot_ret2 - last_tot_ret),3)))
		last_tot_ret = tot_ret1 + tot_ret2
		
		# ---------------------------- gas --------------------------------------
		query = "SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp >= %s AND timestamp < %s ORDER BY timestamp DESC LIMIT 1" % (gasID, last_ts, this_ts)
		# print (query)
		data=CONN.execute(query)
		result = cursor_to_dict(data, output=Dictionary.of_values)
		tot_gas = float(result['value'])

		timestamp_values.append((gas_verbruik_dagbegin, this_ts, round(tot_gas,5)))
		if last_gas is not None: timestamp_values.append((gas_verbruik_dag, last_ts, round((tot_gas - last_gas),5)))
		last_gas = tot_gas

		# print(timestamp_values)
		
		# en we schakelen door naar de volgende dag, precies 24 uren van 60 minuten van 60 seconden verder...
		last_ts=this_ts
		this_ts=this_ts+(24*60*60)
		
		
	values_string = ""
	# Values worden in de DB ALTIJD als TEXT opgeslagen. Bij het terughalen uit de DB moet dus een type conversie plaatsvinden
	for entry in timestamp_values:
		# timestamp_values is a list of tuples (datapointID, timestamp, value)
		values_string += "(%s,%s,'%s')," % (entry[0], entry[1], entry[2])
	values_string = values_string.rstrip(",")
	query = "INSERT INTO 'Values' (datapointID, timestamp, value) VALUES %s" % (values_string)
	
	print (query)
	input("any key")
		
	CONN.execute(query)
	CONN.commit()
	CONN.close()
	
	
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
