import numpy

from LogRoutines import Logger
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import math	

import threading
import sqlite3
import pandas as pd
import numpy as np

import Common_Data
from Common_Data import DATAPOINTS_ID, DATAPOINTS_NAME, CATEGORY_ID, CATEGORY_NAME, INTERFACE_ID, INTERFACE_NAME
from Common_Enums import *
from DataPoint import Datapoint, Category, Pollmessage, Protocol
# from interfaces import BaseInterface
from JSEM_Commons import get_type, dump, IsNot_NOE, Is_NOE, Waitkey, Calculate_Timerset, Calculate_Period
from JSEM_Commons import cursor_to_dict, update_progressbar, get_begin_of_week

from Config import HOST, PORT, DBFILE, DB_RETRIES, DB_WAITBETWEENRETRIES, Max_Chart_Points, DB_alivetime, DB_looptime
# from TCP_Routines import tcp_sql_query

from enum import Enum

from Config import USE_REMOTE_JSEM_DB
from TCP_Routines import tcp_sql_query


# Connections = {}




class DBstore_engine(object):
	def __init__(self, *args, **kwargs):
		self.name = kwargs.get("name", "Unnamed....")
		self.dbfile = kwargs.get("dbfile", None)
		self.looptime = kwargs.get("looptime", DB_looptime)
		self.alivetime = kwargs.get("alivetime", DB_alivetime)
		self.status_widget = None
		self.CONN = None
		self.DBstore_Q = []
		self.keeprunning=False
		self.stoppedrunning=True
		self.thrd = threading.Thread(target=self.start)
		self.thrd.daemon = True
		self.thrd.start()
		Logger.info (f'{self.name}--DBstore_engine started with interval: {self.looptime} s.')
		
	def connect(self):
		try:
			self.CONN=sqlite3.connect(self.dbfile)
		except Exception as err:
			Logger.error(f'{self.name}--Can not establish connection to database {self.dbfile}')
			return False
		return True
		
	def start(self):
		if not self.connect(): return
		self.keeprunning=True
		self.stoppedrunning=False
		start_time = time.time()
		max_Q=0
		while self.keeprunning:
			try:
				# print('dbstore_engine runs...')
				if self.status_widget is not None:
					self.status_widget.set_value(len(self.DBstore_Q))
				if time.time() - start_time > self.alivetime:
					start_time = time.time()
					Logger.info(f'{self.name}--I am still alive and kicking.. Max DBstore_Q size = {max_Q}')
					max_Q=0
				while self.DBstore_Q:
					max_Q = max(len(self.DBstore_Q), max_Q)
					query = self.DBstore_Q[0]
					# remove any null characters from the query...sqlite3 doesnt like them
					query = query.replace('\x00', '')
					for teller in range(DB_RETRIES):
						try:
							self.CONN.execute(query)
							# Logger.debug('Query executed: %s' % query)
							self.DBstore_Q.pop(0)
							break
						except Exception as err:
							Logger.warning(f'{self.name}--Store failed, attempt:{teller+1} -- {err}')
							Logger.warning(f"Query: {query}")
							if (teller + 1) == DB_RETRIES:
								Logger.error(f'{self.name}--Store failed, max retries exceeded, re_adding query to queue ({len(self.DBstore_Q)})...')
								# delete the query from the queue and add it again at the top....
								self.add_query(self.DBstore_Q.pop(0))
								break
							time.sleep(DB_WAITBETWEENRETRIES)
				self.CONN.commit()
				time.sleep(self.looptime)
			except Exception as err:
				Logger.error('%s--%s' % (self.name, err))
				if Conn_IsOpen(self.CONN):
					self.CONN.commit()
					self.CONN.close()
				while self.keeprunning:
					time.sleep(1.0)
					Logger.error(f'{self.name}--restoring connection to {self.dbfile}...')
					if self.connect(): break
				
		self.stoppedrunning=True
		self.keeprunning=False
		
	def stop(self):
		while len(self.DBstore_Q) != 0:
			Logger.info(f'{self.name}--Stop requested but still {len(self.DBstore_Q)} SQL requests in queue ')
			time.sleep(1.0)
			
		self.keeprunning=False
		self.thrd.join()
		Logger.info (f"{self.name}--DBstore_engine stopped.")
		self.thrd = None
		
	def add_query(self, query=""):
		if Is_NOE(query): return
		self.DBstore_Q.append(query)
		# print(len(self.DBstore_Q))
		
	def clear_Q(self):
		self.DBstore_Q=[]
	
	def __str__(self):
		result=""
		for query in self.DBstore_Q: result += query + "\n"
		return result.rstrip('\n')
		
	
def Conn_IsOpen(conn):
     try:
        conn.cursor()
        return True
     except Exception as ex:
        return False
	
	
def get_field_from_database(table, ID=None, field=None):
	'''
	Retrieves the value of a single field (column) of a table
	'''
	CONN=sqlite3.connect(DBFILE, uri=True)
	try:
		id_str = ''
		field_str = '*'
		if ID: id_str = ' WHERE ID in (%s)' % ID
		if field: field_str = '(%s)' % field
		query = "SELECT %s FROM '%s'%s" % (field_str, table, id_str)
		# print (query)
		# Waitkey()
		data = CONN.execute(query)
		result = cursor_to_dict(data, output=Dictionary.of_values)
		# print (result[field])
		# Waitkey()
		return result[field]
		
	except Exception as err:
		Logger.error (str(err))
	finally:
		CONN.close()
	
def store_field_in_database(table, ID, field, value):
	'''
	Stores the value, of a single field (column) of a table.
	'''
	if value is None:
		storevalue = 'NULL'
	elif type(value)==str:
		storevalue = "'%s'" % value
	elif math.isnan(value):
		storevalue = 'NULL'
	else:
		storevalue = str(value)
	query = "UPDATE '%s' SET '%s'=%s WHERE ID=%s" % (table, field, storevalue, ID)
	Common_Data.DB_STORE.add_query(query)
	
	
def store_value_in_database(dpID_timestamp_values=[]):
	'''
	dpID_timestamp_values is a list of tuples (datapointID, timestamp, value)
	Stores the value, with a timestamp in the Values table, under the DatapointID.
	'''
	if dpID_timestamp_values==[]: return
	try:
		# check if the DBstore_engine exists and is running.....
		store_direct = (Common_Data.DB_STORE is None) or (Common_Data.DB_STORE.thrd is None) or (Common_Data.DB_STORE.keeprunning is False)
		
		values_string = ""
		# Values worden in de DB ALTIJD als TEXT opgeslagen. Bij het terughalen uit de DB moet dus een type conversie plaatsvinden
		for entry in dpID_timestamp_values:
			# timestamp_values is a list of tuples (dpID,timestamp, value)
			dpID, timestamp, value = entry[0], entry[1], entry[2]
			if value is None: storevalue = 'NULL'
			elif type(value)==str: storevalue = "'%s'" % value
			elif math.isnan(value): storevalue = 'NULL'
			else: storevalue = str(value)
			values_string += "(%s,%s,%s)," % (dpID, timestamp, storevalue)
		values_string = values_string.rstrip(",")
		query = "INSERT INTO 'Values' (datapointID, timestamp, value) VALUES %s" % (values_string)
		
		if not store_direct:
			Common_Data.DB_STORE.add_query(query)
		else:
			for teller in range(DB_RETRIES):
				try:
					CONN=sqlite3.connect(DBFILE)
					CONN.execute(query)
					CONN.commit()
					# Logger.debug('Query executed: %s' % query)
					break
				except Exception as err:
					Logger.warning("Store failed....reconnecting, attempt " + str(teller+1) + " -- " + str(err))
					Logger.warning("Query: " + query)
					try:
						CONN.close()
					except:
						pass
					if (teller + 1) == DB_RETRIES:
						raise Exception ("Store failed, max retries exceeded...")
					else:
						time.sleep(DB_WAITBETWEENRETRIES)
	except Exception as err:
		Logger.exception(str(err))
		
		
	
def get_value_from_database(dpID=None, ts=None, match=MatchTimestamp.lastprevious, tolerance=None):
	'''
	Routine to retrieve ONE value for a datapoint from the Values table in the JSEM database
	dpID argument MUST be passed
	ts to identify which timestamp will be selected, if NO ts argument is passed the value NOW will be used
	the further behavior depends on the match argument: 
	lastprevious--take the last value before this timestamp (within tolerance)
	firstnext-- take the first next value after this timestamp (within tolerance)
	tolerance is in seconds...if None is specified NO tolerance is used
	'''
	if dpID is None:
		Logger.error("Illegal or missing argument dpID")
		return None

	datatype = None
	decimals = None
	dp = None
	try:
		# Load the dp to get the datatype and decimals
		if dpID in DATAPOINTS_ID:
			dp = DATAPOINTS_ID[dpID]
		else:
			dp = load_datapoint(dpID)
		if dp is None:
			Logger.error("%s-- DatapointID does not exist, or its enabled property is NULL.." % dpID)
			return None

		if IsNot_NOE(dp.datatype): datatype = dp.datatype
		if IsNot_NOE(dp.decimals): decimals = int(dp.decimals)
		
		# check if a timestamp was passed as an argument, if not... use NOW
		if not ts: ts = int(datetime.timestamp(datetime.now()))
		query = f"SELECT * FROM 'Values' WHERE datapointID={dpID} AND timestamp<={ts} ORDER BY timestamp DESC LIMIT 1"

		# if match==MatchTimestamp.firstnext and tolerance is not None:
		# 	query = "SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp>=%s AND timestamp<=%s ORDER BY timestamp ASC LIMIT 1" % \
		# 						(dpID, ts, ts+tolerance)
		# elif match==MatchTimestamp.firstnext and tolerance is None:
		# 	query = "SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp>=%s ORDER BY timestamp ASC LIMIT 1" % (dpID, ts)
		#
		# elif match == MatchTimestamp.lastprevious and tolerance is not None:
		# 	query = f"SELECT * FROM 'Values' WHERE datapointID={dpID} AND timestamp<={ts} AND timestamp>={ts-tolerance} ORDER BY timestamp DESC LIMIT 1"
		# 	# print(query)
		# elif match == MatchTimestamp.lastprevious and tolerance is None:
		# 	query = "SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp<=%s ORDER BY timestamp DESC LIMIT 1" % (dpID, ts)
		#
		# elif match == MatchTimestamp.exact_match and tolerance is not None:
		# 	query = "SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp>=%s AND timestamp<=%s LIMIT 1" % (dpID, ts-tolerance, ts+tolerance)
		#
		# elif match == MatchTimestamp.exact_match and tolerance is None:
		# 	query = "SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp=%s LIMIT 1" % (dpID, ts)
				
		
		if USE_REMOTE_JSEM_DB:
			data, _ = tcp_sql_query(query=query)
		else:
			# Create a DB connection if needed
			try:
				db_conn = sqlite3.connect(DBFILE, uri=True)
				data = pd.read_sql_query(query, db_conn)
			except sqlite3.Error as err:
				Logger.exception(str(err))
			finally:
				db_conn.close()
				
		if data.empty: return None
		
		if datatype is not None:
			result = datatype(data['value'].iloc[0])
			if type(result) == float and decimals is not None:
				result = round(result, decimals)
			return result
		else:
			Logger.error(f'{dp.name}-- Datapoint has no datatype specified, assuming STRing')
			return str(data['value'].iloc[0])
	except Exception as err:
		Logger.exception (str(err))


def query_values_from_database(query=None):
	if query is None: return
	if not query.lower().startswith("select"):
		Logger.error("Use this routine ONLY to retrieve (get) data..%s" % query)
		return
	CONN=sqlite3.connect(DBFILE, uri=True)
	try:
		data = CONN.execute(query)
		result = cursor_to_dict(data, output=Dictionary.of_lists)
		# print ('%s records retrieved' % len(result['value']))
		return result
	except Exception as err:
		Logger.error (str(err))
	finally:
		CONN.close()


def store_df_in_database(df=None, **kwargs):
	from TCP_Routines import tcp_sql_query
	
	if df is None: return

	CONN=None
	query=''
	values_string = ''
	columnnames = ''
	table = ''
	try:
		# check if the DBstore_engine exists and is running.....
		store_direct = (Common_Data.DB_STORE is None) or (Common_Data.DB_STORE.thrd is None) or (Common_Data.DB_STORE.keeprunning is False)
		
		# Build a query from the passed dataframe, the 'table' column has the table name
		table = df.iloc[0]['table']
		columnnames = '(timestamp, datapointID, value)'
		for index, row in df.iterrows():
			values_string += "(%s, %s,'%s')," % (row['timestamp'], row['datapointID'], row['value'])
		values_string = values_string.rstrip(",")
		
		query = 'insert into \'%s\' %s values %s' % (table, columnnames, values_string)

		if USE_REMOTE_JSEM_DB:
			return(tcp_sql_query(query=query))
		elif not store_direct:
			Common_Data.DB_STORE.add_query(query)
		else:
			for teller in range(DB_RETRIES):
				try:
					CONN=sqlite3.connect(DBFILE)
					CONN.execute(query)
					CONN.commit()
					# Logger.debug('Query executed: %s' % query)
					break
				except Exception as err:
					Logger.warning("Store failed....reconnecting, attempt " + str(teller+1) + " -- " + str(err))
					# Logger.warning("Query: " + query)
					try: CONN.close()
					except: pass
					if (teller + 1) == DB_RETRIES:
						raise Exception ("Store failed, max retries exceeded...")
					else:
						time.sleep(DB_WAITBETWEENRETRIES)
	except Exception as err:
		Logger.exception(str(err))

# --------------------------------------------------------------

def load_dps_df(dpIDs=[]):
	'''
	Loads all properties of an ENABLED datapoint into a dataframe and returns that dataframe
	'''
	if dpIDs ==[]: return None
	CONN = None
	dpID_string = '(%s)' % ','.join(str(x) for x in dpIDs)
	# Create a DB connection
	try:
		query = "SELECT * FROM Datapoints WHERE enabled IS NOT NULL AND ID IN %s" % dpID_string
		if USE_REMOTE_JSEM_DB:
			dps_df, _ = tcp_sql_query(query=query)
		else:
			CONN=sqlite3.connect(DBFILE, uri=True)
			dps_df = pd.read_sql_query(query, CONN)
		return dps_df
	except Exception as err:
		print(str(err))
	finally:
		if CONN: CONN.close()


def get_min_max_timestamps (dpIDs=[], pathto_local_DBfile=None):
	# returns the lowest min and the highest max values for the timestamps of the dpIDs
	CONN=None
	
	try:
		if not pathto_local_DBfile: 	dbfile = DBFILE
		else:							dbfile = pathto_local_DBfile
		
		if dpIDs:
			query = "SELECT datapointID AS ID, min(timestamp) AS min, max(timestamp) AS max FROM 'Values' WHERE datapointID IN (%s)" % \
												(",".join([str(x) for x in dpIDs]))
		else:
			query = "SELECT min(timestamp) AS min, max(timestamp) AS max FROM 'Values'"
		# print(query)
		# input('Any key..')
		if USE_REMOTE_JSEM_DB:
			result_df, stats_df = tcp_sql_query(query=query)
			# print(stats_df)
			# print(result_df)
		else:
			CONN=sqlite3.connect(dbfile, uri=True)
			result_df = pd.read_sql_query(query, CONN)
			# print(result_df)
		min_dbts = result_df.iloc[0]['min']
		max_dbts = result_df.iloc[0]['max']
		return min_dbts, max_dbts
	except Exception as err:
		Logger.error(str(err))
	finally:
		if CONN: CONN.close()
	

def stripdatetime(selecteddate, dataselection, correction=0):
	# strips the datetime object down to the datagrouping criteria, adds a correction if needed
	# The correction is based on the unit of the datagrouping.. so DatabaseGrouping.Days -> correction in days etc.
								
	if dataselection == DataSelection.All:
		return None
	if dataselection == DataSelection._Last50:
		return None
	if dataselection.name.startswith('_'):
		return selecteddate - relativedelta(seconds=dataselection.value) + relativedelta(seconds=correction*dataselection.value)
	# elif dataselection == DataSelection.Hour:
	# 	return selecteddate.replace(minute=0, second=0, microsecond=0) + relativedelta(hours=correction)
	elif dataselection == DataSelection.Day:
		return selecteddate.replace(hour=0, minute=0, second=0, microsecond=0) + relativedelta(days=correction)
	elif dataselection == DataSelection.Week:
		# Monday is default start of week (weekday 0), to get to sunday add 1
		weekday = selecteddate.weekday() + 1
		if weekday == 7: weekday=0
		weekstart = selecteddate - relativedelta(days=weekday)
		return weekstart.replace(hour=0, minute=0, second=0, microsecond=0) + relativedelta(weeks=correction)
	elif dataselection == DataSelection.Month:
		return selecteddate.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + relativedelta(months=correction)
	elif dataselection == DataSelection.Year:
		return selecteddate.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) + relativedelta(years=correction)
	else:
		return None

	
def create_leading_timestamps(startdate, enddate, datagrouping):
	# Creates a dataframe filled with leading timestamps to be used to merge other dataframes against
	# this dataframe then dictates the timestamps. returns None if no leading timestamps can be determined..
	timestamps=[]
	if datagrouping == DatabaseGrouping.All: return None

	checkdate = startdate
	untildate = enddate
	# checkdate = stripdatetime(startdate, datagrouping)
	# untildate = stripdatetime(enddate, datagrouping)
	while checkdate < untildate:
		timestamps.append(int(datetime.timestamp(checkdate)))
		if datagrouping == DatabaseGrouping.Minute:
			checkdate = checkdate + relativedelta(minutes=1)
		if datagrouping == DatabaseGrouping.Tenmin:
			checkdate = checkdate + relativedelta(minutes=10)
		if datagrouping == DatabaseGrouping.Hour:
			checkdate = checkdate + relativedelta(hours=1)
		elif datagrouping == DatabaseGrouping.Day:
			checkdate = checkdate + relativedelta(days=1)
		elif datagrouping == DatabaseGrouping.Week:
			checkdate = checkdate + relativedelta(weeks=1)
		elif datagrouping == DatabaseGrouping.Month:
			checkdate = checkdate + relativedelta(months=1)
		elif datagrouping == DatabaseGrouping.Year:
			checkdate = checkdate + relativedelta(years=1)
		else:
			pass
	result_df = pd.DataFrame()
	result_df['timestamp']=timestamps
	result_df['timestamp']=result_df['timestamp'].astype(int)
	return result_df
	
	
	
def get_df_from_database(	dpIDs=[], dataselection=DataSelection.Day, datagrouping=DatabaseGrouping.All, aggregation=Aggregation.Not,
							selected_startdate:datetime=None, selected_enddate:datetime=None, dataselection_date=None, maxrows=None,
							IDs_as_columnheaders=False, add_datetime_column=False, merge_tolerance=3600-10):
	"""
	This routine returns a Pandas dataframe with the values of the datapoints in columns with the datapoints name or ID as columnname.
	After the first datapoint..extra datapoints will be added to this dataframe based on their timestamps whereby 
	the CLOSEST LAST (backwards) timestamp will be fitted
	:param dpIDs:			Datapoints can be passed through the dpIDs argument with their ID's
	:param dataselection: 	(only valid together with a dataselection_date and a selected_startdate and selected_enddate of None (missing)
							Determines the start and enddate automatically based on a display dataselection criterium
	:param datagrouping:	A valid datagrouping can be passed to group the result on certain timeintervals (hour, day, week, month etc.),
							default ALL=no grouping
	:param aggregation:		So data is grouped according to the datagrouping setting, now what to do in terms of aggregation (sum, min, max , mean etc. etc)
							If no aggregation is done, the first row in every group will be returned (same as First) Last is also an option...
	:param selected_startdate:
							The startdate filter on the datapoint values. Default is earliest startdate of all values of the passed dpIDs
	:param selected_enddate:
							The enddate filter on de datapoint values. Default is the latest enddate of all values of the passed dpIDs
	:param maxrows:			(only in combination with datagrouping.All):
							The maximum number of datarows to be returned.. evenly spread between the start and enddate
	:param IDs_as_columnheaders:
							Normally the columnheaders will be the datapoint names, if IDs_as_columnheaders is set to True headers will be datapoint ID's
	:param add_datetime_column:
							Optionally add an extra datetime column so that you can read the timestamp info in a friendly way, default False
	:param merge_tolerance:
							Upon merging 2 datapoints or fitting a datapoint into a fixed time distribution merging happens backwards.
							merge_tolerance specifies how far backwards a value should be taken into the merged results. Default 1 hour minus 10 seconds.
	"""
	datapoints = []
	merge_df = None
	CONN = None
	filter_str=''
	groupby_str=''
	
	if dpIDs == []: return None
	
	dps_df = load_dps_df(dpIDs)
	min_dbts, max_dbts = get_min_max_timestamps(dpIDs)
	# als er geen min en max is dan bestaan de dpIDs niet binnen de DB
	if min_dbts is None or max_dbts is None: return None
	
	starttime = selected_startdate if selected_startdate else datetime.fromtimestamp(min_dbts)
	# correct the max_dbts to the next second mark to make sure the last entry is included,
	endtime = selected_enddate if selected_enddate else datetime.fromtimestamp(max_dbts+1)
	# endtime = selected_enddate if selected_enddate else datetime.fromtimestamp(max_dbts)
	# overwrite start and endtime if dataselection_date is active 
	if dataselection_date is not None and selected_startdate is None and selected_enddate is None:
		starttime = stripdatetime(dataselection_date, dataselection)
		endtime = stripdatetime(dataselection_date, dataselection, correction=1)
	
	
	
	Logger.debug('min_dbts: %s, selected_startdate: %s, dataselection: %s, datagrouping: %s, starttime: %s' % 
					(datetime.fromtimestamp(min_dbts), selected_startdate, dataselection.name, datagrouping.name, starttime))
	# print('min_dbts: %s, selected_startdate: %s, dataselection: %s, datagrouping: %s, starttime: %s' % 
					# (datetime.fromtimestamp(min_dbts), selected_startdate, dataselection.name, datagrouping.name, starttime))
	
	Logger.debug('max_dbts: %s, selected_enddate: %s, dataselection: %s, datagrouping: %s, endtime: %s' % 
					(datetime.fromtimestamp(max_dbts), selected_enddate, dataselection.name, datagrouping.name, endtime))
	# print('max_dbts: %s, selected_enddate: %s, dataselection: %s, datagrouping: %s, endtime: %s' % 
					# (datetime.fromtimestamp(max_dbts), selected_enddate, dataselection.name, datagrouping.name, endtime))
	
	
	# de timestamp verdeling wordt op 1 van 2 manieren gerealiseerd:
	# 1: Wanneer datagrouping.All worden domweg alle datapoint timestamps binnen startime en endtime gebruikt
	# 2: en wanneer datagrouping niet ALL is wordt o.b.v. de datagrouping een serie leader timestamps aangemaakt waaraan de gegevens gefit worden
	if datagrouping != DatabaseGrouping.All:
		merge_df = create_leading_timestamps(starttime, endtime, datagrouping)
		# Als er inderdaad een timestampserie is gemaakt dan moeten we (ivm backward merging) ervoor zorgen dat de starttimestamp ruim VOOR de 
		# eerste van de leaderserie begint...anders lopen we het risico dat er net geen timestamp binnen het filter valt en dus een NaN resultaat.
		if merge_df is not None: starttime = starttime - relativedelta(seconds=merge_tolerance) 
		
	starttimestamp = int(datetime.timestamp(starttime))
	endtimestamp = int(datetime.timestamp(endtime))
	
	# Datagrouping.All gecombineerd met een maxrows getal wordt de database gevraagd om een groupby resultaat.
	# DIt geeft NIET het exacte MaxRow aantal, maar iets minder. Het is wel bloedsnel, veel sneller dan met een Pandas oplossing
	if maxrows is not None and datagrouping==DatabaseGrouping.All: 
		groupby_str = " GROUP BY (timestamp * %s) / (%s - %s)" % ((maxrows-1), endtimestamp, starttimestamp)


	# print(merge_df)
	# input('Leading Timestamps')
	
	filter_str += " AND timestamp >= %s " % starttimestamp
	filter_str += " AND timestamp < %s" % endtimestamp
	try:
		# in order to make the first dp leading we iterate over the dpIDs list, not over the dps_df dataframe
		for dpID in dpIDs:
			# get the dp info row for this dpID, because loc in this case has a filter it returns a dataframe not a series, hence the squeeze()
			row=dps_df.loc[dps_df['ID']==dpID].squeeze()
			dpname = row['name']
			dpdatatype = row['datatype']

			query = "SELECT timestamp, value FROM 'Values' WHERE datapointID=%s%s%s ORDER BY timestamp ASC" % \
										(dpID, filter_str, groupby_str)

			# Get the data for this datapoint in a dataframe
			if USE_REMOTE_JSEM_DB:
				dp_df, _ = tcp_sql_query(query=query)
			else:
				CONN=sqlite3.connect(DBFILE, uri=True)
				dp_df = pd.read_sql_query(query, CONN)
			dp_df = dp_df.astype({'value': get_type(dpdatatype), "timestamp":int})
				
			columnheader = str(dpID) if IDs_as_columnheaders else dpname
			dp_df = dp_df.rename(columns={'value':columnheader})
				
			# Add an extra column named group to help group the data
			if datagrouping != DatabaseGrouping.All:
				if datagrouping==DatabaseGrouping.Year:
					dp_df['group'] = [int(datetime.fromtimestamp(x).replace(month=1,day=1,hour=0,minute=0,second=0).timestamp()) for x in dp_df['timestamp'].values]
				elif datagrouping==DatabaseGrouping.Month:
					dp_df['group'] = [int(datetime.fromtimestamp(x).replace(day=1,hour=0,minute=0,second=0).timestamp()) for x in dp_df['timestamp'].values]
				elif datagrouping==DatabaseGrouping.Week:
					dp_df['group'] = [int(get_begin_of_week(datetime.fromtimestamp(x)).timestamp()) for x in dp_df['timestamp'].values]
				elif datagrouping==DatabaseGrouping.Day:
					dp_df['group'] = [int(datetime.fromtimestamp(x).replace(hour=0,minute=0,second=0).timestamp()) for x in dp_df['timestamp'].values]
				else:
					dp_df['group'] = [(x - (x % datagrouping.value)) for x in dp_df['timestamp'].values]
					
				# print('dp_df')
				# print (dp_df)
				# Waitkey()
			
				if aggregation == Aggregation.Diff:
					dp_df = dp_df.groupby('group')[columnheader].agg(['min','max']).diff(axis=1).drop(columns=['min'])
					dp_df = dp_df.reset_index()
					dp_df = dp_df.rename(columns={'max':columnheader})
				elif aggregation == Aggregation.Not:
					dp_df = dp_df.groupby('group')[columnheader].agg('first')
					dp_df = dp_df.reset_index()
				else:
					# aggregation != Aggregation.Not
					dp_df = dp_df.groupby('group')[columnheader].agg(str(aggregation.name).lower())
					dp_df = dp_df.reset_index()
					
				dp_df['timestamp'] = dp_df['group'].astype(int)
				# print (dp_df.dtypes)
				# print (dp_df)
				# input('dp_df groupby and groups processed on %s' % aggregation.name)
				
			# elif maxrows is not None and datagrouping==DatabaseGrouping.All:
				# # Bij datagrouping.All kan nog een maxrows meegegeven zijn, als dat zo is maak dan een selectie
				# skipper = math.ceil(len(dp_df)/maxrows)
				# dp_df = dp_df.iloc[::skipper]
				# dp_df = dp_df.reset_index()
				# # print (dp_df)
				# # input('dp_df met maxrows= %s' % maxrows)
				
				
			dp_df = dp_df[['timestamp', columnheader]]
			
			# print (dp_df)
			# input('dp_df')
			
			# merge the data, there may already be a leading set of timestamps preset in the merge_df
			if merge_df is None:
				merge_df = dp_df
			else:
				merge_df = pd.merge_asof(merge_df, dp_df, on="timestamp", direction="backward", tolerance=merge_tolerance)
				# merge_df = pd.merge_asof(merge_df, dp_df, on="timestamp", direction="nearest", tolerance=merge_tolerance)
				# replace all NaN entries with 0 in the new column
				# merge_df[dp.name] = merge_df[dp.name].fillna(0)
			
		if add_datetime_column: merge_df['datetime'] = [datetime.fromtimestamp(x) for x in merge_df['timestamp'].values]
		return merge_df
	except Exception as err:
		# print(str(err))
		Logger.error(str(err))
	finally:
		if CONN: CONN.close()

	
def get_values_from_database(datapoint, maxrows=Max_Chart_Points, data_selection=DataSelection.All, start=datetime.now()):
	# format of the starttime string (optional) is: 20-7-2022 23:00:00
	# Minutes and seconds will not be taken into account... only whole hours..
	
	# A special case is the last50 selection....NO DATABASE info is needed for this one.
	if data_selection == DataSelection._Last50:
		return None
	CONN=sqlite3.connect(DBFILE, uri=True)
	try:
		maxrows = int(maxrows)
		filterstr = ""
	
		if data_selection == DataSelection.All:
			# query = "SELECT * FROM (SELECT value,timestamp FROM 'Values' WHERE datapointID = %s %s ORDER BY timestamp DESC LIMIT %s) ORDER BY timestamp ASC" % (str(datapoint.ID), skipstr, str(maxrows))
			query = "SELECT * FROM (SELECT value,timestamp FROM 'Values' WHERE datapointID = %s ORDER BY timestamp DESC) ORDER BY timestamp ASC" % (datapoint.ID)
		else:
			dt_now = start if start is not None else datetime.now()
			starttimestamp, endtimestamp = Calculate_Period(data_selection=data_selection, re_timestamp=int(datetime.timestamp(dt_now)))
			filterstr = " AND timestamp >= %s AND timestamp <= %s" % (str(starttimestamp), str(endtimestamp))
			query = "SELECT * FROM (SELECT value,timestamp FROM 'Values' WHERE datapointID = %s %s ORDER BY timestamp DESC) ORDER BY timestamp ASC" % (datapoint.ID, filterstr)
	
		# print ('query: ' + query)
		data = CONN.execute(query)
		
		result = cursor_to_dict(data, output=Dictionary.of_lists)
		# print ('%s records retrieved' % len(result['value']))
		# apply a skipfactor on the results if needed
		if len(result["value"]) > maxrows:
			skipfactor = int(len(result["value"])/maxrows)
			result["value"] = result["value"][0::skipfactor]
			result["timestamp"] = result["timestamp"][0::skipfactor]
		
		# timestamp is al een INTEGER in de DB, geen conversie nodig, values moeten wel een type conversie ondergaan
		result["value"] = [datapoint.datatype(x) for x in result["value"]]
		# print (result)
		return result
	except Exception as err:
		Logger.error (str(err))
	finally:
		CONN.close()


def get_valueseries_from_database(datapointID, begin_ts=None, end_ts=None, last_one=False, order="ASC", limit=None):

	CONN=sqlite3.connect(DBFILE, uri=True)

	if last_one:
		query = ("SELECT * FROM 'Values' WHERE datapointID=%s ORDER BY timestamp DESC limit 1" % datapointID)
	else:
		limit_str = "limit %s" % limit if limit is not None else ""
		
		if end_ts is None or begin_ts==end_ts:
			query = ("SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp=%s" % (datapointID, begin_ts))
		elif begin_ts < end_ts:
			query = ("SELECT * FROM 'Values' WHERE datapointID=%s AND timestamp>=%s AND timestamp <%s order by timestamp %s %s" % 
													(datapointID, begin_ts, end_ts, order, limit_str))
		else:
			raise ValueError('Begin timestamp is larger then end timestamp')


	for teller in range(DB_RETRIES):
		try:
			data = CONN.execute(query)
			break
		except Exception as err:
			Logger.warning("Read failed, attempt " + str(teller+1) + " -- " + str(err))
			Logger.warning("Query: " + query)
			if (teller + 1) == DB_RETRIES:
				raise Exception ("Read failed, max retries exceeded...")
			else:
				time.sleep(DB_WAITBETWEENRETRIES)
				
	result = cursor_to_dict(data, output=Dictionary.of_lists)
	CONN.close()
	return result




def load_protocol(targetobject=None, *args, **kwargs):
	'''
	This routine returns all key information for a specific protocol, identified by its DB ID key (int) or name
	It populates the targetobject or makes a new generic Protocol ceobject and returns it.
	'''
	CONN=sqlite3.connect(DBFILE, uri=True)
	try:
		
		if targetobject == None: targetobject = Protocol()
		if "ID" in kwargs: query = "SELECT * FROM Protocol where ID=%s" % (str(kwargs["ID"]))
		elif "name" in kwargs: query = "SELECT * FROM Protocol where name='%s'" % (str(kwargs["name"]))
		else:
			raise Exception ("No arguments passed to routine..")
			
		col_names = []
		data = CONN.execute(query)
		
		for col_info in data.description:
			col_names.append(col_info[0])
		for row in data:
			teller=0
			for col in row:
				setattr(targetobject,col_names[teller],row[teller])
				teller +=1
		return targetobject
	except Exception as err:
		Logger.exception(str(err))
	finally:
		CONN.close()
		

def populate_interface(interf=None, name='', ID=None, **kwargs):
	"""
	Populates an Interface object with properties that are fields in the 'Interface' database table
	:param interf: The interface object to be populated
	:param name: Search name matching a name in the Interface table
	:param ID: Search ID matching an ID in the Interface table
	:param kwargs:
	:return: The populated interface
	:raises ValueError if both a name and/or an ID are missing in the arguments
	"""
	CONN=sqlite3.connect(DBFILE)
	try:
		if interf == None: raise ValueError("No interface object passed to routine")
		
		if ID: 		query = f"SELECT * FROM Interface where ID={ID}"
		elif name: 	query = f"SELECT * FROM Interface where name='{name}'"
		else:		raise ValueError ("No valid interface ID or name argument passed to routine..")
		
		result_df = pd.read_sql_query(query, CONN)
		for attribute in result_df:
			if result_df[attribute].dtypes == numpy.int64:
				result_df[attribute] = result_df[attribute].astype(numpy.int32)
			value = result_df.loc[0][attribute]
			setattr(interf, attribute, value)
		
		INTERFACE_ID[interf.ID]=interf
		INTERFACE_NAME[interf.name]=interf
		return interf
	except ValueError as err:
		Logger.info(str(err))
	except Exception as err:
		Logger.exception(str(err))
	finally:
		CONN.close()


def get_pollmessages_from_database(interfaceID):
	'''
	This routine returns all ID,name,searchkey,poll_interval from datapoints with polling enabled and a  poll_interval that is not NULL or empty
	data is returned in a dictionary called pollmsg_name,
	and uses the name as the dictionary key.
	It also returns a dictionary with the same messagedefinitions but with the ID as key: pollmsg_id
	'''
	pollmsg_id = dict()
	pollmsg_name = dict()
	
	CONN=sqlite3.connect(DBFILE, uri=True)
	try:
		query = "SELECT ID,name,searchkey,poll_interval FROM Datapoints WHERE interfaceID=%s AND enabled=1 AND poll=1 AND poll_interval IS NOT NULL AND poll_interval != ''" % (interfaceID)
		# print (query)
		data = CONN.execute(query)

		col_names = []
		for col_info in data.description:
			col_names.append(col_info[0])
		# print (col_names)
		for row in data:
			pollmsgdef = Pollmessage()
			teller=0
			for col in row:
				# print (col_names[teller] + "=" + str(row[teller]) + " | " + str(type(row[teller])))
				# print (col_names[teller] + ":" + str(row[teller]))
				setattr(pollmsgdef,col_names[teller],row[teller])
				# print (str(getattr(pollmsgdef, col_names[teller])))
				teller +=1
			# print (pollmsgdef.name + ":" + str(pollmsgdef.ID) + ":" + str(pollmsgdef.enabled))
			# dump(pollmsgdef)
			# Waitkey()
			pollmsg_name[pollmsgdef.name]=pollmsgdef
			pollmsg_id[pollmsgdef.ID]=pollmsgdef
		# print(pollmsg_id)
		# Waitkey
		return pollmsg_name, pollmsg_id
		
	except Exception as err:
		Logger.exception(str(err))
	finally:
		CONN.close()

def load_all_categories():
	from tqdm import tqdm
	import time
	'''
	This routine loads all categories in a dictionary called CATEGORY_NAME,
	and uses the name as the dictionary key.
	It also creates a dictionary with the same categories but with the ID as key.
	'''
	
	CONN=sqlite3.connect(DBFILE, uri=True)
	col_names = []
	try:

		query = "SELECT * FROM Category"
		data = CONN.execute(query)
		
		for col_info in data.description:
			col_names.append(col_info[0])
		
		for row in data:
			cat = Category()
			teller=0
			for col in row:
				# print (col_names[teller] + "=" + str(row[teller]) + " | " + str(type(row[teller])))
				setattr(cat,col_names[teller],row[teller])
				teller +=1
			CATEGORY_NAME[cat.name]=cat
			CATEGORY_ID[cat.ID]=cat
		# print (CATEGORY_ID)
		# print (CATEGORY_NAME)
	except Exception as err:
		Logger.exception(str(err))
	finally:
		CONN.close()


def get_displaysorted_datapoint_names(categoryID):
	'''
	returns a ordered dictionary with the ordered sub_categories of categoryID as keys
	for each sub category the names of all enabled datapoints are added in a list ordered on display_order
	'''
	CONN=sqlite3.connect(DBFILE, uri=True)
	try:
		# print ("get_displaysorted_datapoint_names called")
		
		query = "select sub_cat, name from Datapoints where enabled is not null and display_order is not null and categoryID=%s order by sub_cat ASC, ifnull(display_order,9999) ASC" % (categoryID)
		query_result = cursor_to_dict(CONN.execute(query), output=Dictionary.of_lists)


		result = dict()
		for teller, naam in enumerate(query_result["name"]):
			sub_cat = query_result["sub_cat"][teller]
			if sub_cat not in result:
				result[sub_cat]=[]
			result[sub_cat].append(naam)
			
		# print (result)
		# Waitkey()
		return result
	except Exception as err:
		Logger.exception (str(err))
	finally:
		CONN.close()
		
def load_lastvalues(dpIDs=[]):
	'''
	Returns 2 dictionaries 1 with last values and 1 with timestamps (both keyed on datapont ID) of a passed list of datapointIDs, 
	an empty list of datapointIDs causes the last values and timestamps of ALL datapoints to be retrieved
	'''
	last_values=dict()
	last_timestamps=dict()
	CONN=sqlite3.connect(DBFILE, uri=True)
	try:
		# Retrieve all the LAST stored values and timestamp of all datapoints from the DB and put them in 2 disctionaries 
		# keyed by datapointID
		if dpIDs==[]:
			query = "SELECT datapointID, value, max(timestamp) as 'timestamp' FROM 'Values' GROUP BY datapointID"
		else:
			dp_list = ','.join(str(dpID) for dpID in dpIDs)
			query = "SELECT datapointID, value, max(timestamp) as 'timestamp' FROM 'Values' WHERE datapointID IN (%s) GROUP BY datapointID" % dp_list
		data = CONN.execute(query)
		# print ("Query executed")
		result = cursor_to_dict(data, output=Dictionary.of_lists)
		for teller, dp_id in enumerate(result["datapointID"]):
			last_values[dp_id]=result["value"][teller]
			last_timestamps[dp_id]=result["timestamp"][teller]
		return last_values, last_timestamps
	except Exception as err:
		Logger.exception(str(err))
	finally:
		CONN.close()

def load_datapoint(dpID=None, dp=None, doNotLoad_list=[]):
	'''
	Loads all properties of an ENABLED datapoint into dp (if provided) or creates a new datapoint object and populates that
	The doNotLoad_list argument can be used to pass the name (case sensitive) of the properties/columns to EXCLUDE
	An existing DB connection can be passed to be used, it wont be closed. Alternatively the routine will open AND close its own DB connection
	This routine returns the populated datapoint object
	'''
	if dpID is None:
		Logger.error("Illegal or missing argument dpID")
		return None
	query = "SELECT * FROM Datapoints WHERE enabled IS NOT NULL AND ID=%s" % dpID
	shut_the_door_behind_you = False
	
	try:
		if USE_REMOTE_JSEM_DB:
			data, _ = tcp_sql_query(query=query)
		else:
			# Create a DB connection if needed
			try:
				db_conn = sqlite3.connect(DBFILE, uri=True)
				data = pd.read_sql_query(query, db_conn)
			except sqlite3.Error as err:
				Logger.exception(str(err))
			finally:
				db_conn.close()
		
		if data.empty: return None
		
		if dp is None: dp = Datapoint()
		for col_name in data.columns:
			if col_name in doNotLoad_list: continue
			# populate the properties
			value = data[col_name].iloc[0]
			if col_name == "datatype":
				setattr(dp, col_name, get_type(value))
			elif col_name == "enabled":
				setattr(dp, col_name, bool(value))
			elif col_name == "poll":
				setattr(dp, col_name, bool(value))
			elif col_name == "dbstore":
				setattr(dp, col_name, bool(value))
			elif col_name == "log_messages":
				setattr(dp, col_name, bool(value))
			else:
				setattr(dp, col_name, value)
		# make sure initial_value and last_value also have the correct datatype
		if IsNot_NOE(dp.initial_value):
			dp.initial_value = dp.datatype(dp.initial_value)
		if IsNot_NOE(dp.last_value):
			dp.last_value = dp.datatype(dp.last_value)
		return dp
	except Exception as err:
		Logger.exception(str(err))


def load_datapoints(dpIDs=[], dps=[], doNotLoad_list=[]):
	'''
	Loads all datapoints from the dpIDs list into memory and builds the DATAPOINTS_ID and DATAPOINTS_NAME dictionaries
	When NO dpIDs list is passed...ALL enabled datapoints are loaded. In that case also the DATAPOINTS_ID and DATAPOINTS_NAME dictionaries
	will be cleaned and completely rebuild
	Alternatively a list of datapoint objects can be passed, this overrules the list of datapoint ID's
	These objects will be populated from the database
	The doNotLoad_list argument can be used to pass the name (case sensitive) of the properties/columns to EXCLUDE from populating from the DB
	'''
	if dpIDs == [] and dps == []:
		# Now load ALL enabled datapoints:
		query = "SELECT * FROM Datapoints WHERE enabled IS NOT NULL"
		DATAPOINTS_ID.clear()
		DATAPOINTS_NAME.clear()
	elif dps != []:
		dp_list = ','.join(str(dp.ID) for dp in dps)
		query = "SELECT * FROM Datapoints WHERE enabled IS NOT NULL AND ID IN (%s)" % dp_list
	elif dpIDs != []:
		dp_list = ','.join(str(ID) for ID in dpIDs)
		query = "SELECT * FROM Datapoints WHERE enabled IS NOT NULL AND ID IN (%s)" % dp_list
		
		
	dp=None
	try:
		if USE_REMOTE_JSEM_DB:
			data, _ = tcp_sql_query(query=query)
		else:
			# Create a DB connection if needed
			try:
				db_conn = sqlite3.connect(DBFILE, uri=True)
				data = pd.read_sql_query(query, db_conn)
			except sqlite3.Error as err:
				Logger.exception(str(err))
			finally:
				db_conn.close()
	
		for teller, row in data.iterrows():
			if dps != []:
				# use an existing Datapoint object and fill the properties
				dp = dps[teller]
			else:
				# create a new Datapoint object and fill the properties
				dp = Datapoint()
			for col_name in data.columns:
				if col_name in doNotLoad_list: continue
				# populate the properties
				value = row[col_name]
				if col_name == "datatype":
					setattr(dp, col_name, get_type(value))
				elif col_name == "enabled":
					setattr(dp, col_name, bool(value))
				elif col_name == "poll":
					setattr(dp, col_name, bool(value))
				elif col_name == "dbstore":
					setattr(dp, col_name, bool(value))
				elif col_name == "log_messages":
					setattr(dp, col_name, bool(value))
				else:
					setattr(dp, col_name, value)
			# make sure initial_value and last_value also have the correct datatype
			if IsNot_NOE(dp.initial_value):
				dp.initial_value = dp.datatype(dp.initial_value)
			if IsNot_NOE(dp.last_value):
				dp.last_value = dp.datatype(dp.last_value)
				
			DATAPOINTS_ID[dp.ID] = dp
			DATAPOINTS_NAME[dp.name] = dp
		Logger.info(f"Loaded {len(data)} datapoints from the database..")
	except Exception as err:
		if dp is not None: Logger.error(f"{dp.name}--Error loading and setting properties")
		Logger.exception(str(err))

def load_and_configure_datapoints(dpIDs=[]):
	from tqdm import tqdm
	'''
	Loads all datapoints from the DB and calculates all necessary extra properties to populate the Datapoint objects.
	Nothing is written to the DB, hence no COMMIT is needed.
	'''
	dp=None
	try:
		load_datapoints(dpIDs=dpIDs)
		num_dps = len(DATAPOINTS_NAME.values())
		print("")
		# for teller,dp in enumerate(DATAPOINTS_NAME.values(), start=1):
		for teller,dp in enumerate(tqdm(DATAPOINTS_NAME.values())):
			'''
			See the document: Functional specs PRESET and DB store and retrieve routines for datapoints.docx
			'''
			# update_progressbar(max_num=num_dps, act_num=teller, max_bars=100)
			if dp.enabled: dp.initialize_datapoint()
			# Waitkey()
		print("")
		Logger.info("Finished initialization of datapoints.")
		
		
	except Exception as err:
		if dp is not None: Logger.error("%s--initialization" % dp.name)
		Logger.exception (str(err))
		




def main(args):
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
