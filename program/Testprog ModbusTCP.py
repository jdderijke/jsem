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
import os
import sys


os.environ["ENV"] = "DEV"

from Common_Utils import get_logger

Logger = get_logger()
Logger.info(f'Logger {__name__} started')

import sdm_modbus
from sdm_modbus.meter import ModbusNotResponding



def main(args):
	try:
		modbus_conn = sdm_modbus.SOLIS3P5K_4G(host="192.168.178.206", port=502, timeout=10, framer=None,unit=1, udp=False)
		modbus_conn.write('power_limitation', 100)

		result = modbus_conn.read('power_limitation', scaling=True)
		print(result)

	except ValueError:
		print("Error with host or port params")
	except ModbusNotResponding as err:
		print(str(err))
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
