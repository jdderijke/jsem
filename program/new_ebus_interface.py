#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  new_ebus_interface.py
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

class EbusInterface(BaseInterface):
	def __init__(self, *args, **kwargs):
		# set the interface_type field, as we maybe want to use the name property for more specific names
		self.interface_type = self.__class__.__name__
		'''
		'''
		self.bus_free = bytearray(b'\xAA')
		self.ack_msg = bytearray(b'\x00')
		self.bus_free_count = 2				# minimal number of bus_free bytes BEFORE a message will be send by this interface

		self.description = "ebus warmtepomp in schuur"
		super().__init__(*args, **kwargs)


	def connect(self):
		address = self.address.strip().upper()
		conn_type = self.conn_type.strip().upper()
		port = self.port
		maxretries = self.maxretries
		timeout = self.timeout
		try:
			if self.connstate != ConnState.DisConnected:
				Logger.error ("Can not connect Interface " + self.name + ": already connected to " + 
								  address + " via " + self.conn_type + "!")
								  
			
			if conn_type == "TCP":
				tries = 1
				BUFFER_SIZE = 1024    # Normally 1024
				while tries <= maxretries:
					try:
						self.connstate = ConnState.Connecting
						self.TCPclientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						self.TCPclientSock.settimeout(timeout)
						self.TCPclientSock.connect((address, port))
						self.connstate = ConnState.Connected
						# print ("TCP connected")
						# define a new listening thread and start it
						self.async_recv = threading.Thread(target=self.recv) 
						# have the receiver run as daemon thread....
						self.async_recv.daemon = True
						self.async_recv.start()  
				
						self.recstate=Recstate.Waiting_For_MsgToReceive
						self.sndstate=Sndstate.Waiting_For_MsgToSend
						self.start_polling()
						break
					except Exception as err:
						Logger.error ("Problem connecting interface " + self.name + " to " + address + 
								   ":" + str(port) + " via " + conn_type + ", attempt:" + str(tries) + " - " + str(err))
						tries +=1
						time.sleep(0.5)
						
			elif conn_type == "UDP":
				tries = 1
				BUFFER_SIZE = 4096
				while tries <= maxretries:
					try:                
						self.connstate = ConnState.Connecting
						# declare our serverSocket upon which
						# we will be listening for UDP messages
						self.UDPclientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
						# One difference is that we will have to bind our declared IP address
						# and port number to our newly declared serverSock
						# If NO ip address is given: listen to the specified port on all interfaces
						# If an ip adress is given it must be the ip address of the RECEIVER, not de sender
						# i.e. my ip_address 
						self.UDPclientSock.bind((get_ip_address(), port))
						# self.UDPclientSock.bind(('', port))

						self.connstate = ConnState.Connected
						# define a new listening thread and start it
						self.async_recv = threading.Thread(target=self.recv) 
						self.async_recv.daemon = True
						self.async_recv.start() 
										 
						self.recstate=Recstate.Waiting_For_MsgToReceive
						self.sndstate=Sndstate.Waiting_For_MsgToSend

						self.start_polling()
						break
					except Exception as err:
						Logger.error ("Problem connecting interface " + self.name + " to " + address + 
								   ":" + str(port) + " via " + conn_type + ", attempt:" + str(tries) + " - " + str(err))
						tries+=1
						time.sleep(0.5)
						
					
			if self.connstate != ConnState.Connected:
				self.connstate = ConnState.DisConnected  
				self.disconnect()          
				Logger.error("Connecting Interface " + self.name + " FAILED!!!")
			else:
				Logger.info("Interface " + self.name + " connected via " + address + ":" + str(port) + ", protocol: " + conn_type)
		except Exception as err:
			Logger.exception(str(err))
		
		
		
	def disconnect(self, reconnect=False):
		address = self.address.strip().upper()
		conn_type = self.conn_type.strip().upper()
		port = self.port
		self.connstate=ConnState.DisConnecting
		try:
			# Stop any polling still going on
			self.stop_polling()
			self.stop_receiving = True
			self.stop_sending = True
			
			# give receiver thread the chance to suspend operation and indicate receiver has stopped
			if self.recv_thread is not None and self.recv_thread != threading.get_ident():
				# de receive routine loopt waarschijnlijk nog gewoon...
				# wait untill the daemon thread has finished
				try:
					self.async_recv.join()
					# while self.async_recv.isAlive(): pass
				except Exception as err:
					pass
			self.recstate=Recstate.Receiver_Stopped
				
			# give sender thread the chance to suspend operation and indicate sender has stopped
			if self.send_thread is not None and self.send_thread != threading.get_ident():
				# de sender routine loopt waarschijnlijk nog gewoon...
				# wait untill the daemon thread has finished
				try:
					self.async_send.join()
				except Exception as err:
					pass
			self.sndstate=Sndstate.Sender_Stopped
			
			# empty the send_msgQ
			while True:
				msg,_,_ = self.get_nxtmsg()
				if msg is None: break
				
			# close connection socket
			try:
				if conn_type == "TCP":
					# shutdown forces all processes to disconnect from the socket and sends an EOF to the peer, but you still need to close the socket
					self.TCPclientSock.shutdown(socket.SHUT_RDWR)
					self.TCPclientSock.close()
					self.TCPclientSock=None
				elif conn_type == "UDP":
					self.UDPclientSock.close()
					self.UDPclientSock=None
				Logger.info ("Interface " + self.name + " on " + address + ":" + str(port) + " disconnected")
			except Exception as err:
				# Something went wrong while closing the sockets
				pass
			finally:
				self.connstate=ConnState.DisConnected
		except Exception as err:
			Logger.exception(str(err))
		finally:
			if reconnect:
				# Wait 1 second before reconnecting
				time.sleep(1)
				self.connect()

	def send(self, ByteArray):
		BUFFER_SIZE = 1
		try:
			self.sndstate=Sndstate.Sending_Msg
			conn_type = self.conn_type.strip().upper()
			address = self.address.strip().upper()
			port = self.port
			
			while True:
				# Zet het eerste byte op de bus....
				if conn_type == "TCP":
					# print ("TCP message send: " + ByteArrayToHexString(ByteArray))
					self.TCPclientSock.send(ByteArray[0:1])
					data = self.TCPclientSock.recv(BUFFER_SIZE)
					print(bytearray([data]), ByteArray[0:1])
					if bytearray([data]) != ByteArray[0:1]:
						# transmission failed: push message back into the queue
						return False
					else:
						# I have the bus... send rest of message
						self.TCPclientSock.send(ByteArray[1:])
						return True
						
				elif conn_type == "UDP":
					# print("UDP message:", ByteArrayToHexString(ByteArray))
					self.UDPclientSock.sendto(ByteArray[0:1], (address,port))
					data, addr = self.UDPclientSock.recvfrom(BUFFER_SIZE)
					if bytearray([data]) != ByteArray[0:1]:
						# transmission failed: push message back into the queue
						return False
					else:
						# I have the bus... send rest of message
						self.UDPclientSock.sendto(ByteArray[1:], (address,port))
						return True
		except Exception as err:
			Logger.exception(str(err))
			return False
		finally:
			self.sndstate=Sndstate.Waiting_For_MsgToSend


	def recv(self):
		BUFFER_SIZE = 1    # Normally 1024
		
		self.recv_thread = threading.get_ident()
		try:
			self.stop_receiving=False
				
			recvbytes = bytearray()
			# create a buffer (length bus_free_count) that holds the last number of received bytes, 
			lastbytes = bytearray(b'\x00') * self.bus_free_count
			
			# we are ready to enter the receive loop
			self.recstate=Recstate.Waiting_For_MsgToReceive
			self.sndstate=Sndstate.Waiting_For_MsgToSend
	
			while not self.stop_receiving:
				try:
					# print ("Recv loop")
					self.recstate=Recstate.Receiving_Msg
					if conn_type == "TCP": 
						data = self.TCPclientSock.recv(BUFFER_SIZE)
					if conn_type == "UDP": 
						data, addr = self.UDPclientSock.recvfrom(BUFFER_SIZE)
					# print ('data = %s' % data)
					if len(data) != BUFFER_SIZE: Logger.error(f'{self.name}-Received more bytes then the BUFFER_SIZE')
					for recvbyte in data:
						# we scan every single byte.....
						BA_byte = bytearray([recvbyte])
						# remember last bytes
						lastbytes = lastbytes[1:] + BA_byte
						if BA_byte==bus_free and len(recvbytes)==0:
							# skip busfree bytes, but check if the bus is free for us
							if all(x==ord(b'\xAA') for x in lastbytes):
								# bus is free, see if we need to send something
								sendmsg, acknowledge_receipt, msgtype = self.get_nxtmsg()
								if sendmsg is not None:
									# if sending the message fails, put it back in the queue 
									if not self.send(sendmsg): self.add_msg(sendmsg, acknowledge_receipt=acknowledge_receipt, msgtype=msgtype)
										 
							self.update_MON_widget(BA_busfree, style=self.idle_style)
						elif BA_byte!=bus_free:
							# plak net zolang bytes (niet zijnde bus_free) achter recvbytes totdat de bus_free langskomt....
							# (the last byte in a message transmission)
							recvbytes = recvbytes + BA_byte
						elif BA_byte==bus_free and len(recvbytes)!=0:
							# het laatste byte was inderdaad een bus_free, een message terminator...
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
									if self.check_msg(msgbytes): self.decode_msg(msgbytes, dp_ID, sk_indexes)
									else: Logger.error ("Corrupt message or datapoint definition? " + ByteArrayToHexString(msgbytes))
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
					Logger.error ("IOError in " + self.name + " receiver: " + str(err))
					self.disconnect(reconnect=False)
					break
				except Exception as err:
					Logger.exception ("General exception in " + self.name + " receiver: " + str(err))
					self.disconnect(reconnect=False)
					break
					
		except Exception as err:
			Logger.exception ("General Exception for Interface  " + self.name + ": " + str(err))
		finally:
			# if we ever arrive here.... a disconnect has been requested...
			self.recstate=Recstate.Receiver_Stopped
			self.connstate=ConnState.DisConnecting



		
	def pre_process_message(self, msgbytes):
		# Messagestring is still a bytearray here!
		# For the EBUS interface specific...we need to replace A9 00 and A9 01 sequences 
		# by A9 and AA respectively, BEFORE we do ANY further processing!
		# print (messagestring)
		# wait=input("any key")
		result=msgbytes.replace(b"\xA9\x01",b"\xAA")
		result=result.replace(b"\xA9\x00",b"\xA9")
		return result

	def check_msg(self, BA_msg):
		'''
		Check if message is not corrupt, returns FALSE if message is corrupt.
		'''
		try:
			# Last byte MUST be a bus_free byte
			if not BA_msg[-1:]==self.bus_free:
				return False
			# remove the bus_free byte
			BA_msg=BA_msg[:-1]
	
			# All messages have a sender part, with a checksum
			# aantal_s_databytes = int.from_bytes(BA_msg[4], byteorder="little")
			# addressing or slicing a bytearray object on 1 index, results in an INTEGER, not a byte!!
			aantal_s_databytes = BA_msg[4]
			s_crc_index = 4 + aantal_s_databytes + 1
			s_crc = self.calc_crc(BA_msg[0:s_crc_index])
			if s_crc != BA_msg[s_crc_index:s_crc_index+1]:
				# Logger.error ("Checksum error in de send part of the message: " + ByteArrayToHexString(BA_msg))
				# Logger.error ("Aantal_s_databytes: %s  - s_crc_index: %s - crc should be: %s - and is: %s " 
							  # % (aantal_s_databytes, s_crc_index, s_crc, BA_msg[s_crc_index:s_crc_index+1]))
				return False
				
			# If the message is longer than the sender checksum then an answer part was attached 
			if len(BA_msg) > s_crc_index + 1:
				# it is possible that an ACK is inserted by the receiver
				if BA_msg[s_crc_index+1:s_crc_index+2]==bytes.fromhex(self.ack_hex):
					# aantal_a_databytes = int.from_bytes(BA_msg[s_crc_index+2])
					aantal_a_databytes = BA_msg[s_crc_index+2]
					a_crc_index = (s_crc_index+2) + aantal_a_databytes + 1
					a_crc = self.calc_crc(BA_msg[(s_crc_index+2):a_crc_index])
				else:
					# aantal_a_databytes = int.from_bytes(BA_msg[s_crc_index+1])
					aantal_a_databytes = BA_msg[s_crc_index+1]
					a_crc_index = (s_crc_index+1) + aantal_a_databytes + 1
					a_crc = self.calc_crc(BA_msg[(s_crc_index+1):a_crc_index])
				if a_crc != BA_msg[a_crc_index:a_crc_index+1]:
					# Checksum error in the answer part of the message
					# Logger.error ("Checksum error in de answer part of the message: " + ByteArrayToHexString(BA_msg))
					# Logger.error ("Aantal_a_databytes: %s - a_crc_index: %s - crc should be: %s - and is: %s "
								  # % (aantal_a_databytes, a_crc_index, a_crc, BA_msg[a_crc_index:a_crc_index+1]))
					return False
					
			return True
		except Exception as err:
			# Waarschijnlijk een index out of range, dat krijg je bij een afgebroken message....
			# geen foutlogging nodig hiervoor
			# print ("Error checking message: " + str(BA_msg) + ", HEX = " + ByteArrayToHexString(BA_msg))
			# print (str(err))
			return False


	def decode_msg(self, BA_msg, dp_ID, sk_indexes):
		# de binnenkomende message is hier nog steed een bytearray....
		try:
			dp=DATAPOINTS_ID[dp_ID]
			if not dp.enabled: return
			
			if dp.st_index == None or dp.length == None or Is_NOE(dp.startkey_hex):
				raise Exception ("Datapoint " + str(dp.ID) + dp.name + " has NO startkey, st_index and/or length defined, cant retrieve data....")
			# isolate the data from the message
			if dp.startkey_hex.upper()=="SND":
				# The startkey refers to the SEND part of the message
				# every message format starts with SS RR C1 C2 ND DD DD DD ..... CS
				# so databytes in the send part always start on index 5
				startpunt=5
			elif dp.startkey_hex.upper()=="RES":
				# The startkey refers to the RESPONSE part of the message
				nd = BA_msg[4]
				# sometimes there is an acknowlegde receipt after de CrC of the send side
				ack = 4 + nd + 1 + 1
				if BA_msg[ack:ack+1]==bytes.fromhex(self.ack_hex):
					# print ("ack found on the send side: " + ByteArrayToHexString(BA_msg))
					# yes there is an ACK, after that is the ND of the response (so on ack+1), and after that the first response databyte (ack+1+1)
					startpunt=ack+1+1
				else:
					# NO, there is NO ack, so the ND of the response in on this position, and after that the first response databyte (ack+1)
					startpunt=ack+1
			else:
				raise Exception("Illegal phrase in startkey: " + dp.startkey_hex + ", must be SND or RES tom indicate the SEND or RESPONSE part of the message.")
			
			
			# print (dp.name)
			# print (ByteArrayToHexString(BA_msg))
			
			BA_databytes = BA_msg[(startpunt+dp.st_index):(startpunt+dp.st_index+dp.length)]

			# print (ByteArrayToHexString(BA_databytes))
			# wait = input("any key")
			
			
			decoder = dp.datadecoder.strip() if IsNot_NOE(dp.datadecoder) else "ASCII"

			if dp.log_messages: Logger.info("%s: %s--data send to the %s datadecoder: %s" % (self.name, dp.name, decoder, ByteArrayToHexString(BA_databytes)))
			result = From_ByteArray_converter(decoder, BA_databytes)
			# print(dp.name + "data received from datadecoder: " + str(result))
			# force result into the correct datatype
			if result != None: 
				dp.write_INTFC_value(nwvalue=dp.datatype(str(result))) 
				if dp.log_messages: Logger.info ("%s: %s--new value from %s datadecoder: %s" % (self.name, dp.name, decoder, str(dp.value)))
			else:
				raise Exception("From_ByteArray_converter " + decoder + " returned NULL as value from input: " + str(BA_databytes))

		except Exception as err:
			Logger.error(self.name + "--Error decoding message: " + str(BA_msg) + ", HEX = " + ByteArrayToHexString(BA_msg))
			Logger.exception(str(err))  

			
	def make_poll_telgr(self,pollmsg_def):
		# SA RA C1 C2 ND DD DD DD CD
		# -- SA Sender address (FF for network management), RA Receive address, 
		# -- C1 C2 Commandbytes, ND Number of databytes, DD databytes, CD Crc of all SA--DD
		sendbytes = HexStringToByteArray("FF " + pollmsg_def.searchkey)
		sendbytes += self.calc_crc(sendbytes)
		# Fix the A9 and AA issues
		sendbytes = sendbytes.replace(b"\xA9",b"\xA9\x00")
		sendbytes = sendbytes.replace(b"\xAA",b"\xA9\x01")
		# print ("EBUS Poll message: " + ByteArrayToHexString(sendbytes))
		return sendbytes
		
	def make_command_telgr(self, dp, nwvalue):
		import json
		try:
			# make sure the nwvalue has the correct datatype
			nwvalue = dp.datatype(nwvalue)
			# het enige wat we weten is dat er geen integraal of datapoints in de calcrule zitten, dus alleen ["*","/","+","-"]
			# alleen SIMPELE calcrules in de geest van x=#/a + b
			
			INTFC_rule = None
			if IsNot_NOE(dp.calc_rule):
				INTFC_rule = json.loads(dp.calc_rule.strip().replace("'",'"')).get('INTFC', None)
				print(INTFC_rule)
				if INTFC_rule.strip().split("&")[0].startswith("#") and type(nwvalue) in [float, int]:
					# It is possible that the nwvalue needs to be scaled/offset back
					operations = [x.strip() for x in INTFC_rule.strip().lower().lstrip("#").split("&")]
					# print ("original operations where: ", operations)
					# old_oper = ["*","/","+","-"]
					# new_oper = ["/","*","-","+"]
					# van achter naar voor terugrekenen
					for teller in range (len(operations)-1,-1,-1):
						# print (teller, operations[teller][0])
						try:
							old_operand = operations[teller][0]
							# index=old_oper.index(old_operand)
							# # print (index)
							# new_operand = new_oper[index]
							# # print (new_operand)
							if old_operand == "*": nwvalue = nwvalue / float(operations[teller].lstrip(old_operand))
							if old_operand == "/": nwvalue = nwvalue * float(operations[teller].lstrip(old_operand))
							if old_operand == "-": nwvalue = nwvalue + float(operations[teller].lstrip(old_operand))
							if old_operand == "+": nwvalue = nwvalue - float(operations[teller].lstrip(old_operand))
							
						except Exception as err:
							print(str(err))
							break
					
			# print ("Re-scaled value = ", nwvalue)
			
			# Waitkey()
			# now convert the new value to the correct bytearray
			BA_nwvalue = To_ByteArray_converter(dp.datadecoder, nwvalue)
			# print(ByteArrayToHexString(BA_nwvalue))
			# Waitkey()
			# convert the datapoint searchkey to a bytearray and add the sender (FF)
			BA_searchkey = HexStringToByteArray("FF " + dp.searchkey)
			# replace in the commanddata the 29 or 0D identifier with 0E
			BA_searchkey[5:6] = b"\x0E"
			# now add the new value bytes
			sendbytes = BA_searchkey + BA_nwvalue
			# recalculate the number of databytes now in the message
			sendbytes[4:5] = (len(sendbytes) - 5).to_bytes(1, byteorder="big")
			# and recalculate the Crc checksum
			sendbytes += self.calc_crc(sendbytes)
			# Fix the A9 and AA issues
			sendbytes = sendbytes.replace(b"\xA9",b"\xA9\x00")
			sendbytes = sendbytes.replace(b"\xAA",b"\xA9\x01")
			print (ByteArrayToHexString(sendbytes))
			# add the message to the message queue for the send routine
			self.add_msg(sendbytes, acknowledge_receipt=True, msgtype=MsgType.CommandMessage)
			# and immediately poll to see the result reflected..
			time.sleep(1.0)
			self.add_msg(self.make_poll_telgr(dp), acknowledge_receipt=False, msgtype=MsgType.PollMessage)
		except Exception as err:
			Logger.exception(str(err))
			
			
	def calc_crc(self,ByteArray):
		uc_crc = 0
		for databyte in ByteArray:
			uc_crc=self.calc_crc_byte(databyte, uc_crc)
		return bytearray([uc_crc])
		
	def calc_crc_byte(self,databyte, initial_uc_crc):
		uc_polynom=0
		uc_crc=initial_uc_crc
		uc_byte = databyte
		
		for i in range(8):
			if (uc_crc & 0x0080):uc_polynom=0x009B
			else: uc_polynom=0x0000
			# the ~ operator is the bitwise NOT operator....i.e. replace every 0 with a 1 and vice versa
			uc_crc = (uc_crc & ~0x0080) << 1
			if (uc_byte & 0x0080): uc_crc = uc_crc | 0x0001
			uc_crc = uc_crc ^ uc_polynom
			uc_byte = uc_byte << 1
			
		return uc_crc




def main(args):
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
