#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  copy weather_epex data.py
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
	 __main__.logfilename = "Copy weather_epex data.log"
	 __main__.backupcount = 2
import os
import sys

import os
import logging
from LogRoutines import Logger
from Config import LOGFILELOCATION, Loglevel
from Config import DB_CSV_FILES
from Config import DBFILE
from Common_Data import CWD
# from Common_Enums import *
import sqlite3
# import urllib3
# from bs4 import BeautifulSoup
# import json
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

epex_data = 214		# epex_data
frcst_temp = 273	# frcst_temp
frcst_wind = 274
frcst_richting = 275
frcst_neerslag = 276
frcst_luchtdruk = 277
frcst_bewolking = 278
frcst_zoninstraling = 279

dpIDs= [frcst_temp, frcst_wind, frcst_richting, frcst_neerslag, frcst_luchtdruk, frcst_bewolking, frcst_zoninstraling, epex_data]

def main(args):
	from DB_Routines import get_df_from_database
	from_date = (datetime.now() - relativedelta(months=1)).replace(hour=0, minute=0, second=0)
	from_str = input('select date from: (YYYY-MM-DD) default = %s:  ' % datetime.strftime(from_date, "%Y-%m-%d"))
	if from_str: from_date = datetime.strptime(from_str, "%Y-%m-%d")
	
	to_date = datetime.now().replace(hour=23, minute=59, second=59) + relativedelta(days=14)
	to_str = input('select date to: (YYYY-MM-DD) default = %s:  ' % datetime.strftime(to_date, "%Y-%m-%d"))
	if to_str: to_date = datetime.strptime(to_str, "%Y-%m-%d")
	
	print (from_date, to_date)
	
	result_df = get_df_from_database(dpIDs=dpIDs, selected_enddate=to_date, selected_startdate=from_date, IDs_as_columnheaders=True)
	
	print (result_df)
	
	save_stats = (input('Opslaan in een CSV file?').lower()=='j')
	if save_stats:
		outdir = CWD + DB_CSV_FILES
		outname = 'weather_epex_data from %s to %s.csv' % (from_str, to_str)
		if not os.path.exists(outdir):
			os.mkdir(outdir)
		fullname = os.path.join(outdir, outname)    
		Logger.info ("Generating CSV file..." + fullname)
		result_df.to_csv(fullname, index=False, encoding='utf-8')

	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
