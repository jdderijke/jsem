#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Testprog sdm_modbus.py
#  
#  Copyright 2024  <pi@raspberrypi>
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

import os
import __main__
if __name__ == "__main__":
	 __main__.logfilename = os.path.basename(__file__).replace("py", "log")
	 __main__.backupcount = 1
from LogRoutines import Logger

import argparse
import json
import sdm_modbus
# from interfaces import SdmModbusInterface
# from DB_Routines import load_and_configure_datapoints

# from pyModbusTCP.client import ModbusClient
# from pyModbusTCP.utils import decode_ieee, word_list_to_long


if __name__ == "__main__":

	# SdmModbusInterface(name="Verm_meter_WP", auto_start=True)
	# load_and_configure_datapoints(dpIDs=[377,424,425,426])
	# input('any')
	
	
	
	# initializer = getattr(sdm_modbus, 'SDM72')
	# meter = initializer(
		# host='192.168.178.205',
		# port=502,
		# timeout=1,
		# framer=None,
		# unit=1,
		# udp=False 
	# )
	
	
	
	# meter = sdm_modbus.SDM72(
		# host='192.168.178.205',
		# port=502,
		# timeout=1,
		# framer=None,
		# unit=1,
		# udp=False 
	# )

	# print("\ndirect access excamples..")
	# print(f"{meter.read('l1_voltage')}")
	# print(f"{meter.read('l2_voltage')}")
	# print(f"{meter.read('l3_voltage')}")
	
	# print("\nInput Registers:")

	# for k, v in meter.read_all(sdm_modbus.registerType.INPUT, scaling=True).items():
		# address, length, rtype, dtype, vtype, label, fmt, batch, sf = meter.registers[k]

		# if type(fmt) is list or type(fmt) is dict:
			# print(f"\t{label}: {fmt[str(v)]}")
		# elif vtype is float:
			# print(f"\t{label}: {v:.2f}{fmt}")
		# else:
			# print(f"\t{label}: {v}{fmt}")

	# print("\nHolding Registers:")

	# for k, v in meter.read_all(sdm_modbus.registerType.HOLDING, scaling=True).items():
		# address, length, rtype, dtype, vtype, label, fmt, batch, sf = meter.registers[k]

		# if type(fmt) is list:
			# print(f"\t{label}: {fmt[v]}")
		# elif type(fmt) is dict:
			# print(f"\t{label}: {fmt[str(v)] if str(v) in fmt else fmt[v]}")
		# elif vtype is float:
			# print(f"\t{label}: {v:.2f}{fmt}")
		# else:
			# print(f"\t{label}: {v}{fmt}")
	
	
	# ---------------------------------LAADPAAL TESTEN---------------------------------------------------------------------

	# laadpaalinfo = sdm_modbus.ALFEN_NG9xx_info(
		# host='192.168.178.140',
		# port=502,
		# timeout=1,
		# framer=None,
		# unit=200,
		# udp=False 
	# )

	# print(f"{laadpaalinfo}:")
	# print("\nHolding Registers:")

	# for k, v in laadpaalinfo.read_all(sdm_modbus.registerType.HOLDING, scaling=True).items():
		# address, length, rtype, dtype, vtype, label, fmt, batch, sf = laadpaalinfo.registers[k]

		# if type(fmt) is list:
			# print(f"\t{label}: {fmt[v]}")
		# elif type(fmt) is dict:
			# print(f"\t{label}: {fmt[str(v)] if str(v) in fmt else fmt[v]}")
		# elif vtype is float:
			# print(f"\t{label}: {v:.2f}{fmt}")
		# else:
			# print(f"\t{label}: {v}{fmt}")

	# laadpaalinfo.disconnect()


	# input('any key')


	laadpaal = sdm_modbus.ALFEN_NG9xx(
		host='192.168.178.140',
		port=502,
		timeout=1,
		framer=None,
		unit=1,
		udp=False 
	)
	
	

	print(f"{laadpaal}:")
	
	# print(laadpaal.registers)
	
	print("\ndirect access excamples..")
	print(f"{laadpaal.read('l1_voltage')}")
	print(f"{laadpaal.read('l2_voltage')}")
	print(f"{laadpaal.read('l3_voltage')}")
	
	# print(f"{laadpaal.read('max_current_setpoint')}")
	# print(f"{laadpaal.read('setpoint_accepted')}")
	# print(f"{laadpaal.read('charging_phases')}")
	
	print("\nInput Registers:")

	for k, v in laadpaal.read_all(sdm_modbus.registerType.INPUT, scaling=True).items():
		address, length, rtype, dtype, vtype, label, fmt, batch, sf = laadpaal.registers[k]

		if type(fmt) is list or type(fmt) is dict:
			print(f"\t{label}: {fmt[str(v)]}")
		elif vtype is float:
			print(f"\t{label}: {v:.2f}{fmt}")
		else:
			print(f"\t{label}: {v}{fmt}")

	print("\nHolding Registers:")

	for k, v in laadpaal.read_all(sdm_modbus.registerType.HOLDING, scaling=True).items():
		address, length, rtype, dtype, vtype, label, fmt, batch, sf = laadpaal.registers[k]

		if type(fmt) is list:
			print(f"\t{label}: {fmt[v]}")
		elif type(fmt) is dict:
			print(f"\t{label}: {fmt[str(v)] if str(v) in fmt else fmt[v]}")
		elif vtype is float:
			print(f"\t{label}: {v:.2f}{fmt}")
		else:
			print(f"\t{label}: {v}{fmt}")

