#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  DatapointRestorer.py
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
	 __main__.logfilename = "DatapointRestorer.log"
	 __main__.backupcount = 2
import os
import sys

# print (sys.path)
import os
import logging
from LogRoutines import Logger
from Config import LOGFILELOCATION, Loglevel
from Config import DBFILE
from Common_Data import CWD
from JSEM_Commons import IsNot_NOE

# from Common_Enums import *
import sqlite3
# import urllib3
# from bs4 import BeautifulSoup
# import json
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

def restore_datapoints(scan_only=False):
	from DB_Routines import store_value_in_database, get_value_from_database
	CONN=sqlite3.connect(CWD+DBFILE)
	# First get all enabled datapointsd from the database
	enabled_dps = pd.read_sql_query("select * from 'Datapoints' where enabled=1 and dbstore=1", CONN)
	enabled_dps = enabled_dps.set_index('ID')
	CONN.close()
	
	for dpID, row in enabled_dps.iterrows():
		# Try to get the LAST value of the datapoint from the Values table
		last_value = get_value_from_database(dpID=dpID)
		if last_value is None:
			Logger.info("DatapointID %s, %s did not have an entry in the Values table..." % (dpID, row['name']))
			if IsNot_NOE(row["last_value"]):
				Logger.info("There is a last_value stored in the Datapoints table: %s" % row["last_value"])
				if scan_only:
					if input("Write this last_value (%s) to the Values tabke for datapoint %s, %s (J/n)" % 
							(row["last_value"], dpID, row['name'])).lower()=="n": continue
				timestamp = int(datetime.timestamp(datetime.now()))
				store_value_in_database(dpID_timestamp_values=[(int(dpID), timestamp, str(row["last_value"]))])
				Logger.info("Datapoint %s, %s last_value added to Values table" % (dpID, row['name']))


def main(args):
	if input("Alle ENABLED(=1) datapoints die een DBSTORE(=1) setting hebben in de database controleren op een entry in de VALUES table?(J/n): ").lower()=="n": return
	if input("Wilt u alleen scannen, en zelf bij ieder probleem bepalen of het opgelost wordt? (J/n): ").lower()=="n": 
		scanonly=True
	else:
		scanonly=False
	
	restore_datapoints(scan_only=scanonly)
	
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
