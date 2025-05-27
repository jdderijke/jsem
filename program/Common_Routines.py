import __main__

from glob2 import glob

import Common_Data
from LogRoutines import Logger

if __name__ == "__main__":
	 __main__.logfilename = "EV_Optimzer.log"
	 __main__.backupcount = 2
import os
import sys

# print (sys.path)
import logging
# from LogRoutines import Logger
import socket
# import glob
from Common_Enums import *
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
from pathlib import Path

'''
Returns the current ip_address of the system
'''
def get_ip_address():
		 ip_address = '';
		 s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		 s.connect(("8.8.8.8",80))
		 ip_address = s.getsockname()[0]
		 s.close()
		 return ip_address

'''
cpu_temp returns the temperature in Celcius in thermal zone 0 aka the CPU
the value argument is not used and only here for compatibility purposes
'''
def cpu_temp(value=None):
	f = open("/sys/class/thermal/thermal_zone0/temp", "r")
	t = f.readline ()
	f.close()
	return (int(t)/1000)

'''
free_diskspace_mb returns de free diskspace in MB as seen from the path variable
the value argument is not used and only here for compatibility purposes
'''
def free_diskspace_mb(value=None, path='/'):
	st = os.statvfs(path)
	
	# free blocks available * fragment size
	bytes_avail = (st.f_bavail * st.f_frsize)
	megabytes = float(bytes_avail / 1024 / 1024)
	gigabytes = float(bytes_avail / 1024 / 1024 / 1024)
	return megabytes

'''
string_builder is a routine that adds an insertstring into a motherstring at the specified index location
It automatically sizes the motherstring UP to fit the insertstring if necessary
'''
def string_builder (motherstring, index, insertstring):
	try:
		if len(motherstring) < index:
			# add spaces till the index location
			resultstring = motherstring + "_" * ((index) - len(motherstring)) + insertstring
			return resultstring
		elif len(motherstring) < (index + len(insertstring)):
			resultstring = motherstring[:index] + insertstring
			return resultstring
		else:
			resultstring = motherstring[:index] + insertstring + motherstring[index+len(insertstring):]
			return resultstring
	except Exception as err:
		Logger.error(str(err))

'''
conv_from_string returns an Boolean, Integer, Float or String derived from the data_string
data_type determines the type of conversion that will happen
Raises an exception when the conversion fails
'''
def conv_from_string(data_string, data_type):
		if data_type==bool and data_string.strip().upper() in ["ON", "AAN", "TRUE", "WAAR", "JA"]: return True
		elif data_type==bool and data_string.strip().upper() in ["OFF", "UIT", "FALSE", "ONWAAR", "NEE"]: return False
		elif data_type==int:
				try:
						result = int(data_string.strip())
						return result
				except:
						raise Exception("Not a valid integer")
		elif data_type==float:
				try:
						result = float(data_string.strip())
						return result
				except:
						raise Exception("Not a valid floating point number")
		elif data_type==str:
			result = data_string.strip()
			return result

'''
ddlist_from_value returns a LIST with strings that can be used for a pulldown menu in a data entry field
The list is populated based on the value argument:
If the value argument is boolean type, then the list contains the normal boolean selections like AAN en UIT etc.
If the value is INT or FLOAT a list is returned with several strings indicating values above and below the value argument.
Also the current string representation of the value argument is returned as selected_item...
'''
def ddlist_from_value(value):
		ddlist = []
		selected_item=""

		if type(value)==bool: 
				ddlist.append("AAN")
				ddlist.append("UIT")
				if value: selected_item = "AAN"
				else: selected_item = "UIT"
				
		elif type(value)==int:
				for perc in [-100,-50,-20,-15,-10,-5,0,5,10,15,20,50,100]:
						if perc == 0:
								if str(value-3) not in ddlist: ddlist.append(str(value-3))
								if str(value-2) not in ddlist: ddlist.append(str(value-2))
								if str(value-1) not in ddlist: ddlist.append(str(value-1))
								ddlist.append(str(value))
								if str(value+1) not in ddlist: ddlist.append(str(value+1))
								if str(value+2) not in ddlist: ddlist.append(str(value+2))
								if str(value+3) not in ddlist: ddlist.append(str(value+3))
						else:
								ddlist.append(str(value + int((perc/100.0)*value)))
				selected_item = str(value)
				
		elif type(value)==float: 
				for perc in [-100,-50,-20,-15,-10,-5,0,5,10,15,20,50,100]:
						if perc == 0:
								ddlist.append(str(value))
						else:
								ddlist.append(str(value + (perc/100.0)*value))
				selected_item = str(value)
						
		elif type(value)==str: 
				if value.upper() in ["AAN", "UIT"]:
						ddlist.append("AAN")
						ddlist.append("UIT")
				elif value.upper() in ["TRUE", "FALSE"]:
						ddlist.append("TRUE")
						ddlist.append("FALSE")
				selected_item = value.upper()
		return ddlist, selected_item
		
import builtins

def get_type(type_name):
	try:
		return getattr(builtins, type_name)
	except AttributeError:
		return None
		
def dump(obj):
	for attr in dir(obj):
		print("obj.%s = %r" % (attr, getattr(obj, attr)))
	
def get_newest_file(path):
	# print("path plus pattern = %s" % path)
	files = glob.glob(path)
	if files == []:
		return None
	else:
		return max(files, key=os.path.getctime)
		
def get_files(path, option='all'):
	import glob
	# print("path plus pattern = %s" % path)
	files = glob.glob(path)
	
	if files == []:
		return []
	elif option.lower()=='newest':
		return max(files, key=os.path.getctime)
	elif option.lower()=='oldest':
		return min(files, key=os.path.getctime)
	elif option.lower()=='all':
		files = sorted(files, key=os.path.getctime)
		return files


def normalize_data(df:pd.DataFrame, normalize:str ='mean_std', settings:dict ={}):
	'''
	This routine normalizes the data in 1 of 2 possible ways:
	mean_std: substract the mean from the data and then divide by the std deviation
	min_max: Scale everything back to a range between 0.0 and 1.0
	
	:param df: The pandas dataframe to normalize
	:param normalize: 'mean_std' or 'min_max'
	:param settings: a dictionary with per column a dictionary with mean/std or min/max presets
	:return: the normalized data (in a dataframe) and a dataframe with the mean/std or min/max values per column
	'''
	'''
	'''
	result_settings = settings.copy()
	
	from pandas.api.types import is_numeric_dtype
	# Normalizes all numerical data in a dataframe, shifts each column by its mean and scales it by its stddev
	def shift_and_scale(col):
		if is_numeric_dtype(col):
			if settings:
				mean = settings[col.name]['mean']
				stddev = settings[col.name]['stddev']
			else:
				mean = col.mean()
				stddev = col.std()
				result_settings[col.name]={}
				result_settings[col.name]['mean'] = mean
				result_settings[col.name]['stddev'] = stddev
			col = col - mean
			if stddev != 0.0: 
				col = col / stddev
		return col
		
	def min_max_scale(col):
		if is_numeric_dtype(col):
			if settings:
				min_value = settings[col.name]['min']
				max_value = settings[col.name]['max']
			else:
				min_value = col.min()
				max_value = col.max()
				result_settings[col.name]={}
				result_settings[col.name]['min'] = min_value
				result_settings[col.name]['max'] = max_value
				
			if min_value != max_value:
				col = (col - min_value)/(max_value - min_value)
			else:
				# all values are equal... so 0 for 0 and 1 for everything else
				col = pd.np.where(col != 0, 1.0, 0.0)
		return col
		
	if normalize == 'mean_std':
		# Shift the data by the mean per columns and scale by the stddev per columns
		return df.apply(lambda x: shift_and_scale(x), axis=0), result_settings
	elif normalize == 'min_max':
		# now scale everything in a range between 0 and 1
		return df.apply(lambda x: min_max_scale(x), axis=0), result_settings
	else:
		raise Exception(f'non existing normalization method..{normalize}')



def is_child_of(child, parent):
	'''
	Determines if child Remi Widget is in any way a descendant of the parent Remi Widget
	:param child:
	:param parent:
	:return: True or False
	'''
	level_up = child.get_parent()
	if level_up is None:
		return False
	elif level_up is parent:
		return True
	else:
		return is_child_of(level_up, parent)
	
	
# def is_child_of(child, parent):
# 	try:
# 		for key in parent.children:
# 			if key.isdecimal():
# 				offspring = parent.children[key]
# 				print(f'checking offspring: {offspring} vs {parent}')
#
# 				if offspring is child:
# 					print(f'{child} is_child_of {parent}')
# 					return True
# 				else:
# 					return is_child_of(child, offspring)
# 		return False
# 	except Exception as err:
# 		Logger.exception(str(err))
# 		return False
	
	
# def isnumeric(checkstring=""):
	# try:
		# tmp=int(checkstring)
		# return True
	# except:
		# pass
		
	# try:
		# tmp2=float(checkstring)
		# return True
	# except:
		# pass
		
	# return False	
	
import inspect
def Waitkey(prompt='Press any key to continue: '):
	"""
	Prints a prompt and waits for a keypress
	:param prompt:
	"""
	wait = input(inspect.currentframe().f_back.f_code.co_name + '> ' + prompt)

def dump(obj):
	"""

	:param obj:
	:return: Prints all attributes of the passed object
	"""
	for attr in dir(obj):
		print("obj.%s = %r" % (attr, getattr(obj, attr)))

def dump_dict(obj:dict):
	'''
	Dumps a dictionary in key:value pairs
	:param obj:
	:return:
	'''
	if not type(obj) is dict: raise TypeError
	for k,v in obj.items():
		print (f'key= {k} : value= {v}')
	
def Is_NOE(value):
	''' returns True if (NULL/None or Empty) '''
	if value is None: return True
	if type(value) in [str, list, dict, bytearray] and len(value) == 0: return True
	return False
	
def IsNot_NOE(value):
	''' returns True if NOT (NULL/None or Empty)'''
	return not Is_NOE(value)
   
# def expandcollapse(*args, **kwargs):
# 	# print ("expandcollapse_clicked called")
# 	kwargs['exp_scr'].css_width = "90%"
# 	kwargs['coll_scr'].css_width = "10%"


def expandcollapse(expand_cont, collaps_cont, **kwargs):
	# print ("expandcollapse_clicked called")
	charts_parent = Common_Data.CHARTS_PARENT_CONTAINER
	data_parent = Common_Data.DATA_PARENT_CONTAINER
	# dont expand an empty charts area
	if expand_cont is charts_parent and len(charts_parent.children.keys()) == 0:
		return
	expand_cont.css_width = "90%"
	collaps_cont.css_width = "10%"
	if collaps_cont is charts_parent:
		visibility = 'hidden'
	else:
		visibility = 'visible'
	
	if len(charts_parent.children.keys()) > 0:
		# We have active charts..
		for child_key in charts_parent.children.keys():
			chart = charts_parent.children[child_key]
			if hasattr(chart, 'legendbox'): chart.legendbox.style['visibility'] = visibility
			if hasattr(chart, 'controlbox'): chart.controlbox.style['visibility'] = visibility
			
	pass	# debug point

def Calculate_Timerset(start_timestamp=None, wakeup_mode=None, interval=None):
	'''
	Routine calculates and returns the initial timerset (in seconds) and the repeating timerset (after the first one)
	The timerset is the time (in seconds) between NOW and the interval applied to the passed start_timstamp (or NOW if None)...
	so the time left from NOW if the interval was applied to the passed start_timstamp.
	
	If that time left is negative, the the timer should have fired already... then the interval is applied to NOW...
	
	for intervals in day, week month and year... the timerset is calculated to the NEXT appropriate moment from NOW, 
	so the start_timestamp is not taken into account....NOW is used instead
	
	interval argument are either:
		- strings indicating an time and interval (e.g. hourly, daily etc): 
				returns initial timerset to top of the hour/day/month etc
				returns repeat timerset as interval corresponding to hour/day/month etc
				Voor al deze modes wordt de timerset t.o.v. start_timestamp berekent als die meegegeven is, t.o.v. NU als niet meegegeven
		- strings indicating only an interval (e.g. in1hour, in2hour, in6hour etc)
				returns initial and repeat timerset as interval corresponding to hour, 2hours etc.
				Voor al deze modes wordt de timerset t.o.v. start_timestamp berekent als die meegegeven is, t.o.v. NU als niet meegegeven
		- integer values in seconds (e.g. 1, 3600 etc)
				returns initial and repeat timerset as interval corresponding integer value
		- negative integer values, indicating a one_time_poll only at start_up (handled by the poller_start routine of the interface)
				returns initial timerset as interval corresponding to absolute integer value
				returns repeat timerset as None
		- date-time strings:
				MM-DD UU:MM:SS.  
				Dus 15 23:30:00 betekent de 15e van iedere maand om 23:30:00
				:15 betekent de 15e seconde van iedere minuut
				13:22 betekent 13 minuten en 22 seconden na ieder uur
				15:00:00 betekent iedere middag om 15:00 uur
				returns initial timerset as interval to the first occurence of the specified time/date
				returns repeat timerset as interval corresponding to the specified time/date interval
	wakeup_mode (Enum) (overrules interval):
			Same as the string definitions above
			Voor al deze modes wordt de timerset t.o.v. start_timestamp berekent als die meegegeven is, t.o.v. NU als niet meegegeven
				Wakeup_Mode.in1hour
				Wakeup_Mode.in2hour
				etc.
				Wakeup_Mode.day
				Wakeup_Mode.week
				Wakeup_Mode.month
				Wakeup_Mode.year
	'''
	timerset = None
	repeatset = None
	try:
		# bepaal de referentietijdstip en nu tijdstip
		start_ts =time.time() if start_timestamp is None else start_timestamp
		start_dt = datetime.fromtimestamp(start_ts)
		if wakeup_mode is not None:
			# wakeup_mode gaat VOOR interval
			interval = wakeup_mode
		else:
			if interval == None: 
				raise ValueError ("No valid input parameters: interval = None")
			elif str(interval).isnumeric():
				# de meest simpele case...gewoon een numerieke timerset 
				timerset = int(float(interval))
				if timerset < 0:
					# negative means only 1 time, so no repeat timerset
					return abs(timerset), None
				else:
					return timerset, timerset
			elif ':' in interval or '-' in interval:
				# MM-DD UU:MM:SS string
				# this is an absolute timepoint, so we calculate it based on now and find the first occurence of the timepoint
				then = datetime.now().replace(microsecond=0)
				time_elements = ['second','minute','hour','day','month','year']
				delta_elements = ['seconds','minutes','hours','days','months','years']
				
				# maak een splitstr met alle elementen
				splitstr = interval.split(' ')
				if len(splitstr) == 1:
					splitstr = interval.split(':')
				else:
					splitstr = interval.split(' ')[0].split('-') + interval.split(' ')[1].split(':')

				# draai de volgorde om zodat seconden eerst komen
				splitstr.reverse()
				for teller, element in enumerate(splitstr):
					if splitstr[teller] != '': 
						arg = {time_elements[teller]:int(splitstr[teller])}
						then=then.replace(**arg)
						# hou bij wat het hoogste gewijzigde element is in THEN
						highest_index = teller
						
				# print (str(then))
				delta_index = highest_index if highest_index == len(time_elements) - 1 else highest_index + 1
				arg = {delta_elements[delta_index]:1}
				if int(datetime.timestamp(then)) - time.time() <= 0:
					# we zouden uitkomen op een tijdstip dat VOOR nu ligt, we verhogen het element BOVEN het hoogst gewijzigde element met 1
					then = then + relativedelta(**arg)
				# bepaal het eerste herhaal tijdstip
				repeat = then + relativedelta(**arg)


				# print (str(then))
				# convert to timestamp, rounded to seconds
				# print('then = %s' % then)
				then = int(datetime.timestamp(then))
				# print ('repeat = %s' % repeat)
				repeat = int(datetime.timestamp(repeat))
				timerset = then - int(time.time())
				repeatset = repeat - then
				return timerset, repeatset
				
			elif interval in ["1hour","in1hour"]: interval = Wakeup_Mode.in1hour
			elif interval in ["2hour","in2hour"]: interval = Wakeup_Mode.in2hour
			elif interval in ["6hour","in6hour"]: interval = Wakeup_Mode.in6hour
			elif interval in ["12hour","in12hour"]: interval = Wakeup_Mode.in12hour
			elif interval in ["24hour","in24hour"]: interval = Wakeup_Mode.in24hour
			elif interval in ["48hour","in48hour"]: interval = Wakeup_Mode.in48hour
			elif interval in ["hourly","hour"]: interval = Wakeup_Mode.hour
			elif interval in ["daily","day"]: interval = Wakeup_Mode.day
			elif interval in ["weekly","week"]: interval = Wakeup_Mode.week
			elif interval in ["monthly","month"]: interval = Wakeup_Mode.month
			elif interval in ["yearly","year"]: interval = Wakeup_Mode.year
			else:
				raise ValueError ("No valid input parameters: interval = " + str(interval))
		
		# als we hier terecht zijn gekomen dan is interval van het type enum Wakeup_Mode	
		if interval in [Wakeup_Mode.in1hour,Wakeup_Mode.in2hour,Wakeup_Mode.in6hour,Wakeup_Mode.in12hour,Wakeup_Mode.in24hour,Wakeup_Mode.in48hour]:
			# bereken het eind timestamp van deze mode....based on start_ts (kan overruled zijn door bijv. last_resettimestamp)
			then = start_ts + interval.value
			# bereken hoe lang nog tot aan dit punt
			timerset = then - int(time.time())
			# controleer of dit punt al voorbij is.....neem anders het gewone interval
			return timerset if timerset > 0 else interval.value, interval.value
		elif interval in [Wakeup_Mode.hour, Wakeup_Mode.day, Wakeup_Mode.week, Wakeup_Mode.month, Wakeup_Mode.year]:
			# bereken het eind timestamp van deze mode....start_ts kan overruled zijn door een start_timestamp argument (bijv. last_resettimestamp)
			if interval.name == "hour":
				then = int(datetime.timestamp(datetime.now().replace(minute=0,second=0, microsecond=0) + relativedelta(hours=1)))
				return (then - int(time.time())), 60*60
			elif interval.name == "day":
				then = int(datetime.timestamp(datetime.now().replace(hour=0,minute=0,second=0) + relativedelta(days=1)))
				return (then - int(time.time())), 24*60*60
			elif interval.name == "week":
				weekday = datetime.now().weekday()
				weekday = weekday + 1 # correct weekday for sunday being the first day of the week rather than monday
				if weekday == 7: weekday = 0
				then = int(datetime.timestamp(datetime.now().replace(hour=0,minute=0,second=0) - relativedelta(days=weekday) + relativedelta(days=7)))
				return (then - int(time.time())), 7*24*60*60
			elif interval.name == "month":
				then = int(datetime.timestamp(datetime.now().replace(day=1,hour=0,minute=0,second=0) + relativedelta(months=1)))
				repeat = int(datetime.timestamp(datetime.now().replace(day=1,hour=0,minute=0,second=0) + relativedelta(months=2)))
				return (then - int(time.time())), repeat - then
			elif interval.name == "year":
				then = int(datetime.timestamp(datetime.now().replace(month=1,day=1,hour=0,minute=0,second=0) + relativedelta(years=1)))
				repeat = int(datetime.timestamp(datetime.now().replace(month=1,day=1,hour=0,minute=0,second=0) + relativedelta(years=2)))
				return (then - int(time.time())), repeat - then
		else:
			raise ValueError("No timerset can be calculated from interval = " + str(interval))
		# print ("Calculated timerset: " + str(timerset))
		return timerset, repeatset
	except ValueError as err:
		Logger.error(str(err))
	except Exception as err:
		Logger.exception(str(err))
		
		
		
def Calculate_Period(data_selection=None, re_timestamp=None):
	'''
	This routine returns the START and END timestamps for the data_selection period selected 
	referenced from the re_timestamp provided or NOW if nothing is provided
	It return None, None if no timestamps can be calculated
	'''
	try:
		if data_selection is None: raise ValueError
		ts_now = time.time() if re_timestamp is None else int(re_timestamp)
		dt_now = datetime.fromtimestamp(ts_now)
		
		if data_selection in [DataSelection.All, DataSelection._Last50]:
			# no timestamps here
			return None,None
		elif data_selection in [DataSelection._48hr,DataSelection._24hr,DataSelection._12hr,
								DataSelection._6hr,DataSelection._2hr,DataSelection.Hour,
								DataSelection._10min, DataSelection._30min, DataSelection._1hr]:
			start_ts = ts_now - data_selection.value
			end_ts = ts_now
		elif data_selection == DataSelection.Day: 
			start_ts = int(datetime.timestamp(dt_now.replace(hour=0,minute=0,second=0)))
			end_ts = int(datetime.timestamp(dt_now.replace(hour=0,minute=0,second=0) + relativedelta(days=1))) - 1
		elif data_selection == DataSelection.Week:
			weekday = dt_now.weekday()
			weekday = weekday + 1 # correct weekday for sunday being the first day of the week rather than monday
			if weekday == 7: weekday = 0
			sunday_thisweek = dt_now.replace(hour=0,minute=0,second=0) - relativedelta(days=weekday)
			sunday_nextweek = sunday_thisweek + relativedelta(days=7)
			start_ts = int(datetime.timestamp(sunday_thisweek))
			end_ts = int(datetime.timestamp(sunday_nextweek)) - 1
		elif data_selection == DataSelection.Month: 
			start_ts = int(datetime.timestamp(dt_now.replace(day=1,hour=0,minute=0,second=0)))
			end_ts = int(datetime.timestamp(dt_now.replace(day=1,hour=0,minute=0,second=0) + relativedelta(months=1))) - 1
		elif data_selection == DataSelection.Year: 
			start_ts = int(datetime.timestamp(dt_now.replace(month=1,day=1,hour=0,minute=0,second=0)))
			end_ts = int(datetime.timestamp(dt_now.replace(month=1,day=1,hour=0,minute=0,second=0) + relativedelta(years=1))) - 1
		
		return start_ts, end_ts
	except Exception as err:
		Logger.exception(str(err))

def thisday_timestamp(now=datetime.now(), at_noon=False):
	'''
	Returns the timestamp of the start of this day.... or noon...
	'''
	if not at_noon: 
		return int(datetime.timestamp(now.replace(hour=0, minute=0, second=0, microsecond=0)))
	else:
		return int(datetime.timestamp(now.replace(hour=12, minute=0, second=0, microsecond=0)))
		
def thishour_timestamp(now=datetime.now(), at_half=False):
	'''
	Returns the timestamp of the start of this hour.... or halfhour...
	'''
	if not at_half:
		return int(datetime.timestamp(now.replace(minute=0, second=0, microsecond=0)))
	else:
		return int(datetime.timestamp(now.replace(minute=30, second=0, microsecond=0)))
	
def this10min_timestamp(now=datetime.now()):
	'''
	Returns the timestamp of the previous 10 minute mark...
	'''
	mark_10min = datetime(now.year, now.month, now.day, now.hour, (now.minute // 10) * 10)
	return int(datetime.timestamp(mark_10min.replace(second=0, microsecond=0)))

def cursor_to_dict(data=None, output=Dictionary.of_lists):
	'''
	Returns a dictionary with the columnnames as keys and de row values as listitems....
	Takes as input a Cursor object resulting from a conn.execute() command to sqlite
	'''
	result = dict()
	col_names = list()
	values = list()
	for col_info in data.description:
		col_names.append(col_info[0])
		# voor iedere column maken we een (nu nog lege) value list
		values.append([])
	# rows = data.fetchall()
	for row in data:
		# iedere row is een tuple met waarden met net zoveel elementen als er columns zijn
		teller=0
		for col in row:
			values[teller].append(row[teller])
			teller +=1
			
			
	if  len(values[0])==0 and (output==Dictionary.of_values or output==Dictionary.autoselect):
		# If NO row returned, then return a dictionary of None's'
		values = [None for x in values]
		result = dict(zip(col_names, values))
	elif len(values[0])==1 and (output==Dictionary.of_values or output==Dictionary.autoselect):
		# If Only one row returned, then return a dictionary of values
		values = [x[0] for x in values]
		result = dict(zip(col_names, values))
	else:
		# return a dictionary of valuelists....
		result = dict(zip(col_names, values))
	return result
	
def get_begin_of_week(check_day=datetime.now(), sunday_as_start=True):
	from datetime import timedelta
	'''
	Returns the start of the week for the given checkday
	'''
	week_day = check_day.weekday()
	if sunday_as_start:
		week_day += 1
		if week_day == 7: week_day=0
	start = check_day - timedelta(days=week_day)
	return start.replace(hour=0, minute=0, second=0, microsecond=0)

	
def get_days_in_month(selecteddate=datetime.now()):
	'''
	Returns the number of days in the month of the selecteddate.
	'''
	first_day_this_month = selecteddate.replace(day=1,hour=0,minute=0,second=0)
	first_day_next_month = selecteddate.replace(day=1,hour=0,minute=0,second=0) + relativedelta(months=1)
	days_in_month = (first_day_next_month - first_day_this_month).days
	# print("Days in this month: %s" % days_in_month)
	return int(days_in_month)

def get_input(prompt="", default=None):
	'''
	prompts the user for input and returns the input in the type specified by the default argument
	'''
	if default is not None: 
		default_str = str(default)
		try:
			inp = input(prompt + "(default: " + default_str + ") :")
			if inp=="": 
				return default
			else: 
				if type(default) in [int,float]:
					return type(default)(float(inp))
				elif type(default) in [bool]:
					if inp.upper() in ['ON', '1','TRUE','AAN','YES']:
						return True
					elif inp.upper() in ['OFF', '0','FALSE','UIT','NO']:
						return False
				else:
					return str(inp)
		except Exception as err:
			Logger.exception(str(err))
			return default
	else:
		return input(prompt + ' :')

def update_progressbar(max_num=100, act_num=100, max_bars=100):
	'''
	Print and updates a progressbar in terminal mode
	'''
	print("\r", end="")
	print("{:.1%} ".format(act_num/max_num),"-"*int(act_num/max_num)*max_bars, end="")

def set_mouse(*args, **kwargs):
	print("args: ", args)
	print("kwargs: ", kwargs)
	widget = args[0]
	event = kwargs.get("event", None)
	if event is None:
		print ("No event passed...")
		return
	if event == "onmouseover":
		widget.onmouseover.connect(None, None)
		widget.style["cursor"] = "grab"
	elif event == "onmousedown":
		widget.style["cursor"] = "grabbing"
	elif event == "onmouseup":
		widget.style["cursor"] = "grab"
	elif event == "onmouseleave":
		widget.onmouseover.connect(set_mouse, event="onmouseover")
		widget.style["cursor"] = "default"


def set_css_sizes(widget=None, *args, **kwargs):
	'''
	This routine reads the kwargs on css settings for a widget object
	and fills those css settings in the passed widget
	'''
	if widget is None: return
	
	if any(x in kwargs for x in ['top', 'bottom', 'left', 'right']): default_position = 'absolute'
	else: default_position = 'relative'
	widget.css_position = kwargs.get('position',default_position)

	# get font, top, left, width and height
	fontsize = str(kwargs.get("fontsize",""))
	top = str(kwargs.get("top",""))
	left = str(kwargs.get("left",""))
	width = str(kwargs.get("width",""))
	height = str(kwargs.get("height",""))
	
	if fontsize.isnumeric(): fontsize += "px"
	if top.isnumeric(): top += "px"
	if left.isnumeric(): left += "px"
	if width.isnumeric(): width += "px"
	if height.isnumeric(): height += "px"
	
	if fontsize: widget.css_font_size = fontsize
	if top: widget.css_top = top
	if left: widget.css_left = left
	widget.css_width = width if width else "100%"
	widget.css_height = height if height else "100%"
	
	kwargs["css_font_size"] = widget.css_font_size
	# kwargs["css_top"] = widget.css_top
	# kwargs["css_left"] = widget.css_left
	# kwargs["css_width"] = widget.css_width
	# kwargs["css_height"] = widget.css_height
	
	kwargs.pop("fontsize", None)
	# kwargs.pop("top", None)
	# kwargs.pop("left", None)
	# kwargs.pop("width", None)
	# kwargs.pop("height", None)
	
	return kwargs
	

def set_widget_colors(widget=None, dp=None):
	from Common_Data import CATEGORY_ID
	
	# Set the colors a widget based on its datapoint binding
	if widget is None or dp is None: return
	if Is_NOE(dp.categoryID): return

	# print ("cat ID is " + str(self.categoryID))
	cat = CATEGORY_ID[dp.categoryID]
	if not dp.enabled:
		widget.css_background_color = cat.disabled_BG_Color
		widget.css_color = cat.disabled_FG_Color
	else:
		widget.css_background_color = cat.BG_Color
		widget.css_color = cat.FG_Color
		

def spinning_cursor():
	while True:
		for cursor in '|/-\\':
			yield cursor

def spincursor(duration=1.0):
	'''
	Spins the cursor for duration seconds
	'''
	spinner = spinning_cursor()
	for _ in range(int(10*duration)):
		sys.stdout.write(next(spinner))
		sys.stdout.flush()
		time.sleep(0.1)
		sys.stdout.write('\b')



from Config import IMAGES_LOCATION
import base64

def Load_Images(image_name):
	'''
	Laad en returned een image file als een bytearray
	'''
	try:
		with open(Path(IMAGES_LOCATION, image_name).with_suffix(".gif"), "rb") as imageFile:
			imagestring = base64.b64encode(imageFile.read()) 
			return "data:image/gif;base64," + imagestring.decode()
	except FileNotFoundError:
		try:
			with open(Path(IMAGES_LOCATION, image_name).with_suffix(".png"), "rb") as imageFile:
				imagestring = base64.b64encode(imageFile.read())
				# print ('File read successfully')
				return "data:image/png;base64," + imagestring.decode()
		except FileNotFoundError:
			Logger.error(f"File not found: {Path(IMAGES_LOCATION, image_name)}.png or .gif")
			return None
	except Exception as err:
		Logger.error(str(err))
		return None

epex_data = 214	# Datapoint ID of the Epex data
epex_pred = 334

def get_all_epexinfo(start_dt=datetime.now(), plan_hours=None):
	from DB_Routines import get_df_from_database
	'''
	Deze routine returned een dataframe met epex_info die bestaat uit epex_data (voorzover beschikbaar)
	aangevuld met epex_pred (indien en voorzover beschikbaar). Alleen aaneensluitende uren worden meegenomen
	De serie wordt dus afgebroken als er uren beginnen te ontbreken
	indien er een plan_hours is opgegeven wordt tot maximaal dat aantal uren vanaf de start_dt meegenomen
	'''
	# dit uur kunnen we beginnen
	selected_startdate = start_dt.replace(minute=0, second=0, microsecond=0)
	start_ts = int(selected_startdate.timestamp())
	selected_enddate = None
	if plan_hours:
		end_ts = start_ts + (3600 * plan_hours)			# op deze manier bepalen van end_ts heeft geen last van zomer/wintertijd overgangen 
		selected_enddate = datetime.fromtimestamp(end_ts)

	# now get all the epex_data starting from start_dt hour
	epex_data_df = get_df_from_database(dpIDs=[epex_data], selected_startdate=selected_startdate, selected_enddate=selected_enddate, 
												add_datetime_column=True)
	# then get the predictions (if any)
	epex_pred_df = get_df_from_database(dpIDs=[epex_pred], selected_startdate=selected_startdate, selected_enddate=selected_enddate)
	
	# met een outer join/merge worden de rijen allemaal gecombineerd van beide dataframes, NaN voor missende values
	epex_df = epex_data_df.merge(epex_pred_df[['timestamp','epex_pred']], how='outer', on="timestamp")
	
	# maak nu een nieuwe kolom met de combi van epex_data en epex_pred waarbij epex_data voorgaat (als we die hebben)
	epex_df['epex_info'] = epex_df['epex_data'].fillna(epex_df['epex_pred'])
	
	# check of er NaN (ontbrekende epex data en of epex_pred) is gevonden in de epex_info, nan_idx is een arrays met de indexen van de NaN entries
	nan_idx = np.nonzero(np.array(epex_df['epex_info'].isnull()))[0]
	if nan_idx.size > 0: 
		# er zijn blijkbaar NaN entries gevonden....bepaal de index van de eerste NaN
		firstnan_idx = nan_idx[0]
		if firstnan_idx < (len(epex_df) -1):
			# purge the rest of the epex_data, we cant use them... they contain NaN's
			epex_df = epex_df[:firstnan_idx]
			last_valid_ts = epex_df['timestamp'].values[-1]
			Logger.info('Plan horizon is gewijzigd naar %s ivm te weinig epex data en/of epex_predictie data' % datetime.fromtimestamp(last_valid_ts))
	
	return epex_df[['timestamp','datetime','epex_info']]


def first_number(s):
	'''
	Returns the index of the first number in a string, including the sign + or -
	'''
	for i, c in enumerate(s):
		if c.isdigit() or c in ['-','+']:
			return i
	return -1


def main(args):
	print(get_all_epexinfo(plan_hours=36))
	

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
