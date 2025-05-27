#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog ModbusTCP.py
#  
#  Copyright 2022  <pi@raspberrypi>
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
if __name__ == "__main__": __main__.logfilename = "ModbusTest.log"
import os
from LogRoutines import Logger
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import decode_ieee, word_list_to_long
from Conversion_Routines import HexStringToByteArray, ByteArrayToHexString, From_ASCII, To_ByteArray_converter, From_ByteArray_converter

def main(args):
	try:
		word_data = []
		headers = ['SAMC', 'TEMP', 'Voltage L1', 'Voltage L2', 'Voltage L3', 'Modbus Slave Max CUrrent', 'ALB Safe Current', 
				   'Actual Applied Max current']
		# c = ModbusClient(host='localhost', port=502)
		c = ModbusClient(host="192.168.178.140", port=502, debug=True)
		# data = c.custom_request(HexStringToByteArray("03 04 4C 00 05"))
		
		c.unit_id = 200
		word_data = word_data + c.read_holding_registers(1100, 4)
		# print (ByteArrayToHexString(data))
		
		c.unit_id = 1
		word_data = word_data + c.read_holding_registers(306, 6)
		print(word_data)
		word_data = word_data + c.read_holding_registers(1210, 4)
		print(word_data)
		word_data = word_data + c.read_holding_registers(1206, 2)
		print(word_data)
		
		results = [decode_ieee(x) for x in word_list_to_long(word_data)]
		print (results)
		for teller,result in enumerate(results):
			print (headers[teller], result)
			
		str_data = c.custom_request(HexStringToByteArray("03 04 B1 00 05"))
		print (ByteArrayToHexString(str_data))
		# eerste byte is herhaling van de function code (hier 03), tweede byte is number of databytes, skip dus eerste 2 bytes
		print('Mode 3 State: ' + From_ASCII(str_data[2:]))

		str_data = c.custom_request(HexStringToByteArray("03 04 BA 00 02"))
		print('Bytestr Setpoint I: ', ByteArrayToHexString(str_data))
		print ("Transaction ID = ", ByteArrayToHexString(To_ByteArray_converter("int16", c._transaction_id)))
		print ('Value Setpoint1: ', From_ByteArray_converter('float32', str_data[2:]))
		
		nwvalue = None
		while True:
			try:
				inputstr = input("New Setpoint Value: ")
				nwvalue = float(inputstr)
				break
			except Exception as err:
				print("Not a valid float number...try again...")
		
		nw_bytearray = To_ByteArray_converter("float32", nwvalue)
		print ("Bytestr NEW Setpoint I: ", ByteArrayToHexString(nw_bytearray))
		nw_bytearray = bytearray(b'\x10\x04\xBA\x00\x02\x04') + nw_bytearray
		print ("Full messagebytes send: ", ByteArrayToHexString(nw_bytearray))
		result = c.custom_request(nw_bytearray)
		print ("Response is: ", ByteArrayToHexString(result))
		
		
	except ValueError:
		print("Error with host or port params")
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
