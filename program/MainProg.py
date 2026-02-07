import pathlib
import sys
import __main__

# print(sys.path)
# sys.path.append('/home/jandirk/common_addons/common_addons')
# print(sys.path)
# input('any')

if __name__ == "__main__":
	__main__.logfilename = "JSEM.log"
	__main__.backupcount = 5


from LogRoutines import Logger

import JSEM_Rules


import GUI_routines
from GUI_routines import show_all

from TCP_Routines import TCPServer
from JSEM_Rules import JSEM_Rule
from interfaces import ESMR50Interface, MbusInterface, SdmModbusInterface, ShellyRelayInterface, ESMR50_via_TCP
import io
import time
from datetime import datetime
import threading
import random
import signal
import sys
import os

from Config import TCPPORT, TCPHOST, MAX_EXTERNAL_CONN
from Config import CWD, DBFILE, LOGFILELOCATION, Loglevel, ENVIRONMENT, DB_looptime, DB_alivetime, Reboot_time
import Common_Data
from Common_Data import DATAPOINTS_ID, DATAPOINTS_NAME, DB_STORE, JSEM_RULES
from JSEM_Commons import expandcollapse, Calculate_Timerset
from common_utils import get_extra_css, get_ip_address, Waitkey, get_seconds_untill
import remi.gui as gui
from remi.gui import *
from remi import start, App
from DB_Routines import load_and_configure_datapoints, load_all_categories, DBstore_engine
# from GUI_routines import show_all
from Common_Enums import *
from pathlib import Path


Exit_Handled = False
def Exit_Handler():
	global Exit_Handled
	if Exit_Handled: return
	Exit_Handled = True

	Logger.info("Stopping all JSEM rules and strategies")
	for rule in Common_Data.JSEM_RULES:
		rule.stop_rule()
		
	Logger.info("Stopping all Interfaces")
	for intf in Common_Data.INTERFACE_NAME.values():
		Logger.info("Stopping Interface " + intf.name)
		intf.disconnect()
		while intf.connstate != ConnState.DisConnected:
			time.sleep(0.01)
			
	if ENVIRONMENT == Environment.Productie:
		Logger.info("Storing last values of all datapoints")
		for dp in DATAPOINTS_NAME.values():
			if dp.enabled: dp.db_store_last_value()

	if Common_Data.MAIN_INSTANCE:
		Logger.info ("Stopping Remi")
		Common_Data.MAIN_INSTANCE.close()
		Common_Data.MAIN_INSTANCE = None
		# print(Common_Data.MAIN_INSTANCE)
		# waitkey()
		# Common_Data.REMI_SHOULD_RUN=False
		# # Give Remi some time to stop
		# time.sleep(0.5)
	
	# Stopping resettimers, en db_store timers
	Logger.info("Stopping datapoint (p)reset- en db_store timers ")
	for dp in DATAPOINTS_NAME.values():
		dp.presettimer_stop()
		dp.db_store_stop()
	
	# stop the DB engine
	if Common_Data.DB_STORE is not None:
		Common_Data.DB_STORE.stop()
	
	Logger.info("Shutdown Logging")
	logging.shutdown()
	# Waitkey()

	
		
# def signal_handler_exit(signal, frame):
# 	Exit_Handler()
# 	print ("Now exitting application......")
# 	sys.exit()

# def signal_handler_reboot(signal, frame):
# 	Exit_Handler()

from subprocess import call
def reboot_callback(*args, **kwargs):
	Logger.info("Reboot requested")
	Common_Data.MAIN_INSTANCE.close()
	Common_Data.MAIN_INSTANCE=None
	Exit_Handler()
	# Now rebooting......
	call("sudo nohup reboot", shell=True)
	
def appexit_callback(*args, **kwargs):
	print(args)
	print(kwargs)
	
	Logger.info("Reboot requested")
	Common_Data.MAIN_INSTANCE.close()
	Common_Data.MAIN_INSTANCE=None
	Exit_Handler()
	# Exit application.....
	sys.exit()


class JSEM(App):
	def __init__(self, *args, **kwargs):
		super(JSEM, self).__init__(*args)

	def main(self):
		# insert an addition to the css stylesheet, specifically for the remi add-ons
		Logger.info("Looking for additional css files....")
		style_str = get_extra_css("css")
		head = self.page.get_child('head')
		head.add_child(str(id(style_str)), style_str)

		Common_Data.MAIN_INSTANCE = self
		return E_mainscreen(self)

	# def close(self):
	# 	print ('close method called om Remi app object')
	# 	super(JSEM, self).close()
	#
	# 	self.server.server_starter_instance._alive = False
	# 	self.server.server_starter_instance._sserver.shutdown()
	# 	print("server stopped")

selected_menubutton = None
def menubutton_clicked(clicked_button, DataCont, ChartCont, my_app, **kwargs):
	global selected_menubutton
	
	# Hightlight the clicked button and reset the previous clicked button
	if selected_menubutton != None:
		selected_menubutton.style.update({'width':'15%', 'height':'60%', 'background':'grey', 'color':'black'})
	clicked_button.style.update({'width':'20%', 'height':'80%', 'background':'red', 'color':'white'})
	selected_menubutton = clicked_button
	
	# find the buildscreen routine for the selected button or pass the button text to the show_all routine
	if hasattr(GUI_routines, selected_menubutton.text):
		buildscreen = getattr(GUI_routines, selected_menubutton.text)
		buildscreen(DataCont, ChartCont, my_app)
	else:
		# buildscreen = getattr(GUI_routines, "show_all")
		show_all(DataCont, ChartCont, clicked_button.text, my_app)
		
	

def E_mainscreen(my_app):
	CATEGORY_ID = Common_Data.CATEGORY_ID
	CATEGORY_NAME = Common_Data.CATEGORY_NAME

	TopCont = VBox(style='top:2%; left:2%; width:95%; height:95%; position:absolute')
	Common_Data.MAIN_CONTAINER = TopCont
	
	MenuCont = HBox(style='width:100%; height:8%; align-content:space-evenly; position:absolute')
	TopCont.append(MenuCont)

	HBox0 = HBox(style='width:100%; height:92%; position:relative; font-size:18px')
	TopCont.append(HBox0)
	Common_Data.CHARTS_AND_DATA_PARENT_CONTAINER = HBox0

	DataCont = Container(style='width:90%;height:96%;margin:10px;position:relative;order:-1;'
							   'overflow:auto;background-color:lightgrey;font-size:100%')
	HBox0.append(DataCont)
	Common_Data.DATA_PARENT_CONTAINER = DataCont

	ChartCont = VBox(style='width:10%;height:96%;margin:10px;position:static;overflow:auto;background-color:lightgrey;font-size:100%')
	HBox0.append(ChartCont, "Charts")
	Common_Data.CHARTS_PARENT_CONTAINER = ChartCont
	
	# make sure that when the chart container is clicked it also expands
	ChartCont.onclick.connect(expandcollapse, DataCont)
	# Same for data container
	DataCont.onclick.connect(expandcollapse, ChartCont)


	menu_items = ["Overzicht", "Electra", "Warmte", "Solar", "Laadpaal", "Zwembad"]
	for cat in CATEGORY_NAME:
		# print(cat," menu_item ", CATEGORY_NAME[cat].menu_item)
		if CATEGORY_NAME[cat].menu_item==True: menu_items.append(CATEGORY_NAME[cat].name)
	menu_items.append("Instellingen")
		
	for menu_item in menu_items:
		btn1 = Button(menu_item)
		btn1.style.update({'width':'15%', 'height':'60%', 'background-color':'grey', 'color':'black'})
		btn1.onclick.connect(menubutton_clicked, DataCont, ChartCont, my_app)
		MenuCont.append(btn1, menu_item)
		
	# simulate click on first menu_item
	menubutton_clicked(MenuCont.get_child(menu_items[0]), DataCont, ChartCont, my_app)
	return TopCont



#Configuration
configuration = {'config_multiple_instance': False, 'config_address': '192.168.178.220', 'config_start_browser': False, 'config_enable_file_cache': True, 'config_project_name': 'test', 'config_resourcepath': './res/', 'config_port': 8081}

if __name__ == "__main__":

	Logger.info ("Starting JSEM")
	
	Logger.info ("Connecting to database: " + str(DBFILE))
	Common_Data.DB_STORE = DBstore_engine(name="JSEM DB_store engine", dbfile=DBFILE)

	Logger.info ("Loading category definitions")
	load_all_categories()

	Logger.info ("Initializing Warmtepomp - WS172 H3")
	SdmModbusInterface(name="Warmtepomp", auto_start=True)
	#
	# Logger.info ("Starting Zonnepanelen - Solis 3p5K-4g")
	# SdmModbusInterface(name="Solar", auto_start=True)

	# Logger.info ("Initializing Slimmemeter - ESMR 5.0")
	# # ESMR50Interface(name="Slimmemeter", auto_start=True)
	# ESMR50_via_TCP(name="Slimmemeter", auto_start=True, address='192.168.178.220', port=65432, conn_type="DEFAULT-TCP")

	# Logger.info ("Initializing Vermogensmeters - M_bus")
	# MbusInterface(name="Vermogensmeters", auto_start=True)

	# Logger.info ("Initializing laadpaal - Modbus")
	# SdmModbusInterface(name="Laadpaal", auto_start=True, awake_registername='max_current_setpoint', awake_interval=60)

	# Logger.info ("Initializing SDM72 verm meter - Modbus")
	# SdmModbusInterface(name="Verm_meter_WP", auto_start=True)
	#
	# Logger.info ("Initializing Zwembadpomp - Shelly")
	# ShellyRelayInterface(name="Zwembadpomp", device_count=3, auto_start=True)

	Logger.info ("Initializing Vloervoelers - Modbus")
	SdmModbusInterface(name="Vloer", auto_start=True)



	Logger.info ("Loading datapoints definitions")
	load_and_configure_datapoints()

	for interf in Common_Data.INTERFACE_ID.values():
		Logger.info ("%s-- Has %s subscribed datapoints, %s polling datapoints and %s searchkeys.." %
					 (interf.name, len(interf.dpids), len(interf.pollQ), len(interf.searchkeys)))

	# Start the TCP SQL server to enable remote access to the database
	# Now first retrieve some network addresses....
	found_address='127.0.0.1'
	found_tcpport=65432 if TCPPORT == 0 else TCPPORT
	if TCPHOST=='':
		try:
			found_address = get_ip_address()
		except:
			Logger.error ("Can't retrieve IP address and none given in config.py file, using localhost 127.0.0.1....")
	else:
		found_address = TCPHOST
		
	if MAX_EXTERNAL_CONN > 0:
		# Here I start a parallel thread that executes the TCP server
		t = threading.Thread(target=TCPServer, kwargs=dict(host=found_address, port=found_tcpport, max_connections=MAX_EXTERNAL_CONN))
		t.daemon = True
		t.start()
		Logger.info("TCP-SQL Server proces started on address: %s, port: %s" % (found_address, found_tcpport))

	# start the optimizer on the next hour and then every hour
	# Common_Data.JSEM_RULES.append(
	# 							JSEM_Rule(name="Warmtepomp optimalisatie algoritme",
	# 							rule=JSEM_Rules.optimizer,
	# 							# interval=60,
	# 							interval=3600,
	# 							startup_delay= 3600 - int(datetime.now().timestamp()) % 3600 + 30,		# 30 seconden na het hele uur
	# 							# startup_delay= 60,
	# 							start=True)
	# 							)
	#
	# #start the execution of the strategy every minute
	# Common_Data.JSEM_RULES.append(
	# 							JSEM_Rule(name="Warmtepomp strategie 1",
	# 							rule=JSEM_Rules.warmtepomp_strat_1,
	# 							interval=60,
	# 							startup_delay=30,
	# 							start=True)
	# 							)
	#
	# Common_Data.JSEM_RULES.append(
	# 							JSEM_Rule(name="EPEX data downloader",
	# 							rule=JSEM_Rules.get_epex_data,
	# 							interval=24*3600,
	# 							startup_delay= get_seconds_untill(untill_time='16:00:00'),
	# 							start=True)
	# 							)
	#
	# Common_Data.JSEM_RULES.append(
	# 							JSEM_Rule(name="LEBA data downloader",
	# 							rule=JSEM_Rules.get_leba_data,
	# 							interval=24*3600,
	# 							startup_delay= get_seconds_untill(untill_time='22:00:00'),
	# 							start=True)
	# 							)
	#
	# Common_Data.JSEM_RULES.append(
	# 							JSEM_Rule(name="Weather forecast",
	# 							rule=JSEM_Rules.get_weather_frcst,
	# 							interval=24*3600,
	# 							startup_delay= get_seconds_untill(untill_time='23:45:00'),
	# 							start=True)
	# 							)

	# Common_Data.JSEM_RULES.append(
	# 							JSEM_Rule(name="laadpaal_rule_1",
	# 							rule=JSEM_Rules.laadpaal_rule_1,
	# 							interval=30,
	# 							startup_delay=45,
	# 							start=True)
	# 							)
	#

	# Common_Data.JSEM_RULES.append(
	# 							JSEM_Rule(name="zwembad_rule_1",
	# 							rule=JSEM_Rules.zwembad_rule_1,
	# 							interval=60,
	# 							startup_delay=30,
	# 							start=True)
	# 							)
	#
	# Common_Data.JSEM_RULES.append(
	# 							JSEM_Rule(name="solar_rule_1",
	# 							rule=JSEM_Rules.solar_rule_1,
	# 							interval=60,
	# 							startup_delay=30,
	# 							start=True)
	# 							)
	#
	Common_Data.JSEM_RULES.append(
								JSEM_Rule(name="load_balance_rule",
								rule=JSEM_Rules.load_balance_rule,
								interval=5,
								startup_delay=30,
								start=True)
								)

	# Set up s timer to automatically force a reboot every night
	timerset = get_seconds_untill(untill_time=Reboot_time)
	Logger.info (f"Setting up automatic reboot, at {Reboot_time}, timer set for {timerset} seconds")
	reboot_timer = threading.Timer(timerset, reboot_callback)
	reboot_timer.start()

	
	
	Logger.info ("Starting Remi web interface")
	
	
	# start(MyApp,address='127.0.0.1', port=8081, multiple_instance=False,enable_file_cache=True, update_interval=0.1, start_browser=True)
	try:
		signal.signal(signal.SIGUSR1, appexit_callback)
		signal.signal(signal.SIGUSR2, reboot_callback)
		
		# start	(
		# 		JSEM, debug=False, address='192.168.178.220', port=8081,
		# 		multiple_instance=False,
		# 		enable_file_cache=True,
		# 		start_browser=False
		# 		# username="jdderijke@yahoo.com", password="Jsem@Jd878481"
		# 		)

		start	(
				JSEM, debug=False, address='127.0.0.1', port=8081,
				multiple_instance=False,
				enable_file_cache=True,
				start_browser=True
				# username="jdderijke@yahoo.com", password="Jsem@Jd878481"
				)

		# Als de GUI loopt dan blijft hij meestal in de regel hierboven loopen, als we door deze regel heenvallen 
		# (dit kan gebeuren als er een control-C vanaf de terminal is ingetypt, of omdat de close() routine is aangeroepen
		# dan is REMI dus gestopt! Maar de exit handler heeft nog niet gelopen....
		Logger.info('Remi stopped....')
		Common_Data.MAIN_INSTANCE=None
		Exit_Handler()
	except Exception as err:
		Logger.error (f"Program stopped unexpectedly, {err}")
		# stop Remi
		Common_Data.MAIN_INSTANCE.close()
		Common_Data.MAIN_INSTANCE=None
		Exit_Handler()
		# Als Remi hier terecht komt dan is hij gestopt via een detectie in de idle loop van het Kloofmachine_GUI object.
		# Dat wil dan zeggen dat de exithandler al loopt en staat te wachten op REMI_IS_RUNNING=False
		# Common_Data.REMI_IS_RUNNING = False
		# trigger een SIGUSR1 signal
		# if not Exit_Handled: os.kill(os.getpid(), signal.SIGUSR1)
