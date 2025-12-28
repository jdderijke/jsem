#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  datapoint_IDs.py
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
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import math	
import os

import threading
import sqlite3
import pandas as pd
import numpy as np

import Common_Data
# from Common_Data import CWD, DATAPOINTS_ID, DATAPOINTS_NAME, CATEGORY_ID, CATEGORY_NAME, INTERFACE_ID, INTERFACE_NAME
# from LogRoutines import Logger
# from Common_Enums import *
# from DataPoint import Datapoint, Category, Pollmessage, Protocol
# # from interfaces import BaseInterface
# from Common_Routines import get_type, dump, IsNot_NOE, Is_NOE, Waitkey, Calculate_Timerset, Calculate_Period
# from Common_Routines import cursor_to_dict, update_progressbar, get_begin_of_week

from Config import DBFILE
# from Config import TCPPORT, DBFILE, DB_RETRIES, DB_WAITBETWEENRETRIES, Max_Chart_Points, DB_alivetime, DB_looptime
# from TCP_Routines import tcp_sql_query

# from enum import Enum

CWD=(os.path.dirname(os.path.realpath(__file__)))



def main(args):
	CONN=sqlite3.connect(DBFILE, uri=True)
	query = "SELECT * FROM Datapoints WHERE enabled IS NOT NULL"
	dp_df = pd.read_sql_query(query, CONN)
	# print (dp_df)
	# input ('any key')
	with open('Datapoint_IDs.py', 'w') as f:
		for ID, row in dp_df.iterrows():
			if not row['ID'] or not row['name']:
				print ('Error!!!')
				print (row['ID'], row['name'])
				input ('any key')
				
			f.write(row['name'] + ' = ' + str(row['ID']) + '\n')
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
