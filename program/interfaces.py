import socket

from Config import MsgQ_Alarm, ENVIRONMENT
from Common_Enums import *
from enum import Enum

import threading
import time
import re
import sys
from datetime import datetime
# from dateutil.relativedelta import relativedelta
import random
import serial

from Conversion_Routines import ByteArrayToHexString, From_ByteArray_converter, To_ByteArray_converter, \
	HexStringToByteArray
from DataPoint import Datapoint
from LogRoutines import Logger
from DB_Routines import populate_interface, get_pollmessages_from_database
from JSEM_Commons import get_ip_address, Is_NOE, IsNot_NOE, dump, Waitkey, string_builder, Calculate_Timerset, spincursor
from Common_Data import DATAPOINTS_ID, DATAPOINTS_NAME, CATEGORY_ID, CATEGORY_NAME
import remi.gui as gui
import errno

import sdm_modbus
from sdm_modbus import *
from pyShelly import pyShelly



class styled_txt(gui.Widget, gui._MixinTextualWidget):
	def __init__(self, text, *args, **kwargs):
		super(styled_txt, self).__init__(*args, **kwargs)
		self.type = 'span'
		self.text=text


	
class BaseInterface(object):
# in order to use the properties functionality the class must inherit from the OBJECT class (where properties are implemented)

	def get_connstate(self):
		return self._connstate
	def set_connstate(self,value):
		if value != self.connstate:
			self._connstate = value
			self.upd_stats()
	connstate = property(get_connstate,set_connstate)
	
	def get_sndstate(self):
		return self._sndstate
	def set_sndstate(self,value):
		if value != self.sndstate:
			self._sndstate = value
			self.upd_indicators()
	sndstate = property(get_sndstate,set_sndstate)
	
	def get_recstate(self):
		return self._recstate
	def set_recstate(self,value):
		if value != self.recstate:
			self._recstate = value
			self.upd_indicators()
	recstate = property(get_recstate,set_recstate)

	def get_pollstate(self):
		return self._pollstate
	def set_pollstate(self,value):
		if value != self.pollstate:
			self._pollstate=value
			self.upd_stats()
	pollstate = property(get_pollstate,set_pollstate)
	

	def __repr__(self):
		conntype = self.conn_type.split('-')[-1].upper()
		state = self.connstate.name
		if conntype in ['TCP', 'UDP']:
			return (f'{self.name}:{state}|{self.conn_type}|{self.address}:{self.port}|dev:{self.device_type}|addr:{self.device_sub_addr}|retr:{self.maxretries}|timeout:{self.timeout}')
		elif conntype in ['SERIAL']:
			return (f'{self.name}:{state}|{self.conn_type}|{self.address}|{self.baudrate}|{self.bytesize}|{self.parity}|{self.stopbits}|{self.xonxoff}|{self.rtscts}|retr:{self.maxretries}|timeout:{self.timeout}')
		else:
			return(f'{self.name}:{state}|unknown connectiontype {self.conn_type}')


	
	def __init__(self, name='Default', **kwargs):
		self.name = name
		# set default properties, they will be overwritten by the populate_interface routine
		self.address = '0.0.0.0'
		self.conn_type = ''
		self.device_type = 'UNKNOWN'
		self.device_sub_addr = 0
		self.port = 0
		self.maxretries = 3
		self.timeout = 30
		# defaults for serial connections
		self.baudrate = 115200
		self.bytesize = 'EIGHTBITS'
		self.parity = 'PARITY_NONE'
		self.stopbits = 'STOPBITS_ONE'
		self.xonxoff = 0
		self.rtscts = 0
		
		# populate_interface adds properties to this interface object based on the DB table interface fields
		populate_interface(self, name=self.name)
		# If a port is specified... make sure its type int .... None is also allowed
		if self.port: self.port = int(self.port)
		# Now overrule any property if it appears in kwargs and add missing properties
		for prop in kwargs:
			setattr(self, prop, kwargs.get(prop, None))
		
		# Add standard instance properties
		self.msgQ = list()
		""" msgQ is the list of messages waiting to be send via the send routine """

		# searchkeys is een dictionary met alle searchkeys van alle enabled datapoints op deze interface. Searchkey is KEY en 
		# DatapointID's (want het kunnen er meer zijn) is een lijst met datapoints die aan de searchstring gekoppeld zijn... 
		self.searchkeys = dict()
		
		# dpids is the dictionary with all subscribed datapoint ID's to this interface
		self.dpids = dict()
		
		# Koppel de juiste enabled datapoints aan deze interface
		for dp in DATAPOINTS_ID.values():
			if dp.enabled and dp.interfaceID == self.ID:
				self.subscribe(dp)
				
		
		# the following widgets are used to display the status of the connection, poller, sender and receiver part of this interface
		self.recvwidget = None
		self.sendwidget = None
		self.connwidget = None
		self.pollwidget = None
		
		# define a thread to use later for starting the receiver
		self.stop_receiving=True
		self.stop_sending=True
		self.async_recv = None
		self.async_send = None
		self.onconnect_start_receiver=True
		self.onconnect_start_sender=False
		self.onconnect_start_poller=True
		
		self.localecho_send_messages = False
		
		self.pollQ = list()
		self.POLLQ_widget = None
		self.poll_timer = None
		self.stoppoll = True
		self._pollstate = PollState.Not_Polling
		self.pollstate = PollState.Not_Polling
		# self.pollmsg_name = dict()
		# self.pollmsg_id = dict()


		self._connstate = 0
		self._sndstate = 0
		self._recstate = 0        
		self._connstate = ConnState.DisConnected
		self.connstate = ConnState.DisConnected
		self.sndstate = Sndstate.Sender_Stopped
		self.recstate = Recstate.Receiver_Stopped
		
		# The sockets and objects that hold the connections
		self.UDPclientSock = None
		self.TCPclientSock = None
		self.Ser = None
		self.Modbus_Conn = None
		self.Shelly = None
				
		self.idle_style={"color":"black", "background-color":"white"} 
		self.dp_style = {"color":"black", "background-color":"yellow"}
		self.unknown_style = {"color":"black", "background-color":"lightgrey"}
		self.send_style={"color":"white", "background-color":"green"}
		self.error_style={"color":"white", "background-color":"red"}
		
		# # A place to store the thread ID's' of the sender and receiver routine (if running ASYNC)
		# self.send_thread = None
		# self.recv_thread = None
		# self.async_send = None
		# self.async_recv = None
		
		# Default display format for the monitor widget
		self.display_format = "HEX"
		# monitor widget to view the communication channel in real time
		self.MON_widget=None
		# buffer to store the communication while the monitor widget is paused from updating
		self.MON_buffer=[]
			

	def subscribe(self, datapoint=None):
		'''
		By this method an enabled datapoint can subscribe to an interface. By doing so the searchstring will be added to 
		the interface dictionary of searchstrings it listens to.
		If searchstring is detected the interface will fill the value property of the datapoint by means of its decode_msg method.
		Also the datapoint will be added to the PollQ for this interface if needed.
		'''
		if datapoint is None: return
		dp=datapoint
		# first remove any searchkey and pollQ entries of this datapoint.
		self.un_subscribe(dp)
		
		if not dp.enabled: return
		
		# link this interface to the datapoint and vice versa
		dp.interface = self
		self.dpids[dp.ID] = dp
		Logger.debug("%s-- Datapoint %s subscribed." % (self.name, dp.name))

		# Koppel de searchkeys van enabled datapoints aan deze interface
		if IsNot_NOE(dp.searchkey):
			if dp.searchkey in self.searchkeys:
				# voeg hem alleen toe als hij er niet al instond
				if not dp.ID in self.searchkeys[dp.searchkey]:
					self.searchkeys[dp.searchkey].append(dp.ID)
			else:
				self.searchkeys[dp.searchkey]=[dp.ID]
		
		# het datapoint moet ook evt toegevoegd worden aan de pollQ
		if dp.poll and IsNot_NOE(dp.poll_interval):
			random.seed()
			# for every ENABLED Pollmessage add the message to the PollQ and calcukate the initial ticks (1ms) and the ticksremaining, to
			# improve performance...use a list of lists that can be sorted on the ticks_remaining
			initial, repeat = Calculate_Timerset(interval=dp.poll_interval)
			# Polling interval in the DB is stored in SECONDS, not ticks, so convert to ticks first
			if repeat != None: repeat = repeat * 1000
		
			# distribute the ticks_remaining around with a random distribution arounnd the tick_initial time, if we need to do a
			if initial < 600:
				# om te voorkomen dat in de eerste 10 minuten alle interfaces overspoeld worden met poll messages
				initial = (initial*1000) - random.randint(0,(initial*1000))
				# print('1-initial = %s' % initial)
			else:
				# daarna mag het hoogstens 1 minuut (60000 ticks) afwijken
				initial = (initial*1000) - random.randint(0,60000)
				# print('2-initial = %s' % initial)
			self.pollQ.append([initial,repeat,dp])
			Logger.debug("%s-- Datapoint %s added to the Poll Queue." % (self.name, dp.name))
			
		
		
	def un_subscribe(self, datapoint=None):
		'''
		This method removes the datapoint from the searchkey and poll mechanisms of this interface.
		After un_subscribing a datapoint will no longer be detected by its searchkey and will no longer
		be polled by this interface.
		'''
		if datapoint is None: return
		dp=datapoint
		# first remove any searchkey entries of this datapoint.
		for key in list(self.searchkeys.keys()):
			dpIDs = self.searchkeys[key]
			if dp.ID in dpIDs:
				dpIDs.remove(dp.ID)
				# Check if this was the only entry for this searchkey, if so remove searchkey also
				if dpIDs == []: self.searchkeys.pop(key)

		# Eerst eventuele oude PollQ entry verwijderen
		for entry in self.pollQ:
			polling_dp = entry[2]
			if polling_dp.ID == dp.ID: 
				self.pollQ.remove(entry)
				break
				
		# last remove the connection.
		dp.interface = None
		self.dpids.pop(dp.ID, None)

	
	# send queue handling routines --------------------------------------------------------------------------------
	def get_nxtmsg(self):
		'''
		Method returns the first message in the send queue (msgQ)
		Returns the message, if an achknowlegde receipt is expected, and the message type (Commandmessage or Pollmessage)
		Message are stored in the msgQ in tuples (3 elements)
		The get_nxtmsg and add_msg routines also control the sndstate indicator of the interface...
		'''
		if self.msgQ: 
			(value, acknowledge_receipt, msgtype) = self.msgQ.pop(0)
			if not self.msgQ: self.sndstate=Sndstate.Waiting_For_MsgToSend
			return value, acknowledge_receipt, msgtype
		else: 
			return None, None, None
		
		
	def add_msg(self, value, acknowledge_receipt:bool, msgtype:MsgType):
		'''
		Method adds a message to the send queue, if the queue size becomes larger then MsgQ_Alarm (in Config), an error is generated and
		the interface is disconnected and reconnected to the device (losing all of the msgQ in the process)
		adds the message, if an achknowlegde receipt is expected, and the message type (Commandmessage or Pollmessage) packed as a tuple
		The get_nxtmsg and add_msg routines also control the sndstate indicator of the interface...
		'''
		if ENVIRONMENT not in [Environment.Productie, Environment.Test_full]:
			return

		self.sndstate=Sndstate.Sending_Msg
		self.msgQ.append((value, acknowledge_receipt, msgtype))
		if len(self.msgQ) >= MsgQ_Alarm:
			Logger.error(f'{self.name}-- Send msgQ reached level of {len(self.msgQ)} messages, reconnecting this interface...')
			self.disconnect(reconnect=True)
			
		
	# connect and disconnect routines --------------------------------------------------------------------------------
	def connect(self):
		from tqdm import tqdm
		
		if ENVIRONMENT not in [Environment.Productie, Environment.Test_full]: return
		
		if self.connstate == ConnState.Connected:
			raise ConnectionError (f'{self.name}-- Cant connect...already connected to {self.conn_type}-{self.address}:{self.port}')

		try:
			Logger.info(f'{self.name}-- Connecting to device....')
			self.connstate = ConnState.Connecting
			
			if self.conn_type in ["MBUS-TCP", "RS485-TCP", "DEFAULT-TCP"]:
				self.TCPclientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.TCPclientSock.settimeout(self.timeout)
				for tries in range(self.maxretries):
					try:
						self.TCPclientSock.connect((self.address, self.port))
						self.connstate = ConnState.Connected
						break
					except Exception as err:
						time.sleep(0.5)
						
					
			elif self.conn_type == "MODBUS-TCP":
				for tries in range(self.maxretries):
					try:
						initializer = getattr(sdm_modbus, self.device_type)
						self.Modbus_Conn = initializer(
							host=self.address,
							port=self.port,
							timeout=self.timeout,
							framer=None,
							unit=self.device_sub_addr,
							udp=False
						)
						self.connstate = ConnState.Connected
						break
					except Exception as err:
						Logger.error(
							f'{self.name}-- Problem connecting {self.conn_type}-{self.address}:{self.port} attempt {tries + 1}, {err}')
						time.sleep(0.5)
						
			elif self.conn_type == "P1-SERIAL":
				# Configure serial Com port
				self.Ser = serial.Serial()
				self.Ser.baudrate = self.baudrate
				self.Ser.bytesize=getattr(serial,self.bytesize)
				self.Ser.parity=getattr(serial,self.parity)
				self.Ser.stopbits=getattr(serial,self.stopbits)
				self.Ser.xonxoff=self.xonxoff
				self.Ser.rtscts=self.rtscts
				self.Ser.timeout=self.timeout
				# beetje verwarrend maar met port wordt hier een serial COM port bedoeld, oftewel een adres...
				self.Ser.port = self.address
				for tries in range(self.maxretries):
					try:
						# Now try to Open the COM port
						self.Ser.open()
						self.connstate = ConnState.Connected
						Logger.info(f'{self}')
						break
					except Exception as err:
						Logger.error (f'{self.name}-- Problem connecting {self.conn_type}-{self.address} attempt {tries+1}, {err}')
						time.sleep(0.5)
						
			elif self.conn_type == "SHELLY-TCP":
				# define a new Shelly interface
				for tries in range(self.maxretries):
					self.Shelly = pyShelly()
					try:
						self.Shelly.start()
						# self.shelly.discover()
						self.Shelly.add_device_by_ip(self.address, 'IP-addr')  # this takes some time
						# Now the device list should get filled with logical devices on this address, a Relay has 3... 1 relay and 2 switches
						total_time = 0.0
						with tqdm(total=self.timeout) as pbar:
							while len(self.Shelly.devices) < self.device_count:
								loop_start = time.time()
								if total_time > self.timeout:
									raise Exception('Timeout reached')
								else:
									time.sleep(0.1)
								loop_time = round(time.time() - loop_start, 2)
								pbar.update(loop_time)
								total_time += loop_time
							# Finish, fill up the pbar to 100%
							pbar.update(self.timeout - total_time)
						
						Logger.info(
							f'Found the following devices on address {self.address}: {[x.device_type for x in self.Shelly.devices]}')
						self.connstate = ConnState.Connected
						Logger.info(f'{self}')
						break
					except Exception as err:
						Logger.error(
							f'{self.name}-- Problem connecting {self.conn_type}-{self.address} attempt {tries + 1}, {err}')
						time.sleep(0.5)
				
				
			if not self.connstate == ConnState.Connected:
				self.connstate = ConnState.DisConnected
				raise ConnectionError (f'{self.name}-- Can not connect to {self.conn_type}-{self.address}:{self.port}')
			else:
				Logger.info(f'{self}')		#The interface dunder method __repr__ contains a short description of the interface
			
				# Extra start options
				if self.onconnect_start_receiver:
					# define a new listening thread and start it
					self.async_recv = threading.Thread(target=self.recv)
					# have the receiver run as daemon thread....
					self.async_recv.daemon = True
					self.async_recv.start()
				if self.onconnect_start_sender:
					# have the SENDER run as daemon thread....
					self.async_send = threading.Thread(target=self.send)
					self.async_send.daemon = True
					self.async_send.start()
				if self.onconnect_start_poller:
					# start the poller for this interface
					self.start_polling()
	
				Logger.info(f'{self.name}-- finished connecting')

		except ConnectionError as err:
			Logger.error(str(err))
		except Exception as err:
			Logger.exception(str(err))
			# # There was an error....make sure any half made connection or deamon thread is closed....
			# self.disconnect(reconnect=False)
		
		
		
	def disconnect(self, reconnect=False):
		address = self.address.strip().upper()
		conn_type = self.conn_type.strip().upper()
		port = self.port
		self.connstate=ConnState.DisConnecting
		try:
			Logger.info (f'{self.name}-- {conn_type}-{address}:{port} disconnect requested with reconnect={reconnect}')
			# Stop any sending, receiving
			self.stop_receiving = True
			self.stop_sending = True
			
			# See if any threads where started on connect... receiver, sender and poller, stop those tasks
			self.stop_polling()
			if self.async_recv:
				# ...wait untill the daemon thread has finished, if join is called on the current thread, a runtimeerror is generated
				try:
					self.async_recv.join()
					# give receiver thread the chance to suspend operation and indicate receiver has stopped
				except Exception as err:
					pass
				
			if self.async_send:
				# ...wait untill the daemon thread has finished, if join is called on the current thread, a runtimeerror is generated
				try:
					self.async_send.join()
					# give sender thread the chance to suspend operation and indicate sender has stopped
				except Exception as err:
					pass
			self.recstate=Recstate.Receiver_Stopped
			self.sndstate=Sndstate.Sender_Stopped
				
			# empty the send_msgQ
			while True:
				msg,_,_ = self.get_nxtmsg()
				if msg is None: break
				
			# close connection socket
			try:
				if conn_type in ["EBUS-TCP", "MBUS-TCP", "RS485-TCP", "DEFAULT-TCP"]:
					# shutdown forces all processes to disconnect from the socket and sends an EOF to the peer, but you still need to close the socket
					self.TCPclientSock.shutdown(socket.SHUT_RDWR)
					self.TCPclientSock.close()
					self.TCPclientSock=None
				elif conn_type in ["EBUS-UDP"]:
					self.UDPclientSock.close()
					self.UDPclientSock=None
				elif conn_type == "MODBUS-TCP":
					self.Modbus_Conn.close()
					self.Modbus_Conn=None
				elif conn_type == "P1-SERIAL":
					self.Ser.close()
					self.Ser=None
				elif conn_type == "SHELLY-TCP":
					self.Shelly.close()
					self.Shelly=None
			except:
				pass
			Logger.info (f'{self.name}-- {conn_type}-{address}:{port} disconnected')
			self.connstate=ConnState.DisConnected
		except Exception as err:
			Logger.exception(str(err))
		finally:
			if reconnect:
				# Wait 1 second before reconnecting
				time.sleep(1)
				self.connect()
		

			
	# Polling routines for starting and stopping polling messages over this interface
	def start_polling(self):
		self.stop_polling()
		if not self.connstate == ConnState.Connected: return
		
		try:
			if self.pollQ == []:
				# If the PollQ is empty then wait for 1 second before looking again
				timerset = 1000
			else:
				# SORT ON THE FIRST ELEMENT (ticks remaining) of the lists in the pollQ
				self.pollQ.sort(key=lambda x: x[0])
				self.update_POLLQ_widget()
				timerset = float(self.pollQ[0][0])
				
			# and start a timer to wait for the first ticks_remaining time in the PollQ
			self.poll_timer = threading.Timer(timerset/1000, lambda:self.__poll_timer_callback(timerset))
			self.poll_timer.start()
			self.pollstate=PollState.Polling
			Logger.info ("Polling started on interface %s, polling %s datapoints.." % (self.name, len(self.pollQ)))
		except Exception as err:
			Logger.exception(str(err))
		
	def __poll_timer_callback(self, time_passed):
		try:
			# check if we are still polling
			if self.pollstate==PollState.Not_Polling: return
			# or if we lost the connection on this interface
			if self.connstate != ConnState.Connected:
				self.stop_polling()
				return 
				
			if self.pollQ == []: 
				timerset = 1000
			else:
				# substract the passed time from all ticks_remaining in the queue
				self.pollQ = [[x[0]-time_passed,x[1],x[2]] for x in self.pollQ]
				index=0
				while index<len(self.pollQ) and self.pollQ[index][0]<=0:
					entry=self.pollQ[index]
					# Create a poll telegram to be send, first find the proper poll defition
					polling_dp = entry[2]
					# make and send poll message
					self.make_poll_telgr(polling_dp)

					if entry[1] == None: 
						# check if this was a one_time poll message... if so remove it from the PollQ
						self.pollQ.pop(index)
						continue
					else:
						# reset the ticks remaining to the initial value
						entry[0]=entry[1]
						index+=1
				# now do the rest of the bookkeeping for the polling: Re-sort the queue, so that the the next Pollmessage is first in queue, 
				# SORT ON THE FIRST ELEMENT (ticks remaining) of the lists in the pollQ
				self.pollQ.sort(key=lambda x: x[0])
				# update a potential POLLQ widget in the GUI
				self.update_POLLQ_widget()
				# and get the next timerset
				timerset = float(self.pollQ[0][0])

			# print ("polling....next poll in " + "{:3.2f}".format(timerset/1000) + " seconds.") 
			self.poll_timer = threading.Timer(timerset/1000, lambda:self.__poll_timer_callback(timerset))
			self.poll_timer.start()
		except Exception as err:
			Logger.error("%s-- Error in logger, pollQ length = %s" % (self.name, len(self.pollQ)))
			Logger.exception (str(err))
		
	def stop_polling(self):
		if self.pollstate==PollState.Not_Polling: return
		
		try:
			# cancel running poll_timer
			self.poll_timer.cancel()
			# wait untill the timer has exited, this may cause an exception when no timer is active....
			self.poll_timer.join()
		except Exception as err:
			pass
		finally:
			self.poll_timer=None
			self.pollstate=PollState.Not_Polling
			Logger.info ("Polling stopped on interface: "+ self.name)
			
 

				

	def check_msg(self, BA_msg):
		'''
		Placeholder for the check_msg routine
		Implement check_msg routine in the specific interface classes, not in the base class
		'''
		# print ("check_msg of BaseInterface called..... ")
		return True

											
			
	def update_POLLQ_widget(self):
		if self.POLLQ_widget is None: return
		self.POLLQ_widget.empty()
		style={"color":"white", "background-color":"black","font-family":"Courier","font-size":"15px"}
		Headerstr = ""
		Headerstr = string_builder(Headerstr, 0, "tcks_rem")
		Headerstr = string_builder(Headerstr, 11, "tcks_init")
		Headerstr = string_builder(Headerstr, 22, "datapoint")
		self.POLLQ_widget.append(styled_txt(Headerstr, style=style))
		style={"color":"black", "background-color":"white"} 
		teller = 1
		for ticksremain, ticksinit, polldp in self.pollQ:
			pollQstr = ""
			pollQstr = string_builder(pollQstr, 0, str(int(ticksremain)))
			pollQstr = string_builder(pollQstr, 11, str(ticksinit))
			pollQstr = string_builder(pollQstr, 22, str(polldp.name))
			
			if teller == 1:
				self.POLLQ_widget.append(styled_txt(pollQstr, style={"color":"white", "background-color":"red","font-family":"Courier","font-size":"15px"})) 
			elif teller == 2:
				self.POLLQ_widget.append(styled_txt(pollQstr, style={"color":"black", "background-color":"orange","font-family":"Courier","font-size":"15px"}))
			elif teller == 3:
				self.POLLQ_widget.append(styled_txt(pollQstr, style={"color":"black", "background-color":"yellow","font-family":"Courier","font-size":"15px"}))
			else:
				self.POLLQ_widget.append(styled_txt(pollQstr, style={"color":"black", "background-color":"white","font-family":"Courier","font-size":"15px"}))
			teller+=1
			
	def update_MON_widget(self, BA_msg, style=None):
		'''
		converteerd een ByteArray naar ASCII of HEX presentatie en presenteerd die in op het scherm in de monitor
		Als de monitor niet update (op pause staat) slaat hij ze zoals op in het MON_buffer zodat ze niet verloren gaan.
		'''
		try:
			if self.MON_widget is None: return
			
			if self.display_format == "HEX":
				displ_txt = ByteArrayToHexString(BA_msg) + " "
			elif self.display_format == "ASCII":
				displ_txt = str(BA_msg, 'utf-8')
			elif self.display_format == "TEXT":
				# just display BA_msg as TEXT, no conversion from bytearray
				displ_txt = BA_msg
				
			# No style? Use default style
			if style == None: style={"color":"black", "background-color":"white"} 
			
			new_element = styled_txt(displ_txt, style=style)
			
			if self.MON_widget.attributes["is_updating"]:
				self.MON_widget.append(new_element)
				# werkt niet
				# self.MON_widget.style["overflow-anchor"] = "none"
				# new_element.style["overflow-anchor"]="auto"
				# new_element.redraw()
			else:
				self.MON_buffer.append(new_element)
		except Exception as err:
			Logger.error(str(err))
			

	def flush_MON_buffer(self):
		'''
		flusht de inhoud van hey monitor buffer en zet ze op het scherm in de monitor (als die er is)
		'''
		if self.MON_widget is not None:
			for new_element in self.MON_buffer:
				self.MON_widget.append(new_element)
				# werkt niet
				# self.MON_widget.attributes["overflow-anchor"] = "none"
				# new_element.attributes["overflow-anchor"]="auto"
				
		self.MON_buffer=[]
		
			
		
			
	def upd_indicators(self):
		try:
			if self.recvwidget is not None:
				if self.recstate == Recstate.Receiver_Stopped:
					self.recvwidget.css_background_color = "grey"
				elif self.recstate == Recstate.Waiting_For_MsgToReceive:
					self.recvwidget.css_background_color = "green"
				elif self.recstate == Recstate.Receiving_Msg:
					self.recvwidget.css_background_color = "red"
				elif self.recstate == Recstate.Deconstructing_Msg:
					self.recvwidget.css_background_color = "orange"
				self.recvwidget.redraw()
				
			if self.sendwidget is not None:
				if self.sndstate == Sndstate.Sender_Stopped:
					self.sendwidget.css_background_color = "grey"
				elif self.sndstate == Sndstate.Waiting_For_MsgToSend:
					self.sendwidget.css_background_color = "green"
				elif self.sndstate == Sndstate.Sending_Msg:
					self.sendwidget.css_background_color = "red"
				self.sendwidget.text = self.sendwidget.text.split(":")[0] + ": " + str(len(self.msgQ))
				self.sendwidget.redraw()
				
		except Exception as err:
			# self.write("upd_stats-" + str(err))
			raise Exception("upd_stats-" + str(err))         
		finally:
			pass
		
	def upd_stats(self):
		try:
			if self.connwidget is not None:
				if self.connstate == ConnState.DisConnected:
					self.connwidget.css_background_color = "grey"
				elif self.connstate == ConnState.Connecting:
					self.connwidget.css_background_color = "orange"
				elif self.connstate == ConnState.Connected:
					self.connwidget.css_background_color = "green"
				elif self.connstate == ConnState.DisConnecting:
					self.connwidget.css_background_color = "orange"
				self.connwidget.text = self.connstate.name
				self.connwidget.redraw()
					
			if self.pollwidget is not None: 
				if self.pollstate == PollState.Polling:
					self.pollwidget.css_background_color = "green"
				elif self.pollstate == PollState.Not_Polling:
					self.pollwidget.css_background_color = "grey"
				self.pollwidget.text = self.pollstate.name
				self.pollwidget.redraw()
			
		except Exception as err:
			# self.write("upd_stats-" + str(err))
			raise Exception("upd_stats-" + str(err))         
		finally:
			pass
		
	def pre_process_message(self, messagestring):
		# print ("pre_process_message of BaseInterface called..... ")
		return messagestring



class SdmModbusInterface(BaseInterface):
	def __init__(self, *args, **kwargs):
		# set the interface_type field, as we maybe want to use the name property for more specific names
		self.interface_type = self.__class__.__name__
		super().__init__(*args, **kwargs)

		self.localecho_send_messages = True
		
		self.sk_format = SearchkeyFormat.ASCII
		self.display_format = "TEXT"
		
		self.awake_interval = kwargs.get('awake_interval', 30)
		self.awake_registername = kwargs.get('awake_registername', None)
		
		self.onconnect_start_receiver=False
		self.onconnect_start_sender=True
		self.onconnect_start_poller=True
		if kwargs.get("auto_start", False): self.connect()
		
		
	def recv(self, results):
		style=self.unknown_style
		
		for key, value in results.items(): 
			dp_IDs, _ = self.get_datapoints_from_msg(key)
			if dp_IDs != []:
				# we found at least one datapoint connected to this message
				style=self.dp_style
				# Check if we need to log the messages for these datapoints for testing purposes
				for dp_ID in dp_IDs:
					dp = DATAPOINTS_ID[dp_ID]
					if dp.log_messages==True: Logger.info(f'Logmessages:{dp.name} : {key}:{value}')
				# now check if the message is corrupt or not
				if self.check_msg(key):
					for dp_ID in dp_IDs: self.decode_msg(value, dp_ID)
				else:
					pass
			else:
				# No datapoint found, this message is unknown to us
				style=self.unknown_style

			self.update_MON_widget(f'{key}:{value} \n', style=style)

				
	def send(self):
		"""
		For modbus the communication is synchronous, we send a request and the modbus device answers.
		Apart from that a keep_awake needs to be send to let the device know the connection is still
		up. So this send routines loops and any results received from a request to the device is dispatched
		to the receive routine to be decomposed..
		:return:
		"""
		if ENVIRONMENT not in [Environment.Productie, Environment.Test_full]:
			return
		
		if self.connstate != ConnState.Connected:
			Logger.error(f'{self.name}-- Trying to call send while not connected, first connect!')
			return
		
		last_awake_time = time.time()
		self.stop_sending = False
		try:
			while not self.stop_sending:
				if not self.Modbus_Conn.connected():
					self.Modbus_Conn.connect()
					time.sleep(1.0)
					

				self.sndstate=Sndstate.Waiting_For_MsgToSend
				self.recstate = Recstate.Waiting_For_MsgToReceive
				if self.awake_registername and self.awake_interval:
					# Check if we need to do an awake signal
					if time.time() >= last_awake_time + self.awake_interval:
						self.sndstate = Sndstate.Sending_Msg
						self.recstate = Recstate.Receiving_Msg
						result=self.Modbus_Conn.read(self.awake_registername)
						# Write back to the same register to let the device know we are awake
						self.Modbus_Conn.write(self.awake_registername,result)
						if self.localecho_send_messages:
							self.update_MON_widget(f'Ping awake register: {result}->', style=self.send_style)
						Logger.debug(f'{self.name}-- Awake signal send to {self.awake_registername} register')
						last_awake_time = time.time()
						continue
					
				# get the next send message from the queue
				key, ack_recv, msgtype = self.get_nxtmsg()
				if not key:
					# No message, end of queue
					time.sleep(0.5)
					continue

				self.sndstate = Sndstate.Sending_Msg
				self.recstate = Recstate.Receiving_Msg
				
				result = {}
				try:
					if key.lower() in ['all','readall','read_all','alles', 'all_registers', 'alle_registers']:
						result = self.Modbus_Conn.read_all(sdm_modbus.registerType.INPUT, scaling=True)
						result.update(self.Modbus_Conn.read_all(sdm_modbus.registerType.HOLDING, scaling=True))
						result.update(self.Modbus_Conn.read_all(sdm_modbus.registerType.COIL, scaling=False))
						result.update(self.Modbus_Conn.read_all(sdm_modbus.registerType.DISCR_INPUT, scaling=False))
					elif key.lower() in ['all_inputs', 'input', 'inputs', 'inputregisters', 'input_registers']:
						result = self.Modbus_Conn.read_all(sdm_modbus.registerType.INPUT, scaling=True)
					elif key.lower() in ['all_holdings', 'holdings', 'holding', 'holdingregisters', 'holding_registers']:
						result = self.Modbus_Conn.read_all(sdm_modbus.registerType.HOLDING, scaling=True)
					else:
						result = {key:self.Modbus_Conn.read(key)}
				except ConnectionError:
					raise
				except Exception as err:
					raise err
				
				if self.localecho_send_messages: 
					# print(send_header + sendbytes)
					self.update_MON_widget(f'Poll {key} ->', style=self.send_style)
				if result: 
					self.recv(result)
					self.recstate = Recstate.Deconstructing_Msg
			
		except ConnectionError as err:
			Logger.error(f'{self.name}-- ConnectionError, trying to reconnect.')
			self.disconnect(reconnect=True)
		except Exception as err:
			Logger.exception(f'{self.name}-- exception {err}, disconnecting....')
			self.disconnect(reconnect=False)
		finally:
			self.sndstate=Sndstate.Sender_Stopped
			self.recstate = Recstate.Receiver_Stopped
			

	def get_datapoints_from_msg(self, result_key):
		'''
		result is een resultaat van een Modbus read of read_all... in de vorm van een dictionary (key,value pairs)
		de key zou voor moeten komen in de self.searchkeys dict van deze interface en die zou de DPids moeten bevatten
		van de gekoppelde datapoints
		'''
		try:
			dp_ids=[]
			if result_key in self.searchkeys:
				dp_ids = self.searchkeys[result_key]
			return dp_ids, []
					
		except Exception as err:
			Logger.error(f'{self.name}-- Error getting datapoints from key: {result_key}')
			Logger.exception(str(err)) 
			return [],[] 


		
	def check_msg(self, result_key):
		'''
		Checks if the message is corrupt or not
		Everything should have already been checked by the sdmModbus module
		'''
		return True

	def decode_msg(self, value, dp_ID):
		'''
		Alle noodzakelijke decoding is al gedaan door de sdmModbus module, hier wordt alleen de waarde weggeschreven
		naar het datapoint, in het datapoint datatype
		'''
		try:
			dp:Datapoint =DATAPOINTS_ID[dp_ID]
			if value is not None:
				try:
					nwvalue = dp.datatype(str(value))
					if dp.log_messages: Logger.info(f'Logmessages:{dp.name} : {value} Decoded into {nwvalue}')
					dp.write_INTFC_value(nwvalue = nwvalue)
				except ValueError:
					Logger.info(f'{self.name}--Datapoint: {dp.name}-- Can not convert {value} into {dp.datatype}')
				
		except Exception as err:
			Logger.exception(str(err))

		
	def make_poll_telgr(self, dp):
		# de searchkey wordt gebruikt als poll request_key...
		self.add_msg(dp.searchkey, acknowledge_receipt=False, msgtype=MsgType.PollMessage)
		
	def make_command_telgr(self, dp, nwvalue):
		try:
			# make sure the nwvalue has the correct datatype
			nwvalue = dp.datatype(nwvalue)
			# evt nieuw te ontwikkelen functie..... nwvalue = reverse_calc_rule(dp, nwvalue)
			
			# no need to add the message to the message queue for the send routine, we can directly write to the Modbus_Conn
			self.Modbus_Conn.write(dp.searchkey, nwvalue)
			# # and immediately (after delay) poll to see the result reflected..
			# time.sleep(1.0)
			# self.make_poll_telgr(dp)
		except Exception as err:
			Logger.exception(str(err))
		
	def calc_crc(self,ByteArray):
		# crc is handled by the underlying (sdm)modbus library
		pass



	
class ShellyRelayInterface(BaseInterface):
	def __init__(self, *args, **kwargs):
		# set the interface_type field, as we maybe want to use the name property for more specific names
		self.interface_type = self.__class__.__name__
		self.device_count = kwargs.get('device_count', 3)
		super().__init__(*args, **kwargs)

		self.display_format = "TEXT"
		self.localecho_send_messages = True
		
		self.onconnect_start_receiver=False
		self.onconnect_start_sender=False
		self.onconnect_start_poller=True
		if kwargs.get("auto_start", False): self.connect()

			
	def make_poll_telgr(self, polling_dp):
		# poll the relay state for this datapoint
		try:
			if Is_NOE(polling_dp.st_index): 
				raise Exception(f'Device index should be listed under st_index in dp definition')
			else:
				device_index = polling_dp.st_index
				self.recv(device_index, polling_dp)
		except Exception as err:
			Logger.exception(str(err))
			self.update_MON_widget(f'{self.name}:{polling_dp.name}-- Can not poll_state: {err}', style=self.error_style)

	def make_command_telgr(self, polling_dp, nwvalue):
		try:
			if Is_NOE(polling_dp.st_index): 
				raise ValueError(f'Device index should be listed under st_index in dp definition')
			else:
				device_index = polling_dp.st_index
				# no need to use add_msg queue here, call send directly
				self.send(device_index, nwvalue)
		except ValueError as err:
			Logger.error(str(err))
			self.update_MON_widget(f'{self.name}:{polling_dp.name}-- Can not change state: {err}', style=self.error_style)
		except Exception as err:
			Logger.exception(str(err))
			self.update_MON_widget(f'{self.name}:{polling_dp.name}-- Can not change state: {err}', style=self.error_style)


	def send(self, device_index, nwvalue:bool):
		if ENVIRONMENT not in [Environment.Productie, Environment.Test_full]: return
		
		if self.connstate != ConnState.Connected:
			Logger.error(f'{self.name}-- Trying to call receive while not connected, first connect!')
			return
		
		self.sndstate = Sndstate.Sending_Msg
		device_type = self.Shelly.devices[device_index].device_type.upper()
		if device_type == 'RELAY':
			if nwvalue:
				self.Shelly.devices[device_index].turn_on()
			else:
				self.Shelly.devices[device_index].turn_off()
				
			if self.localecho_send_messages:
				self.update_MON_widget(
					f'Device {device_index}--{self.conn_type}-{self.address}:{self.port}, type {device_type}, switched to {"ON" if nwvalue else "OFF"}. ',
					style=self.send_style)

		time.sleep(0.2)
		self.sndstate = Sndstate.Waiting_For_MsgToSend
	
	
	def recv(self, device_index, polling_dp):
		if ENVIRONMENT not in [Environment.Productie, Environment.Test_full]: return
		
		if self.connstate != ConnState.Connected:
			Logger.error(f'{self.name}-- Trying to call receive while not connected, first connect!')
			return
		
		self.recstate = Recstate.Receiving_Msg
		device_type = self.Shelly.devices[device_index].device_type.upper()
		if device_type in ['RELAY', 'SWITCH']:
			state = int(self.Shelly.devices[device_index].state)
			polling_dp.value = state
			self.update_MON_widget(
				f'Device {device_index}--{self.conn_type}-{self.address}:{self.port}, type {device_type}, state {state}. ',
				style=self.dp_style)
		time.sleep(0.2)
		self.recstate = Recstate.Waiting_For_MsgToReceive

		
		
class MbusInterface(BaseInterface):
	def __init__(self, *args, **kwargs):
		# set the interface_type field, as we maybe want to use the name property for more specific names
		self.interface_type = self.__class__.__name__
		super().__init__(*args, **kwargs)
		'''
		sync_hex         - geeft in HEX het byte aan dat het EINDE van een message aangeeft, na ontvangst gaat de ontvanger over tot decoden
		busfree_hex      - geeft in HEX het byte wat aangeeft dat de bus VRIJ is om te gebruiken, of leeg voor bussen die dit niet gebruiken
		min_busfreebytes_count - geeft in INT het minimale aantal busfree bytes dat achter elkaar gezien moet zijn VOORDAT de interface op de bus gaat..
		stx_hex          - geeft in HEX het byte aan waarmee een message START, de ontvanger wordt getriggerd om te luisteren
		fixed_msg_length - geeft (als hij niet None is) aan hoe lang een messageblok is, de ontvanger zal na dit aantal overgaan tot decoden
		ack_hex          - is een bytearray die door de ontvanger gezonden kan worden om te bevestigen dat de boodschap ontvangen is.
		cmd_ack_hex      - is een bytearray die specifiek bedoeld is om COMMANDOS te bevestigen, deze wordt door de ontvanger verstuurd na het ontavngen 
		localecho_send_messages  - geeft aan of VERZONDEN messages zoals POLLS en COMMANDS locaal in de interfacemonitor ge-echo'd moeten worden
		'''
		# self.sync_hex = ""
		self.bus_free = bytearray([])
		# self.ack_hex = ""
		# self.cmd_ack_hex = ""
		
		# self.min_busfreebytes_count = 1
		# self.stx_hex = "68"
		self.fixed_msg_length = 167
		self.localecho_send_messages = True
		
		'''
		de index en de lengte van de SEARCHKEY (sk) gelden normaal vanaf DE START van de ontvangen message
		als sk_indicator is opgegeven dan is index t.o.v. deze indicator (positief of negatief), bij geen index is deze 1
		als sk_terminator is opgegeven dan overruled deze de fixed length
		als er EN geen terminator EN geen length is opgegeven dan wordt er REVERSE gefit. 
		(dan worden alle keys over de message gelegd vanaf de index om een fit te vinden.
		index defaults to 0,
		'''
		self.key_format="HEX"
		self.sk_index = 0
		# self.sk_length = 7
		# self.sk_terminator_hex = ""
		# self.sk_indicator_hex = ""
		self.sk_format = SearchkeyFormat.HEXstring

		# special telegram lines
		# self.headerkey_hex = ""
		# self.crckey_hex = ""
		
		self.display_format = "HEX"
		
		self.onconnect_start_receiver=True
		self.onconnect_start_sender=False
		self.onconnect_start_poller=True
		if kwargs.get("auto_start", False): self.connect()



	def send(self):
		# Trying to send something while not connected?...
		if self.connstate != ConnState.Connected:
			Logger.error(f'{self.name}-- Trying to call send while not connected, first connect!')
			return
		
		sendbytes, ack_recv, msgtype = self.get_nxtmsg()
		try:
			self.sndstate=Sndstate.Sending_Msg
			if self.conn_type == "MBUS-TCP":
				try:
					self.TCPclientSock.send(sendbytes)
				except Exception as err:
					raise ConnectionError
			elif self.conn_type == "MBUS-UDP":
				try:
					self.UDPclientSock.sendto(sendbytes, (self.address,self.port))
				except Exception as err:
					raise ConnectionError
				
			if self.localecho_send_messages: self.update_MON_widget(sendbytes, style=self.send_style)
			time.sleep(0.05) 			# always wait a little after detecting an empty buffer before resuming socket reads....
		except ConnectionError:
			# transmission failed: push message back into the queue
			self.add_msg(sendbytes, acknowledge_receipt=ack_recv, msgtype=msgtype)
		except Exception as err:
			Logger.exception(str(err))
		finally:
			self.sndstate=Sndstate.Waiting_For_MsgToSend

		
	def recv(self):
		if ENVIRONMENT not in [Environment.Productie, Environment.Test_full]: return
		
		if self.connstate != ConnState.Connected:
			Logger.error(f'{self.name}-- Trying to call receive while not connected, first connect!')
			return
			
		self.stop_receiving = False
		TCP_BUFFER_SIZE = 1024
		UDP_BUFFER_SIZE = 4096
		data = ""
		try:
			# print(conn_type)
			if self.conn_type == "MBUS-TCP": self.TCPclientSock.setblocking(False)
			if self.conn_type == "MBUS-UDP": self.UDPclientSock.setblocking(False)
				
			recvbytes = bytearray()

			while not self.stop_receiving:
				try:
					# print ("Recv loop")
					if self.conn_type == "MBUS-TCP":
						data = self.TCPclientSock.recv(TCP_BUFFER_SIZE)
					if self.conn_type == "MBUS-UDP":
						data, addr = self.UDPclientSock.recvfrom(UDP_BUFFER_SIZE)
					# print ('data = %s' % data)
					self.recstate=Recstate.Receiving_Msg
					for recvbyte in data:
						# plak achter recvbytes
						recvbytes = recvbytes +  bytearray([recvbyte])
						# Check if we reached the fixed message length
						if len(recvbytes)==self.fixed_msg_length:
							# some messages need pre-processing, implement in specific interface classes
							msgbytes = self.pre_process_message(recvbytes)
							# see if this message can be related to a datapoint
							dp_IDs, sk_indexes = self.get_datapoints_from_msg(msgbytes)
							if dp_IDs != []:
								self.recstate=Recstate.Deconstructing_Msg
								# we found at least one datapoint connected to this message
								self.update_MON_widget(recvbytes, style=self.dp_style)
								# Check if we need to log the messages for these datapoints for testing purposes
								for dp_ID in dp_IDs:
									dp=DATAPOINTS_ID[dp_ID]
									if dp.log_messages: Logger.info("%s: %s--bytes received: %s" % (self.name, dp.name, ByteArrayToHexString(recvbytes)))
								# now check if the message is corrupt or not
								if self.check_msg(msgbytes):
									for dp_ID in dp_IDs: self.decode_msg(msgbytes, dp_ID, sk_indexes)
								else:
									# Logger.error ("Corrupt message or datapoint definition? " + ByteArrayToHexString(msgbytes))
									pass
							else:
								# No datapoint found, this message is unknown to us
								self.update_MON_widget(recvbytes, style=self.unknown_style)
								
							# RESET the message bytearray
							recvbytes=bytearray()
						else:
							# de message is nog niet volledig binnen...blijf luisteren
							pass
							
				except ConnectionError as err:
					Logger.exception ("ConnectionError in " + self.name + " receiver: " + str(err))
					self.disconnect(reconnect=True)
					return
				except IOError as err:
					# print('IOerror', err)
					if err.errno == 11:
						# 11 is "resource temporarily unavailable" when reading in a non-blocking manner from an empty buffer....
						self.recstate=Recstate.Waiting_For_MsgToReceive
						if self.msgQ: self.send()
						# always wait a little after detecting an empty buffer before resuming socket reads....
						time.sleep(0.05) 
					else:
						Logger.error ("IOError in " + self.name + " receiver: " + str(err))
						self.disconnect(reconnect=False)
						break
				except Exception as err:
					Logger.exception ("General exception in " + self.name + " receiver: " + str(err))
					self.disconnect(reconnect=False)
					break
					
			# if we ever arrive here.... a disconnect has been requested...
			self.recstate=Recstate.Receiver_Stopped
			self.connstate=ConnState.DisConnecting
		except Exception as err:
			Logger.exception ("General Exception for Interface  " + self.name + ": " + str(err))


	def get_datapoints_from_msg(self, BA_msg):
		# Messagestring is still a bytearray here!
		try:
			# de start van de searchkey waarmee de datapoint geidentificeerd kan worden kan gevonden worden door een INDEX
			start_index = self.sk_index
			# we kunnen geen end_index bepalen vanwege wisselende keystring lengtes, dus -> reverse_fitting doen')
			dp_ids=[]
			for key in self.searchkeys:
				if self.sk_format == SearchkeyFormat.HEXstring: keybytes = bytearray.fromhex(key)
				elif self.sk_format == SearchkeyFormat.ASCII: keybytes = bytearray(key.encode())
				if BA_msg.find(keybytes) == start_index:
					dp_ids = self.searchkeys[key]
					end_index = start_index + len(keybytes)
					# print ("RevFit: Datapoints found", dp_ids)
					return dp_ids,[start_index,end_index]
					
			# als we hier terecht komen -> geen fit gevonden
			return [],[]
					
		except Exception as err:
			Logger.error(f'{self.name}-- Error getting datapoint from msg: {BA_msg} - HEX = {ByteArrayToHexString(BA_msg)}')
			Logger.exception(str(err)) 
			return [],[] 

	def decode_msg(self, BA_msg, dp_ID, sk_indexes):
		# de binnenkomende message is hier nog steed een bytearray....
		dp = None
		try:
			dp=DATAPOINTS_ID[dp_ID]
			# print ("Handling datapoint ", dp.name)
			
			end_index = sk_indexes[1]
			BA_datapart = BA_msg[end_index:]
			# print ("sk end_index:", end_index)
			# databytes is the bytearray left over after removal of the key, the key terminator is still there!!!
			# print ("messagebytes: ", ByteArrayToHexString(BA_msg))
			# print ("databytes: " + ByteArrayToHexString(BA_datapart))
			
			
			start_index=-1
			end_index=-1
			startkey = HexStringToByteArray(dp.startkey_hex) if IsNot_NOE(dp.startkey_hex) else None
			stopkey = HexStringToByteArray(dp.stopkey_hex) if IsNot_NOE(dp.stopkey_hex) else None
			# extract the data from the remaining message
			if startkey!=None: start_index=BA_datapart.find(startkey) + len(startkey) + (0 if dp.st_index == None else dp.st_index)
			else: start_index = (0 if dp.st_index==None else dp.st_index)
			if start_index==-1: 
				raise Exception ("Can not retrieve data from message, no data start_index")
			# print ("data_startindex = " + str(start_index))

			if stopkey!=None: end_index=BA_datapart.find(stopkey) 
			else: end_index = len(BA_datapart) if dp.length==None else (start_index + dp.length)
			if end_index==-1: 
				raise Exception ("Can not retrieve data from message, no data end_index.")
				return
			# print ("data endindex = " + str(end_index))
			BA_databytes = BA_datapart[start_index:end_index]
			if len(BA_databytes) == 0: return
			
			decoder = dp.datadecoder.strip() if IsNot_NOE(dp.datadecoder) else "ASCII"
			
			# print("data send to the datadecoder: " + ByteArrayToHexString(BA_databytes))
			result = From_ByteArray_converter(decoder, BA_databytes)
			# print(dp.name + "data received from datadecoder: " + str(result))
			# force result into the correct datatype
			if result != None:
				dp.write_INTFC_value(nwvalue=dp.datatype(str(result))) 
				# dp.value =  dp.datatype(str(result))
				# print (dp.name + ":" + str(dp.value))
			else:
				raise Exception("Decoding error, From_ByteArray_converter " + decoder + " returned None from databytes " + str(BA_databytes))
				
		except Exception as err:
			Logger.error(self.name + "--" + str(err))
			Logger.error(self.name + "--Error decoding message: " + str(BA_msg) + ", HEX = " + ByteArrayToHexString(BA_msg))
			Logger.exception(str(err))



	def make_poll_telgr(self,polldef):
		# 10 CM RA CD SY
		# -- 10 start
		# -- CM Command, 5B = request status, RA Receive address, CD Crc over CM RA, SY Sync
		rec_addr = polldef.searchkey.strip()[15:17]
		# aantalbytes = len(polldef.command.strip().split(" "))
		sndmessage = "5B " + rec_addr
		crcbytes = bytearray.fromhex(sndmessage)
		sndmessage = "10 " + sndmessage + " " + ByteArrayToHexString(self.calc_crc(crcbytes)) + " " + "16"
		# print(f'{self.name}--Poll message prepared: {sndmessage}')
		sndbytes = bytearray.fromhex(sndmessage)
		# add the message to the message queue for the send routine, but only if it is not None (empty)
		self.add_msg(sndbytes, acknowledge_receipt=False, msgtype=MsgType.PollMessage)
		
	def make_command_telgr(self, definition):
		pass
		
	def calc_crc(self,ByteArray):
		tmpsum = 0x0000         # force an Unsigned INT16 into tmpsum
		for i in range(len(ByteArray)):
			tmpsum = tmpsum + ByteArray[i]
		# % is the modulo operator, it results in the remainder after dividing the left through the right variable, i.e. 7 % 2 = 1
		tmpsum =tmpsum % 256 
		return bytearray([tmpsum])
			


class ESMR50Interface(BaseInterface):
	def __init__(self, *args, **kwargs):
		# set the interface_type field, as we maybe want to use the name property for more specific names
		self.interface_type = self.__class__.__name__
		super().__init__(*args, **kwargs)

		self.sk_format = SearchkeyFormat.ASCII		# Format the searchkey is written in
		self.sk_index = 0							# Search_key startindex in the receive string
		self.localecho_send_messages = False		# Need to echo send messages to the monitor...
		self.display_format = "ASCII"				# display definition for live comm monitor
		
		self.onconnect_start_receiver=True
		self.onconnect_start_sender=False
		self.onconnect_start_poller=False
		if kwargs.get("auto_start", False): self.connect()

		
	def pre_process_message(self, BA_msg):
		# BA_msg is still a bytearray here!
		# The ESMR interface sometimes sends a \x00, ignore that, remove them
		# every line in an ESMR telegram is terminated by a \r\n (\x0D en \x0A), ne need to remove those
		# result=BA_msg.replace(b"\x0d",b'')
		# result=result.replace(b"\x0a",b'')
		result=BA_msg.replace(b'\x00',b'')
		return result


	def recv(self):
		'''
		Specifiek een kleine receiver voor ESMR, alleen voor serieel, niet UDP of TCP op dit moment
		'''
		if ENVIRONMENT not in [Environment.Productie, Environment.Test_full]: return
		
		if self.connstate != ConnState.Connected:
			Logger.error(f'{self.name}-- Trying to call receive while not connected, first connect!')
			return
		
		try:
			# clean the buffer before we start
			self.Ser.flushInput()
			self.stop_receiving=False
			while not self.stop_receiving:
				self.recstate=Recstate.Waiting_For_MsgToReceive
				
				data = self.Ser.readline() # data is van <class Bytes>
				if data is None: continue
				
				# print(self.Ser.in_waiting,":",data)
				if data[0:1] == b'!':
					# last line starts with a ! followed by the checksum...
					# print ("end reached")
					self.recstate=Recstate.Waiting_For_MsgToReceive
					self.Ser.close()
					# Sleep for 1 seconds before re-opening the connection...
					time.sleep(1.0)
					self.Ser.open()
					continue
					
				self.recstate=Recstate.Receiving_Msg
				# some messages need pre-processing, implement in specific interface classes
				msgbytes = self.pre_process_message(data)
				# see if this message can be related to a datapoint
				dp_IDs, sk_indexes = self.get_datapoints_from_msg(msgbytes)
				if dp_IDs != []:
					self.recstate=Recstate.Deconstructing_Msg
					# we found at least one datapoint connected to this message
					self.update_MON_widget(data, style=self.dp_style)
					for dp_ID in dp_IDs:
						dp=DATAPOINTS_ID[dp_ID]
						# Check if we need to log the messages for these datapoints for testing purposes
						if dp.log_messages: Logger.info("%s: %s--bytes received: %s" % (self.name, dp.name, ByteArrayToHexString(data)))
						self.decode_msg(msgbytes, dp_ID, sk_indexes)
				else:
					# No datapoint found, this message is unknown to us
					self.update_MON_widget(data, style=self.unknown_style)
					
		except ConnectionError as err:
			Logger.exception ("ConnectionError in " + self.name + " receiver: " + str(err))
			self.disconnect(reconnect=True)
		except Exception as err:
			Logger.exception ("%s--General Exception: %s" % (self.name,err))
			self.disconnect(reconnect=False)
		finally:
			# if we ever arrive here.... a disconnect has been requested...
			self.recstate=Recstate.Receiver_Stopped





	def get_datapoints_from_msg(self, BA_msg):
		# Messagestring is still a bytearray here!
		try:
			# de start van de searchkey waarmee de datapoint geidentificeerd kan worden kan gevonden worden door een INDEX
			start_index = self.sk_index
			# we kunnen geen end_index bepalen vanwege wisselende keystring lengtes, dus -> reverse_fitting doen')
			dp_ids=[]
			for key in self.searchkeys:
				if self.sk_format == SearchkeyFormat.HEXstring: keybytes = bytearray.fromhex(key)
				elif self.sk_format == SearchkeyFormat.ASCII: keybytes = bytearray(key.encode())
				if BA_msg.find(keybytes) == start_index:
					dp_ids = self.searchkeys[key]
					end_index = start_index + len(keybytes)
					# print ("RevFit: Datapoints found", dp_ids)
					return dp_ids,[start_index,end_index]
					
			# als we hier terecht komen -> geen fit gevonden
			return [],[]
					
		except Exception as err:
			Logger.error(f'{self.name}-- Error getting datapoint from msg: {BA_msg} - HEX = {ByteArrayToHexString(BA_msg)}')
			Logger.exception(str(err)) 
			return [],[] 


	def decode_msg(self, BA_msg, dp_ID, sk_indexes):
		# de binnenkomende message is hier nog steed de complete bytearray....
		dp = None
		try:
			dp=DATAPOINTS_ID[dp_ID]
			# print ("Handling datapoint ", dp.name)
			if len(BA_msg) == 0: return
			# omdat alles in deze interface in ASCII gaat converteren we de BA_msg bytearray eerst maar eens naar een ASCII string
			STR_msg = str(BA_msg, "utf-8")
			# om het juiste datapoint te vinden moeten we de searchkey isoleren
			
			BA_databytes = None
			result=re.finditer('\\(.+?\\)',STR_msg)
			for match in result:
				# ieder dataelement zit tussen 1 haakje en een haakje: 1-0:32.7.0(220.1*V)
				# er zijn ook een aantal data elementen die meer dan 1 set haakjes bevatten: 0-1:24.2.1(101209112500W)(12785.123*m3)
				# wij implementeren hier (voor nu) alleen de eerste waarde tussen ( en ) waar een * in voorkomt
				# # check if this is last one
				# if match.span()[1]==len(STR_msg):
					# # remove brackets and strip unit from datapart
					# data_str = match.group().replace('(','').replace(')','').split('*')[0]
					# BA_databytes = bytearray(data_str.encode('utf-8'))
					# # we have our valuedata, 
					# break
					# check if * character is present
					if '*' in match.group():
						# remove brackets and strip unit from datapart
						data_str = match.group().replace('(','').replace(')','').split('*')[0]
						BA_databytes = bytearray(data_str.encode('utf-8'))
						# we have our valuedata, 
						break
					

			if BA_databytes is None:
				Logger.error("%s--Resetting interface. Error decoding, unable to isolate data: %s" % (self.name, BA_msg))
				self.disconnect(reconnect=True)
				return

			decoder = dp.datadecoder.strip() if IsNot_NOE(dp.datadecoder) else "ASCII"
			
			# print("data send to the datadecoder: " + ByteArrayToHexString(BA_databytes))
			result = From_ByteArray_converter(decoder, BA_databytes)
			# print(dp.name + "data received from datadecoder: " + str(result))
			# force result into the correct datatype
			if result is None:
				Logger.error("%s--Resetting interface. Error decoding, from_ByteArray_converter %s returned None from databytes %s." % (self.name, decoder, BA_databytes))
				self.disconnect(reconnect=True)
				return
			
			try:
				dp.write_INTFC_value(nwvalue=dp.datatype(str(result))) 
				# print (dp.name + ":" + str(dp.value))
			except Exception as err:
				Logger.error("%s--Resetting interface. Unable to convert %s to %s" % (self.name, result, dp.datatype))
				self.disconnect(reconnect=True)
				return
		except Exception as err:
			Logger.exception(str(err))
			
class ESMR50_via_TCP(ESMR50Interface):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def recv(self):
		'''
		Specifiek een kleine receiver serieel over TCP
		'''
		s = self.TCPclientSock
		msgbytes = b''
		self.stop_receiving = False
		try:
			while not self.stop_receiving:
				self.recstate=Recstate.Waiting_For_MsgToReceive
				packet = s.recv(1024)
				if not packet: break
				lines = packet.split(b'\n')
				
				if len(lines) == 1:
					msgbytes += packet			# no \n encountered yet... add to buffer
					continue

				while len(lines) > 1:
					msgbytes += lines[0]
					msgbytes = msgbytes.strip(b'\r')
					
					if len(msgbytes) == 0:
						pass
					else:
						# print(msgbytes.decode('utf-8'))
						self.recstate = Recstate.Receiving_Msg
						# some messages need pre-processing, implement in specific interface classes
						msgbytes = self.pre_process_message(msgbytes)
						# see if this message can be related to a datapoint
						dp_IDs, sk_indexes = self.get_datapoints_from_msg(msgbytes)
						if dp_IDs != []:
							# we found at least one datapoint connected to this message
							self.update_MON_widget(msgbytes, style=self.dp_style)
							for dp_ID in dp_IDs:
								self.decode_msg(msgbytes, dp_ID, sk_indexes)
						else:
							# No datapoint found, this message is unknown to us
							self.update_MON_widget(msgbytes, style=self.unknown_style)
						
					msgbytes = b''
					lines.pop(0)
				# store whatever remains in the buffer for the next time
				msgbytes = lines[0]
		except Exception as err:
			Logger.exception(str(err))
			
