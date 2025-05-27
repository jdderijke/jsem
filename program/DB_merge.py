import os
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
		into_fullpath = Path(input('Specify the full path to the database file you want to merge INTO: ')).with_suffix('.db')
		if not into_fullpath.is_file():
			print('Illegal or non existing INTO file(name)..')
		else:
			from_fullpath = Path(input('Specify the full path to the database file you want to merge FROM: ')).with_suffix('.db')
			if not from_fullpath.is_file():
				print('Illegal or non existing FROM file(name)..')
			else:
				break
			break
	
	Logger.info(f'Using INTO database: {into_fullpath}')
	Logger.info(f'Using FROM database: {from_fullpath}')
	
	asyncwait_start()
	into_firstTS, into_lastTS = get_min_max_timestamps(pathto_local_DBfile=into_fullpath)
	from_firstTS, from_lastTS = get_min_max_timestamps(pathto_local_DBfile=from_fullpath)
	asyncwait_stop()
	
	into_firstDT = datetime.fromtimestamp(into_firstTS)
	into_lastDT = datetime.fromtimestamp(into_lastTS)
	from_firstDT = datetime.fromtimestamp(from_firstTS)
	from_lastDT = datetime.fromtimestamp(from_lastTS)
	
	Logger.info(f'INTO database, values table: firstrow found: {into_firstDT}, lastrow found: {into_lastDT}')
	Logger.info(f'FROM database, values table: firstrow found: {from_firstDT}, lastrow found: {from_lastDT}')
	
	if into_firstTS <= from_firstTS <= from_lastTS <= into_lastTS:
		if input('The FROM database timestamps are fully within the INTO database timestamps....continue (J/n): ').upper() == 'N':
			return 0
	
	if input('Do you want to BACKUP the INTO database BEFORE merging the FROM database into it? (J/n): ').upper() == 'J':
		backup_fullpath = Path(into_fullpath.parent, into_fullpath.name, "_backup").with_suffix(".db")
		Logger.info(f'This can take some time.....saving backup in {backup_fullpath}')
		asyncwait_start()
		shutil.copy2(into_fullpath, backup_fullpath)
		asyncwait_stop()
		Logger.info('Backup completed...')
	
	attach_query = 	f"attach database '{from_fullpath}' as dbfrom"
	detach_query = 	f"detach database dbfrom"
	merge_query = 	f"insert or replace into 'Values' (datapointID, timestamp, value) select datapointID, timestamp, value " \
					f"from dbfrom.'Values'"

	print(merge_query)
	input('any key')
	
	vacuum_query = f"VACUUM"

	CONN = None
	try:
		Logger.info(f"Opening INTO database {into_fullpath.name}")
		CONN = sqlite3.connect(into_fullpath)
		Logger.info(f'Attaching FROM database {from_fullpath.name}')
		CONN.execute(attach_query)

		Logger.info(f'merging.....')
		asyncwait_start()
		CONN.execute(merge_query)
		CONN.commit()
		asyncwait_stop()

		Logger.info(f'Detaching FROM database {from_fullpath.name}')
		CONN.execute(detach_query)

		if input("Do you want to VACUUM the INTO database? (J/n): ").upper() == 'J':
			Logger.info('Vacuuming the INTO database to optimise.........')
			asyncwait_start()
			CONN.execute(vacuum_query)
			asyncwait_stop()
		
		return 0
	
	except Exception as err:
		print(str(err))
		return 1
	finally:
		if CONN:
			CONN.commit()
			CONN.close()

if __name__ == '__main__':
	import sys
	
	sys.exit(main(sys.argv))
