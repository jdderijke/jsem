import threading
import time
import re
from collections import OrderedDict
from datetime import datetime
import remi.gui as gui
from remi.gui import *
import json

import DB_Routines
from Config import *
import Common_Data
# from LogRoutines import Logger
from Common_Enums import *
from Common_Routines import dump, IsNot_NOE, Is_NOE, Calculate_Timerset, Waitkey
from LogRoutines import Logger


# from inspect import stack
	
class Category(object):
	def __init__(*args, **kwargs):
		pass
	
class Pollmessage(object):
	def __init__(*args, **kwargs):
		pass
	
class Protocol(object):
	def __init__(*args, **kwargs):
		pass
	



	
	
class Datapoint(object):
	def __get_enabled(self):
		# print ("__get_enabled called")
		return self._enabled
	def __set_enabled(self,nwvalue):
		# print ("__set_enabled called")
		if nwvalue != self._enabled:
			self._enabled = nwvalue
			# self.__set_widget_colors()
	enabled = property(__get_enabled,__set_enabled)
	
	# def __get_GUI_widget(self):
		# # print ("__get_GUI_widget called")
		# return self._GUI_widget
	# def __set_GUI_widget(self,nwvalue):
		# # print ("__set_GUI_widget called, current GUI_widget list = %s" % self.GUI_widget)
		# if nwvalue != self._GUI_widget:
			# self._GUI_widget = nwvalue
			# self.update_GUI()
	# GUI_widget = property(__get_GUI_widget,__set_GUI_widget)
	
	def __get_category(self):
		# print ("__get_category called")
		return self._category
	def __set_category(self,nwvalue):
		# print ("__set_category called")
		if nwvalue != self._category:
			self._category = nwvalue
			# self.__set_widget_colors()
	category = property(__get_category,__set_category)

	# def __set_widget_colors(self):
		# # Set the colors for all connected GUI widgets
		# if self._GUI_widget is None or self._GUI_widget == []: return
		
		# CATEGORY_ID = Common_Data.CATEGORY_ID
		# # print ("cat ID is " + str(self.categoryID))
		# cat = CATEGORY_ID[self.categoryID]
		# # print (cat.name)
		# # print ("__set_widget_colors called for dp %s " % self.name)
		# if not self._enabled:
			# self.GUI_BG_color = cat.disabled_BG_Color
			# self.GUI_FG_color = cat.disabled_FG_Color
		# else:
			# self.GUI_BG_color = cat.BG_Color
			# self.GUI_FG_color = cat.FG_Color
			
		# for widg in self._GUI_widget:
			# widg.css_background_color = self.GUI_BG_color
			# widg.css_color = self.GUI_FG_color

	# def __get_SIG_widget(self):
		# # print ("__get_SIG_widget called")
		# return self._SIG_widget
	# def __set_SIG_widget(self,nwvalue):
		# # print ("__set_SIG_widget called")
		# if nwvalue is not self._SIG_widget:
			# self._SIG_widget = nwvalue
			# self.__set_signal_colors()
	# SIG_widget = property(__get_SIG_widget,__set_SIG_widget)

	# def __get_signal(self):
		# # print ("__get_signal called")
		# return self._signal
	# def __set_signal(self,nwvalue):
		# # print ("__set_signal called for ", self.name)
		# if nwvalue != self._signal:
			# self._signal = nwvalue
			# self.__set_signal_colors()
	# signal = property(__get_signal,__set_signal)
	
	# def __get_warning(self):
		# # print ("__get_warning called")
		# return self._warning
	# def __set_warning(self,nwvalue):
		# # print ("__set_warning called for ", self.name)
		# if nwvalue != self._warning:
			# self._warning = nwvalue
			# self.__set_signal_colors()
	# warning = property(__get_warning,__set_warning)

	# def __get_alarm(self):
		# # print ("__get_alarm called for ", self.name)
		# return self._alarm
	# def __set_alarm(self,nwvalue):
		# # print ("__set_alarm called")
		# if nwvalue != self._alarm:
			# self._alarm = nwvalue
			# self.__set_signal_colors()
	# alarm = property(__get_alarm,__set_alarm)

	# def __set_signal_colors(self):
		# if self.SIG_widget is None: return
		
		# if self.alarm: 
			# bgcolor = Alarm_bg_color
			# color = Alarm_fg_color
		# elif self.warning:
			# bgcolor = Warning_bg_color
			# color = Warning_fg_color
		# elif self.signal:
			# bgcolor = Signal_bg_color
			# color = Signal_fg_color
		# else:
			# # GEEN SIGNAAL -->als de GUI en SIG dezelfde widget zijn, dan de GUI kleuren aanhouden
			# if self.GUI_widget is not None and self.SIG_widget in self.GUI_widget:
				# bgcolor = self.GUI_widget[0].bg_color
				# color = self.GUI_widget[0].fg_color
			# else:
				# bgcolor = NoSignal_bg_color
				# color = NoSignal_fg_color
				
		# # Now set the widget signal color on the screen
		# self.SIG_widget.css_background_color = bgcolor
		# self.SIG_widget.css_color = color



	
	def __get_value(self):
		# return the current value
		return self._value
		
	def __set_value(self,nwvalue):
		if nwvalue is None:
			return
		else:
			try:
				nwvalue = self.datatype(nwvalue)
			except Exception as err:
				Logger.error(self.name + '-- ' + str(err))
				return
			self.process_nwvalue(nwvalue)
			
	value = property(__get_value,__set_value)
	
	def process_nwvalue(self, nwvalue=None, nwtimestamp=time.time()):
		try:
			# None wordt niet geaccepteerd als tmpvalue, als je dit wil zet dan de hidden property _value op None
			# if nwvalue is None: return
			
			# of er nu iets veranderd is of niet.... sla deze waarde op als de nieuwe waarde en bewaar de oude waarde
			# sla waarden en timestamps met volledige accuracy op, dit is nodig voor het correct uitvoeren van integraal berekeningen
			# store de oude waarde, en noteer de timestamp, een timestamp is in SECONDEN...met seconden fracties achter de decimale punt
			self._oldvalue = self._value
			self._oldvalue_timestamp = self._value_timestamp
			self._value = nwvalue
			self._value_timestamp = nwtimestamp
			
			self.last50_values.append(self._value)
			self.last50_timestamps.append(self._value_timestamp)
			# 1 erbij, houd de 50 laatste entries
			self.last50_values = self.last50_values[-50:]
			self.last50_timestamps = self.last50_timestamps[-50:]
			
			if self.dbstore: self.db_store()
			# Trigger dependants en widgets alleen als dat zinvol is
			# if self._value != self._oldvalue:
			self.update_dependants()
			self.update_widgets()

		except Exception as err:
			Logger.error('%s - An error occurred' % self.name)
			Logger.exception(str(err))

	def update_widgets(self):
		'''
			This routine updates all widgets that are subscribed to this datapoint.
			Widgets that a not active are first removed from the subscriptionlist.
			A better way would be to clean up widgets when they are no longer visible... however
			REMI does not do that, widgets remain in exisitence even if they are not displayed anymore...
		'''
		from Common_Routines import is_child_of
		try:
			# if self.ID == 214: Logger.info(f'{self.name}-- datapoints update_widgets routine entered, len(self.subscribed_widgets)={len(self.subscribed_widgets)}')
				
			index=0
			# Logger.info(f'{self.name}-- updating widgets, number of subscribed widgets = {len(self.subscribed_widgets)}')
			while index < len(self.subscribed_widgets):
				widget = self.subscribed_widgets[index]
				if widget is None:
					del self.subscribed_widgets[index]
					Logger.error('%s -- Found a widget with value None in the subscribed_widgets list, deleted it!' % self.name)
					continue
				else:
					# Logger.info(f'{self.name}-- checking if subscribed widget..{widget} is child of DATA_PARENT_CONTAINER')
					if is_child_of(widget, Common_Data.DATA_PARENT_CONTAINER):
						# Logger.info(f'{self.name}-- YES IT IS')
						widget.refresh(dp=self)
						index +=1
						continue
						
					# Logger.info(f'{self.name}-- checking if subscribed widget..{widget} is child of CHARTS_PARENT_CONTAINER')
					if is_child_of(widget, Common_Data.CHARTS_PARENT_CONTAINER):
						# Logger.info(f'{self.name}-- YES IT IS')
						widget.refresh(dp=self)
						index +=1
						continue
					# Logger.info(f'{self.name}-- WIDGET IS INACTIVE....deleting from subscribed widget list')
					del self.subscribed_widgets[index]
		except Exception as err:
			Logger.exception(str(err))
			

	def rebuild_dependencies(self):
		'''
		Rebuild the dependants dictionary based on all datapoints currently loaded in DATAPOINTS_NAME and DATAPOINTS_ID dictionaries
		'''
		self.dependants=[]
		# print ("Checking for dependants of datapoint " + self.name)
		# we kijken voor ieder datapoint of zijn naam gebruikt wordt in de calc_rule van een ander datapoint.
		# maar dan alleen daar waar de # loader NIET voorkomt, want Calc_Rules met ergens een # zijn bedoeld om alleen door zn eigen
		# datapoint getriggerd te worden!!!
		for that_dp in Common_Data.DATAPOINTS_NAME.values():
			that_dpname = that_dp.name
			if (
					IsNot_NOE(that_dp.calc_rule) and
					"|" + self.name.lower() + "|" in that_dp.calc_rule.lower() and
					"#" not in that_dp.calc_rule
				):
				# als dat inderdaad het geval is voegen we dat andere datapoint toe als dependant van dit datapoint
				self.dependants.append(that_dp)
				# zodat hij door dit datapoint wakker geschopt kan worden wanneer deze value gewijzigd wordt.
				# print ("In this datapoint " + self.name + " the datapoint " + that_dpname + " was added as a dependant. because " + self.name + " showed up in the calc_rule of " + that_dpname)


	def update_dependants(self):
		'''
		Update all dependant datapoint by triggering their _Calc_Rules
		'''
		# voor ieder datapoint wat afhankelijk is van dit datapoint
		# dit triggert de __calc routines van al die afhankelijke datapoints en update ze...
		for dp in self.dependants: 
			if dp.enabled: dp.write_RECALC_value(None)

	def initialize_datapoint(self):
		'''
		last_values and last_timestamps arguments can be passed to allow for one central query to get all last values of all datapoints in 1 go.
		
		Further See the document: Functional specs PRESET and DB store and retrieve routines for datapoints.docx
		'''
		self.db_restore_last_value(use_values_table_if_needed=True)
		
		self.rebuild_dependencies()
		
		# Check if any presets are needed...first as a result of a startup indicator in the reset_interval
		if IsNot_NOE(self.reset_interval) and self.reset_interval.lower().strip() == 'startup': 
			self.do_preset()
			# make sure the startup preset only runs once!
			self.reset_interval=None
		# If a datapoint still does not have a value after the db_restore_last_value routine and the startup indicator... then load the initial value
		if Is_NOE(self.value): 
			self.do_preset()
		# If there still is a reset_interval ('startup' is removed by now) then we need to start the presettimer for the first time....
		if IsNot_NOE(self.reset_interval): self.presettimer_start()

		
		if self.dbstore and IsNot_NOE(self.store_interval):
			# this dp needs a dbstore_timer started
			self.db_store_start()
			
		
		if IsNot_NOE(self.interfaceID):
			# Check of the interface for this datapoint has been loaded
			if self.interfaceID in Common_Data.INTERFACE_ID:
				interf = Common_Data.INTERFACE_ID[self.interfaceID]
				interf.subscribe(self)
		
		self.initialize_chartdefinitions()
		
		
	def reload(self, *args, **kwargs):
		'''
		Reloads the properties from the database and re-initializes the datapoint, including rebuilding dependencies
		'''
		DB_Routines.load_datapoints(dps=[self])
		self.initialize_datapoint()
		Logger.info('%s-- datapoint reloaded from database' % self.name)


	def __init__(self, *args, **kwargs):
		### property initializations
		self._value = None
		self._value_timestamp = None
		self._oldvalue = None
		self._oldvalue_timestamp = None
		# self._value_lastreset_timestamp = None
		self._enabled = None
		self._GUI_widget = []
		self._SIG_widget = None
		self._category = None
		self._signal = False
		self._warning = False
		self._alarm = False



		# self._store_timestamp = 0.0

		self.presettimer = None
		self._presettimer_running = False
		
		self.dbstore_timer = None
		self._dbstore_timer_running = False
		
		# Generic attributes: Alleen de attributes met een specifiek datatype die niet direkt uit de db te herleiden is
		# worden hier geinitialiseerd, vaak zijn deze in de db als een ander datatype opgeslagen (Bool als integer 0 of 1 en Type als textstring)
		self.enabled = False
		self.dbstore = False
		self.datatype = str
		
		# En dan nog de attributes die niet uit de db geladen kunnen worden,
		# datapoints_dict point naar de dict waar alle datapoints inhangen (op naam key)
		# self.datapoints_dict = None
		
		# dependants is een lijst met andere (afgeleide)datapoints die voor hun waarde afhankelijk zijn van dit datapoint (bijv via een calculatie)
		self.dependants = list()
		# interface points naar de interface waaraan dit datapoint gekoppeld is, als die tenminste draait..
		self.interface = None
		# last50 is de lijst met de 50 laatste waarden met timestamps tijdens deze run (dus geen DB waarden, maar life waarden)
		# de laatste waarde (current value) staat als laatste
		self.last50_values = []
		self.last50_timestamps = []
		
		# een dictionary met widgets waarin dit datapoint voorkomt, bijvoorbeels als graph of chart
		# deze widghets MOETEN een refresh() method hebben die wordt aangeroepen wanneer de value van het datapoint verandert.
		self.subscribed_widgets = list()

		self.chartsinfo=[]

	def initialize_chartdefinitions(self):

		'''
		the chart_type property of the datapoint contains info on the chart definitions
		default is just the word "line" or "bar" or "map".  And this routine will then fill the rest of the chart_info object
		But if the chart_type property startswith a "{" character then the whole chart_type property will be read as a JSON file 
		and fill the chart_info property accordingly
	
		Some typical JSON lines for the chart_type field:
		{"chartsinfo": [{"ctype": "line", "title": "Bron Temperaturen", "joinwith":["BronAanvoerTemp", "Delta_T_Bron"]}]}
		{"chartsinfo": [{"ctype": "line", "title": "Eerste Chart"},{"ctype": "bar", "title": "Tweede Chart"}]}
		{"chartsinfo": [{"ctype": "map", "title": "MAP Chart", "joinwith":"pool_flush", "x_col_labels": ["1","2"]},{"ctype": "bar", "title": "Tweede Chart"}]}
		{"chartsinfo": [{"ctype": "pipo", "title": "Eerste Chart"},{"ctype": "bar", "title": "Tweede Chart"}]}
		'''
		if Is_NOE(self.chart_type):
			self.chartsinfo = [] 
			return
		
		chart_type = self.chart_type.strip()
		if not chart_type.startswith("{"):
			if chart_type.lower() in Chart_Definitions:
				self.chartsinfo = [Chart_Definitions[chart_type.lower()].copy()]
				return
			else:
				Logger.error("%s--Illegal chart_type: %s" % (self.name, chart_type))
				self.chartsinfo = [] 
				return
		else:
			# JSON format, read the LSON string
			definitions = json.loads(chart_type)["chartsinfo"]
			# definitions now contains a list of chart definitions
			for chartdef in definitions:
				ctype = chartdef["ctype"]
				if ctype not in Chart_Definitions:
					Logger.error ("%s--Illegal chart_type found in JSON string:  %s" % (self.name, ctype))
					self.chartsinfo = [] 
					return
				else:
					for prop in Chart_Definitions[ctype].keys():
						# now look at any property that was NOT filled by the JSON line and fill that property
						# from the default definition of that type of chart/map
						chartdef[prop] = chartdef.get(prop, Chart_Definitions[ctype][prop])
			self.chartsinfo = definitions
			return


	def write_value(self, nwvalue=None):
		'''
		Deze routine schrijft de nwvalue naar de interface van het datapoint (als die bestaat).
		In dat geval update hij de value van het datapoint niet, dat gebeurt wel via de interface wanneer de wijziging geaccepteerd is
		
		Als er geen interface bestaat, dan wordt wel de datapoint value geschreven, zonder enige aanpassing
		'''
		try:
			# Check datatype van de nwvalue
			try:
				nwvalue = self.datatype(nwvalue)
			except Exception as err:
				Logger.error(self.name + str(err))
				return

			if self.interface is not None:
				# als er een interfaceis voor dit datapoint... dan zenden we de input naar die interface
				self.interface.make_command_telgr(self, nwvalue)
			else:
				# geen interface? dan gewoon de value zetten.. verder niets
				self.value = nwvalue
		except Exception as err:
			Logger.error('%s-- Error writing nwvalue %s...' % (self.name, nwvalue))
			Logger.exception(str(err))



	def write_GUI_value(self, *args, **kwargs):
		'''
		Deze routine is alleen voor input die via de GUI binnenkomt (user input).
		write_GUI_value kan op 2 manieren aangeroepen worden: als handler voor een textinputbox of CheckBox (REMI), in dit geval wordt de calling widget
		en de nieuwe waarde in het textveld meegegeven in args[0] en args[1]. De andere manier is met een keyword argument (input_value) met de nieuwe waarde

		Hij leest de input en checkt of er een GUI calc_rule bestaat voor dit dp, zo ja dan voert hij die uit.
		Als er een interface gedefinieerd is voor deze dp, dan stuurt hij de input naar die interface en doet verder NIETS (dus ook geen GUI calc_rule)

		'''
		import json
		try:
			# print ("write_value called for dp %s" % self.name)
			# Deconstruct the arguments
			if len(args) >= 2 and type(args[0]) in [TextInput, CheckBox]: 
				calling_widget = args[0]
				if type(calling_widget) is TextInput:
					input_value = args[1]
					# reset the text to empty field
					calling_widget.text=""
				if type(calling_widget) is CheckBox:
					input_value = int(calling_widget.get_value())
			else:
				input_value = kwargs.get("input_value", None)
			if input_value is None: 
				Logger.error("Routine called without valid arguments")
				return
			
			# Pas op! input_value is een STRING en moet meestal nog geconverteerd worden!
			try:
				nwvalue = self.datatype(input_value)
			except Exception as err:
				Logger.error(self.name + str(err))
				return
			
			GUI_rule = None
			if IsNot_NOE(self.calc_rule):
				GUI_rule = json.loads(self.calc_rule.strip().replace("'",'"')).get('GUI', None)
				
			
			# I have to write the newvalue first, because a calc_rule may need that raw (unchanged) nwvalue for its calculations
			self.write_value(nwvalue)
			if GUI_rule:
				# er is een calcrule gevonden voor input via de GUI
				nwvalue, timestamp = self.exec_calc_rule(nwvalue, GUI_rule)
				self.process_nwvalue(nwvalue, timestamp)
				
		except Exception as err:
			if IsNot_NOE(self.calc_rule): Logger.error('Error during execution of GUI rule: %s' % self.calc_rule)
			Logger.exception(str(err))

	def write_RECALC_value(self, nwvalue):
		'''
		Deze routine is alleen voor het geforceerd uitvoeren van een INTERN calc_rule.
		Hij runt de RECALC calc_rule, als die er is, en stored het resultaat in de value/timestamp.
		Als dit leidt tot een WIJZIGING van de value returned hij True, anders False
		'''
		import json
		result = False
		try:
			RECALC_rule = None
			if IsNot_NOE(self.calc_rule):
				RECALC_rule = json.loads(self.calc_rule.strip().replace("'",'"')).get('RECALC', None)
				
			if RECALC_rule:
				# er is een calcrule ghevonden voor input via de GUI
				recalc_value, timestamp = self.exec_calc_rule(nwvalue, RECALC_rule)
				
				# if self.ID == 214:
					# Logger.info(f'{self.name}-- value = {self.value}, calcrule = {RECALC_rule}, nwvalue = {recalc_value}, timestamp = {timestamp}')

				# Handle deze nieuwe waarde af
				self.process_nwvalue(recalc_value, timestamp)
				result=True
			else:
				# geen RECALC_rule, niets doen
				pass
				
		except Exception as err:
			if IsNot_NOE(self.calc_rule): Logger.error('Error during execution of RECALC rule: %s' % self.calc_rule)
			Logger.exception(str(err))
		finally:
			return result


	def write_INTFC_value(self, nwvalue=None):
		'''
		Deze routine is alleen voor input die via een INTERFACE binnenkomt.
		Hij checkt of er een INTFC calc_rule bestaat voor dit dp, zo ja dan voert hij die uit.
		'''
		import json
		try:
			# Het datatype wordt in de decoder van de interface al gecheckt
			INTFC_rule = None
			if IsNot_NOE(self.calc_rule):
				INTFC_rule = json.loads(self.calc_rule.strip().replace("'",'"')).get('INTFC', None)
				
			if INTFC_rule:
				# er is een calcrule ghevonden voor input via de GUI
				nwvalue, timestamp = self.exec_calc_rule(nwvalue, INTFC_rule)
				self.process_nwvalue(nwvalue, timestamp)
			else:
				# geen INTFC_rule
				self.process_nwvalue(nwvalue, time.time())
				
				
		except Exception as err:
			if IsNot_NOE(self.calc_rule): Logger.error('Error during execution of INTFC rule: %s' % self.calc_rule)
			Logger.exception(str(err))


	def exec_calc_rule(self, input_value=None, calc_rule=None):
		from Calculate_costs import calculate_hourly_cost, calculate_daily_cost, calculate_monthly_cost
		from Calcrule_routines import mode3_state_change, get_daily_use, get_daily_return, get_monthly_use, get_monthly_return
		from Calcrule_routines import get_daily_gas, get_monthly_gas
		from Common_Routines import thisday_timestamp, thishour_timestamp
		from DB_Routines import get_value_from_database
		from EV_Optimizer import make_ev_plan
		from Pool_Optimizer import make_timer_plan, make_pool_plan
		
		DATAPOINTS_NAME = Common_Data.DATAPOINTS_NAME
		DATAPOINTS_ID = Common_Data.DATAPOINTS_ID
		
		def integral(inputv):
			# calculate integral
			# Logger.info(self.name + " calc integraal, _value=" + str(self._value) + ", _timestamp=" + str(self._value_timestamp))
			if self._value == None or self._value_timestamp == None:
				# Er zit een integraal in de calc_rule maar die heeft blijkbaar nog nooit gedraaid.....
				# we initialiseren de value op 0 en vullen de timestamp in op NU.
				self._value_timestamp = time.time()
				self._value = 0.0
				
			# now that we know for sure there is a value and a timestamp...calculate the timeintegral value based on hours (3600 sec)
			delta_t = (time.time() - self._value_timestamp)/3600.0
			result = self._value + (delta_t * inputv)

			# if self.ID == 335:
				# Logger.info("integral: dp: %s, _value: %s, inputv: %s, delta_t: %s, integral adds %s, nw_value: %s" % 
									# (self.ID, self._value, inputv, delta_t, (delta_t * inputv), result))
			return result
			
		dpname = Common_Data.DATAPOINTS_NAME
		try:
			# if self.ID in [230]: print(input_value, self.value)

			# zonder calc_rule hoef ik niets, kan ik niets
			if Is_NOE(calc_rule): return input_value, time.time()
			if input_value is None and "#" in calc_rule: return None, None
			if "#" in calc_rule:
				# Now first replace all # sysmbols in the calcrule with input_value
				if type(input_value)==bool or type(input_value)==int: repl = str(int(input_value))
				elif type(input_value)==float: repl = str(float(input_value))
				elif type(input_value)==str: repl = input_value
				else: 
					Logger.error('%s--Input value has an unsupported type: %s' % (self.name, type(input_value)))
					return None, None
				work_rule = calc_rule.replace("#", repl)
			else:
				work_rule = calc_rule
				
			# if self.ID in [230]: print(work_rule)
			# if self.ID in [215, 230]: print('%s--Calc rule called with rule %s' % (self.name, work_rule))
			pattern = re.compile('\\|.+?\\|')
			for item in pattern.finditer(work_rule): 
				# item is a MatchObject, 
				# its methods .span() returns a tuple with start,end indexes and 
				# its method .string returns the string passed into the search
				# its method .group() returns the part of the string where the match was found..
				repl_string = item.group()
				dp_name = repl_string.replace("|","")
				dp = dpname[dp_name]
				# dp = self.datapoints_dict[dp_name]
				# Als één van de datapoints in de rule None is, dan kan de hele rule niet worden uitgevoerd....
				if dp.value == None: 
					# Logger.warning('%s Kan zijn Calc_rule niet uitvoeren want het gerefereerde datapunt %s is None!' % (self.name, dp_name))
					return None, None
				new_string = str(int(dp.value)) if dp.datatype == bool else str(dp.value)
				work_rule = work_rule.replace(repl_string, new_string)
				work_rule = work_rule.replace('\x00', '')
			# if self.ID in [335]: Logger.info("__calc ran for dp %s with work rule %s" % (self.ID, work_rule))
			eval_result = eval(work_rule)
			# if self.ID in [335]: Logger.info("__calc result for dp %s = %s" % (self.ID, eval_result))
			
			if type(eval_result)==tuple and len(eval_result)>=2:
				result=eval_result[0]
				if eval_result[1] is None:
					timestamp=int(time.time())
				else:
					timestamp=int(eval_result[1])
			elif eval_result is None:
				# calc routine kwam met niets terug, waarschijnlijk een actie routine, zonder output
				result = input_value
				timestamp=int(time.time())
			else:
				result=eval_result
				timestamp=int(time.time())
			return result,timestamp
		except Exception as err:
			Logger.exception(self.name + "--Calc problem: " + str(err))
			return None, None
		
		
		
	# def update_signals(self):
		# '''
		# This routine fills the SIGNAL, WARNING and ALARM properties based on the SIGNAL_rule of this datapoint
		# It checks input_value OR the current value property against the different signalling tresholds
		# Syntax van SIGNAL_rule: alarm>100&warning<50&signal=True&<>False
		# '''
		# try:
			# # zonder input_value kan ik niets, default neem ik de huidige value als die tenminste niet None is
			# if self.value is None: return False
			# # zonder sig_rule hoef ik niets
			# if Is_NOE(self.sig_rule): return False
			# # met een string kan ik niets in termen van signalling
			# if self.datatype == str: return False
			
			# comparitors = self.sig_rule.split("&")
			# # print (comparitors)
			# result = {"signal":False, "warning":False, "alarm":False}
			# valid_operators = ["=", "<>", "<=", "<", ">=", ">"]
			# for comparitor in comparitors:
				# comparitor = comparitor.upper()
				# if comparitor.startswith("ALARM"): mode="alarm"
				# elif comparitor.startswith("WARNING"):mode="warning"
				# elif comparitor.startswith("SIGNAL"):mode="signal"
				# elif comparitor.startswith(tuple(valid_operators)):mode="signal"
				# else:
					# Logger.error("Illegal compare argument in signal rule of datapoint " + self.name)
					# Logger.error ("Invalid sig_rule: " + str(sig_rule))
					# return False
				# comparitor=comparitor.lstrip("ALARM").lstrip("WARNING").lstrip("SIGNAL")
				# # print (self.name + " update_signals--------------comparitor string:" + str(comparitor))
				# if comparitor.startswith("="):
					# comparitor = comparitor.lstrip("=")
					# result[mode] = result[mode] or (self.value==bool(comparitor.upper()) if self.datatype==bool else round(self.value,3)==round(float(comparitor),3))
				# elif comparitor.startswith("<>"):
					# comparitor = comparitor.lstrip("<>")
					# # print (self.name + " update_signals, check for <>")
					# result[mode] = result[mode] or (self.value!=bool(comparitor.upper()) if self.datatype==bool else round(self.value,3)!=round(float(comparitor),3))
				# elif comparitor.startswith("<="):
					# comparitor = comparitor.lstrip("<=")
					# result[mode] = result[mode] or (False if self.datatype==bool else round(self.value,3)<=round(float(comparitor),3))
				# elif comparitor.startswith("<"):
					# comparitor = comparitor.lstrip("<")
					# # print (self.name + ".__checksignal: check if self.value=" + str(self.value) + " < " + str(float(comparitor)))
					# result[mode] = result[mode] or (False if self.datatype==bool else round(self.value,3)<round(float(comparitor),3))
				# elif comparitor.startswith(">="):
					# comparitor = comparitor.lstrip(">=")
					# # print (self.name + ".__checksignal: check if self.value=" + str(self.value) + " >= " + str(float(comparitor)))
					# result[mode] = result[mode] or (False if self.datatype==bool else round(self.value,3)>=round(float(comparitor),3))
				# elif comparitor.startswith(">"):
					# comparitor = comparitor.lstrip(">")
					# # print (self.name + ".__checksignal: check if self.value=" + str(self.value) + " > " + str(float(comparitor)))
					# result[mode] = result[mode] or (False if self.datatype==bool else round(self.value,3)>round(float(comparitor),3))
	
			# # print (self.name + ".__setsignal ran, result: " + str(result))
			# self.signal = result["signal"]
			# self.warning = result["warning"]
			# self.alarm = result["alarm"]
			# # print ("signal", "warning", "alarm", sep=" | ")
			# # print (str(self.signal), str(self.warning), str(self.alarm), sep=" | ")
			# return result
		# except Exception as err:
			# Logger.exception(str(err))
	
	
	def presettimer_start(self):
		# if self.ID==257: 
			# print ("presettimer_start called for dp:", self.name)
			# Waitkey()
		
		if self._presettimer_running: 
			self.presettimer_stop()

		if Is_NOE(self.reset_interval): 
			Logger.error('%s--presettimer_start called and there is no reset_interval!' % self.name)
			return
		
		# determine the reference timestamp for the timerset calculation
		start_timestamp = None if (Is_NOE(self.last_reset_timestamp) or int(self.last_reset_timestamp)==0) else int(self.last_reset_timestamp) 
		timerset,_ = Calculate_Timerset(start_timestamp=start_timestamp, interval=self.reset_interval)
		# There is a possibility that its too late already...
		# if self.ID==257: 
			# print ("timerset:", timerset)
			# Waitkey()
		
		if timerset <=0: 
			Logger.error('%s illegal timerset returned from Calculate_Timerset routine, preset timer STOPPED')
			return
			
		if str(self.reset_interval).isnumeric() and int(self.reset_interval) < 0:
			# remove the one-time intervals from the scenario after this
			self.reset_interval=None
			
		self.presettimer = threading.Timer(timerset, lambda:self.do_preset(callback=True))
		self.presettimer.start()
		self._presettimer_running = True
		
		
	def do_preset(self, callback=False):
		'''
		Deze routine kan op 2 manieren worden aangeroepen: direkt vanuit de initialize routine of als callback van de presettimer
		De do_preset routine kijkt of er een initial_value is of dat er een RECALC routine is die een preset value kan berekenen...
		'''
		reset_done = False
		# print(f'do_preset, callback = {callback}')

		if callback:
			self._presettimer_running = False
			self.presettimer = None
			
		# kunnen we wel iets doen? Is er wel een reset_interval of een initial_value?
		if not self.reset_interval and not self.initial_value: return
		
		if IsNot_NOE(self.initial_value):
			# hier de initial value worden gezet
			self.value = self.datatype(self.initial_value)
			Logger.debug(f'{self.name}--initial_value loaded')
			reset_done = True
		elif self.write_RECALC_value(None):
			# There is NO initial value, see if the Calc_Rule produces a (preset) value
			Logger.debug(f'{self.name}--Calc_Rule_value loaded')
			reset_done = True
		else:
			Logger.info(f'{self.name}--Preset failed, no inital value found and CALC routine did not produce a preset value....')
			
		if reset_done:
			# Log this (p)reset_action in the DB
			self.last_reset_timestamp = int(time.time())
			DB_Routines.store_field_in_database(table="Datapoints", 
												ID=self.ID, field="last_reset_timestamp", 
												value=self.last_reset_timestamp)
		# Restart the persettimer
		if callback: self.presettimer_start()
		
	
	def presettimer_stop(self):
		if self.presettimer is not None: 
			self.presettimer.cancel()
			# wait untill the timer thread has stopped
			self.presettimer.join()
			self.presettimer = None
		self._presettimer_running = False

		
	def db_store_start(self):
		if self._dbstore_timer_running: 
			self.db_store_stop()

		# To start a timer i need an interval...
		if Is_NOE(self.store_interval): 
			Logger.error('%s, db_store_start called and there is no store_interval' % self.name)
			return
		
		timerset,_ = Calculate_Timerset(interval=self.store_interval)
			
		self.dbstore_timer = threading.Timer(timerset, lambda:self.db_store(callback=True))
		self.dbstore_timer.start()
		self._dbstore_timer_running = True
		
		
	def db_store(self, callback=False):
		if not self.dbstore: return
		if self._value is None: return
		store_values = []
		# print(f'db_store, callback = {callback}')
		
		new_storevalue = round(self._value, self.decimals) if self.datatype == float else self._value
		
		if Is_NOE(self.store_interval) and not callback:
			# Only store if value has changed...
			if self._value != self._oldvalue:
				# Value changed
				if self._oldvalue is not None:
					# Binary achtige datapoints, vaak inputs en settings of status/mode/onoff signalen: 
					# we slaan op indien de waarde gewijzigd is....maar als dat het geval is dan slaan we eerst nog even de oude waarde op met de 
					# huidige timestamp minus (zeg) 1 sec om te voorkomen dat er bij chartpresentatie vreemd geinterpoleerd gaat worden.
					old_storevalue = round(self._oldvalue, self.decimals) if self.datatype == float else self._oldvalue
					store_values.append((self.ID, int(self._value_timestamp - 1), old_storevalue))
				store_values.append((self.ID, int(self._value_timestamp), new_storevalue))
				DB_Routines.store_value_in_database(store_values)
		
		elif callback:
			# Store after a certain interval, this interval has expired because we got here through a timer callback
			store_values.append((self.ID, int(self._value_timestamp), new_storevalue)) 
			DB_Routines.store_value_in_database(store_values)
			
		
		if callback: 
			self._dbstore_timer_running = False
			self.dbstore_timer = None
			self.db_store_start()

		
	def db_store_stop(self):
		if self.dbstore_timer is not None: 
			self.dbstore_timer.cancel()
			# wait untill the timer thread has stopped
			self.dbstore_timer.join()
		self._dbstore_timer_running = False
		self.dbstore_timer = None
		
	def db_store_last_value(self):
		'''
		Saves the last value of this datapoint with the datapoint info in the database, so not in the values table but in the datapoints table
		This value will be used at startup/restart to preset the value of the datapoint. This avoids long SQL queries on the values table at every
		startup/restart
		'''
		if self._value_timestamp is not None:
			DB_Routines.store_field_in_database("Datapoints", self.ID, "last_value", self._value)
			DB_Routines.store_field_in_database("Datapoints", self.ID, "last_timestamp", self._value_timestamp)
		
	def db_restore_last_value(self, use_values_table_if_needed=False):
		'''
		Restores the earlier stored last_value of this datapoint,...
		'''
		value = DB_Routines.get_field_from_database("Datapoints", self.ID, "last_value")
		timestamp = DB_Routines.get_field_from_database("Datapoints", self.ID, "last_timestamp")
		if timestamp is not None:
			self._value = self.datatype(value) if value!=None else None
			self._value_timestamp = int(timestamp)
		elif use_values_table_if_needed:
			# If this failed because nothing was stored there.... then try the long process of retrieving it from the Values table
			Logger.info('%s--Last value not found, trying Values table...' % self.name)
			last_value,last_timestamp = DB_Routines.load_lastvalues(dpIDs=[self.ID])
			if self.ID in last_value: 
				value = last_value[self.ID]
				timestamp = last_timestamp[self.ID]
				self._value = self.datatype(value) if value!=None else None
				self._value_timestamp = int(timestamp)
			else:
				Logger.warning('%s--Could not retrieve last value' % self.name)
		else:
			Logger.warning('%s--Could not retrieve last value' % self.name)
		
def main(args):
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
