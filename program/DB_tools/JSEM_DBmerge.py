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


def get_min_max_timestamps(CONN=None, dpIDs=[], full_db_path=None, **kwargs):
	"""
	Returns the lowest (min) and the highest (max) values for the timestamps in the Values table
	
	:param CONN: A valid DB connection. If not provided a valid full_db_path (Path) has to be provided
	:param dpIDs: Limit the results to timestamps of these datapoint ID's only
	:param full_db_path: If no valid DB connection is provided, give the Path to a valid DB here.
	:param kwargs:
	:return:
	"""
	close_the_door = False
	try:
		if not CONN:
			if full_db_path and full_db_path.is_file():
				Logger.info(f"Opening database {full_db_path.name}")
				CONN = sqlite3.connect(full_db_path)
				close_the_door = True
			else:
				raise FileNotFoundError('No valid path to DB file')
		if dpIDs:
			query = "SELECT datapointID AS ID, min(timestamp) AS min, max(timestamp) AS max FROM 'Values' WHERE datapointID IN (%s)" % \
					(",".join([str(x) for x in dpIDs]))
		else:
			query = "SELECT min(timestamp) AS min, max(timestamp) AS max FROM 'Values'"

		result_df = pd.read_sql_query(query, CONN)
		# print(result_df)
		min_dbts = result_df.iloc[0]['min']
		max_dbts = result_df.iloc[0]['max']
		return min_dbts, max_dbts
	except Exception as err:
		Logger.error(str(err))
	finally:
		if close_the_door:
			CONN.commit()
			CONN.close()
	
		
def get_table_names(CONN=None, full_db_path=None, **kwargs):
	close_the_door = False
	result_df = None
	try:
		if not CONN:
			if full_db_path and full_db_path.is_file():
				Logger.info(f"Opening database {full_db_path.name}")
				CONN = sqlite3.connect(full_db_path)
				close_the_door = True
			else:
				raise FileNotFoundError('No valid path to DB file')

		query = "SELECT name FROM sqlite_master WHERE type='table'"
		result_df = pd.read_sql_query(query, CONN)
		return result_df
	except Exception as err:
		Logger.error(str(err))
	finally:
		if close_the_door:
			CONN.commit()
			CONN.close()


def get_column_names(CONN=None, full_db_path=None, table_name=None, **kwargs):
	close_the_door = False
	try:
		if not CONN:
			if full_db_path and full_db_path.is_file():
				Logger.info(f"Opening database {full_db_path.name}")
				CONN = sqlite3.connect(full_db_path)
				close_the_door = True
			else:
				raise FileNotFoundError('No valid path to DB file')

		query = f"pragma table_info('{table_name}')"
		result_df = pd.read_sql_query(query, CONN)
		return result_df
	except Exception as err:
		Logger.error(str(err))
	finally:
		if close_the_door:
			CONN.commit()
			CONN.close()


def main(args):
	'''
	This program merges data from the Values table (JSEM) of a FROM database into the Values table of a INTO database
	
	:param args:
	:return:
	'''
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
	
	into_tables_df = get_table_names(full_db_path=into_fullpath)
	from_tables_df = get_table_names(full_db_path=from_fullpath)
	
	if not into_tables_df.compare(from_tables_df).empty:
		raise Exception('Into and From databases have different table definitions! Can not merge..')
		
	if input('BACKUP the target database BEFORE merging new data into it? (only when database not in use!!)(J/n): ').upper() != 'N':
		backup_fullpath = Path(into_fullpath.parent, "backup").with_suffix(".db")
		print(backup_fullpath)
		input('any key')
		Logger.info(f'This can take some time.....saving backup in {backup_fullpath}')
		asyncwait_start()
		shutil.copy2(into_fullpath, backup_fullpath)
		asyncwait_stop()
		Logger.info('Backup completed...')
	
	while True:
		print(into_tables_df)
		inp = input("List the (comma separated) index numbers of the tables you want to merge.... i.e. '2,4,5' or just '2'")
		inp = inp.strip()
		inp = inp.replace('.',',')
		t_list = [into_tables_df.loc[int(tbl)]['name'] for tbl in inp.split(',')]
		print('Only the Values table will truly be merged, all other tables will be replaced (not merged)')
		if input(f'You chose the following tables: {",".join(t_list)}... Correct? (N/j)').upper() == 'J': break

	CONN = None
	try:
		Logger.info(f"Opening INTO database {into_fullpath.name}")
		CONN = sqlite3.connect(into_fullpath)
		Logger.info(f'Attaching FROM database {from_fullpath.name}')
		CONN.execute(f"attach database '{from_fullpath}' as dbfrom")
		
		for table in t_list:
			count_before = pd.read_sql_query(f"select count(*) from '{table}'", CONN).loc[0]['count(*)']
			if table == 'Values':
				# For the VALUES table, make a list of all column names that are NOT in the primary key
				col_list = get_column_names(CONN, table_name=table)
				col_list = col_list[col_list['pk'] == 0]['name'].tolist()
				# check if the timestamps overlap
				asyncwait_start()
				into_firstTS, into_lastTS = get_min_max_timestamps(CONN)
				from_firstTS, from_lastTS = get_min_max_timestamps(full_db_path=from_fullpath)
				asyncwait_stop()
				Logger.info(f'INTO database, values table: firstrow found: {datetime.fromtimestamp(into_firstTS)}, lastrow found: {datetime.fromtimestamp(into_lastTS)}')
				Logger.info(f'FROM database, values table: firstrow found: {datetime.fromtimestamp(from_firstTS)}, lastrow found: {datetime.fromtimestamp(from_lastTS)}')
				
				if into_firstTS <= from_firstTS <= from_lastTS <= into_lastTS:
					if input('The FROM database Values timestamps are fully within the INTO database Values timestamps....continue? (J/n): ').upper() == 'N':
						continue
						
				merge_query = f"insert or replace into 'Values' ({', '.join(col_list)}) select {', '.join(col_list)} " \
							  f"from dbfrom.'Values'"
			
				Logger.info(f'MERGING.....')
				asyncwait_start()
				CONN.execute(merge_query)
				CONN.commit()
				asyncwait_stop()
				
				count_after = pd.read_sql_query(f"select count(*) from '{table}'", CONN).loc[0]['count(*)']
				Logger.info(f'Table {table}: Rowcount before merge: {count_before}, after merge: {count_after}... added {count_after - count_before} rows to {table} table..')
			
			else:
				Logger.info(f'REPLACING.....')
				asyncwait_start()
				CONN.execute(f"delete from '{table}'")
				CONN.execute(f"insert into '{table}' select * from dbfrom.'{table}'")
				CONN.commit()
				asyncwait_stop()
				
				count_after = pd.read_sql_query(f"select count(*) from '{table}'", CONN).loc[0]['count(*)']
				Logger.info(f'Table {table}: Rowcount before replace: {count_before}, after replace: {count_after}...')

			

		Logger.info(f'Detaching FROM database {from_fullpath.name}')
		CONN.execute(f"detach database dbfrom")
		
		if input("Do you want to VACUUM the INTO database? (J/n): ").upper() == 'J':
			Logger.info('Vacuuming the INTO database to optimise.........')
			asyncwait_start()
			CONN.execute(f"VACUUM")
			asyncwait_stop()
		
		return 0
	
	except Exception as err:
		Logger.error(str(err))
		return 1
	finally:
		if CONN:
			CONN.commit()
			CONN.close()

if __name__ == '__main__':
	import sys
	
	sys.exit(main(sys.argv))
