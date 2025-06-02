
import __main__
import logging
import sys


Logger = None
if hasattr(__main__, 'Logger') and __main__.Logger is not None:
	# use the passed logger from the __main__ object
	Logger = __main__.Logger
else:
	# create my own simple logger
	logging.basicConfig(stream=sys.stdout, level=logging.INFO,
						format='%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s')
	Logger = logging.getLogger(__name__)
	__main__.Logger = Logger
	Logger.info(f'Logger {__name__} started')

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import threading

import sqlite3
import shutil
from pathlib import Path
import pandas as pd


'''
The schema of the Values table is as follows-----
CREATE TABLE `Values` (
	`ID`	INTEGER PRIMARY KEY AUTOINCREMENT,
	`datapointID`	INTEGER NOT NULL,
	`timestamp`	INTEGER NOT NULL,
	`value`	TEXT DEFAULT NULL,
	UNIQUE(datapointID,timestamp) ON CONFLICT REPLACE
	FOREIGN KEY(`datapointID`) REFERENCES `Datapoints`(`ID`) ON UPDATE CASCADE ON DELETE NO ACTION
);

This program asks for the database to perform a purge/cleanse operation on. Defaults to the database specified in the Config.py file
It checks for the FIRST and LAST records in this database. Based on this info the user can select a CUTOFF point.
It gives the option of creating a backup of the FULL database, so as to not loose any information

After this.....For all datapoints the program will lookup the last datavalue BEFORE or ON this CUTOFF and note this value down in the 
database ON this CUTOFF timepoint. After this has been completed succesfully... all data BEFORE the CUTOFF will be deleted.
And finally a VACUUM operation on the database can be performed to optimize the database to the smaller size.
'''
async_spin = None
stop_spinning = True


def spinning_cursor():
	while True:
		for cursor in '|/-\\':
			yield cursor


def spincursor(duration=1.0):
	'''
	Spins the cursor for duration seconds
	'''
	spinner = spinning_cursor()
	for _ in range(int(10 * duration)):
		sys.stdout.write(next(spinner))
		sys.stdout.flush()
		time.sleep(0.1)
		sys.stdout.write('\b')


def spinning():
	while not stop_spinning:
		spincursor(0.5)


def asyncwait_start():
	global async_spin, stop_spinning
	async_spin = threading.Thread(target=spinning)
	# have the receiver run as daemon thread....
	async_spin.daemon = True
	stop_spinning = False
	async_spin.start()


def asyncwait_stop():
	global stop_spinning
	stop_spinning = True
	async_spin.join()


def get_min_max_timestamps(dpIDs=[], pathto_local_DBfile=None):
	# returns the lowest min and the highest max values for the timestamps of the dpIDs
	CONN = None
	
	try:
		if dpIDs:
			query = "SELECT datapointID AS ID, min(timestamp) AS min, max(timestamp) AS max FROM 'Values' WHERE datapointID IN (%s)" % \
					(",".join([str(x) for x in dpIDs]))
		else:
			query = "SELECT min(timestamp) AS min, max(timestamp) AS max FROM 'Values'"
		# print(query)
		# input('Any key..')
		CONN = sqlite3.connect(pathto_local_DBfile, uri=True)
		result_df = pd.read_sql_query(query, CONN)
		# print(result_df)
		min_dbts = result_df.iloc[0]['min']
		max_dbts = result_df.iloc[0]['max']
		return min_dbts, max_dbts
	except Exception as err:
		Logger.error(str(err))
	finally:
		if CONN: CONN.close()


def main(args):
	while True:
		fullpath = Path(input('Specify the full path to the database you want to PURGE: ')).with_suffix('.db')
		if not fullpath.is_file():
			print('Illegal or non existing file(name)..')
		else:
			break
	
	Logger.info(f'Using database: {fullpath}')
	
	asyncwait_start()
	firstTS, lastTS = get_min_max_timestamps(pathto_local_DBfile=fullpath)
	asyncwait_stop()
	
	firstDT = datetime.fromtimestamp(firstTS)
	lastDT = datetime.fromtimestamp(lastTS)
	
	Logger.info(f'{fullpath.name} database, values table: firstrow found: {firstDT}, lastrow found: {lastDT}')
	
	# We default keep the last 3 months of data
	cutoff_dt = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=3)
	while True:
		try:
			dt_str = input(f"From what date do you want to keep entries in the {fullpath.name}.Values "
						   f"table ({cutoff_dt.strftime('%Y-%m-%d')})? ")
			if dt_str: cutoff_dt = datetime.strptime(dt_str, '%Y-%m-%d')
			break
		except:
			print('Illegal datetime format, must be YYYY-mm-dd')
			
	Logger.info(f"Using a cutoff point of {cutoff_dt}, purging all entries BEFORE this point...")
	
	if input('Do you want to backup the database BEFORE purging? (J/n): ').upper() == 'J':
		backup_fullpath = Path(fullpath.parent, fullpath.name, "_backup").with_suffix(".db")
		Logger.info(f'This can take some time.....saving backup in {backup_fullpath}')
		asyncwait_start()
		shutil.copy2(fullpath, backup_fullpath)
		asyncwait_stop()
		Logger.info('Backup completed...')
		
	cutoff_ts = int(cutoff_dt.timestamp())
	
	anchor_query = f"insert into 'Values' (timestamp, datapointID, value) select {cutoff_ts} as timestamp, datapointID, value from(select max(timestamp), datapointID, value from 'Values' where datapointID in (select ID from Datapoints) and timestamp <= {cutoff_ts} group by datapointID)"
	purge_query = f"delete from 'Values' where timestamp < {cutoff_ts}"
	vacuum_query = 'VACUUM'
	
	CONN = None
	try:
		
		Logger.info(f"Opening the database {fullpath.name}")
		CONN=sqlite3.connect(fullpath)
		
		Logger.info(f'Creating anchorpoints on timestamp {cutoff_ts} ({cutoff_dt}) for all datapoints with data BEFORE this timestamp...')
		asyncwait_start()
		CONN.execute(anchor_query)
		CONN.commit()
		asyncwait_stop()
		
		Logger.info(f'Purging all datarows before timestamp {cutoff_ts} ({cutoff_dt}).....')
		asyncwait_start()
		CONN.execute(purge_query)
		CONN.commit()
		asyncwait_stop()
		
		if input("Do you want to VACUUM the database? (J/n): ").upper()!='N':
			Logger.info('Vacuuming the database to optimise.........')
			asyncwait_start()
			CONN.execute(vacuum_query)
			asyncwait_stop()
			
		return 0
					
	except Exception as err:
		print (str(err))
		return 1
	finally:
		if CONN:
			CONN.commit()
			CONN.close()


if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
