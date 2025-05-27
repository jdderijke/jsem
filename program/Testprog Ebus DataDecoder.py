#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Ebus DataDecoder test.py
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
import __main__
CWD=(os.path.dirname(os.path.realpath(__file__)))
if __name__ == "__main__":
	logfilename = os.path.basename(__main__.__file__)
	logfilename = logfilename.split('.')[0] + '.log'
	__main__.logfilename = logfilename
	__main__.backupcount = 1

	print(sys.path)
	
from LogRoutines import Logger

from Conversion_Routines import ByteToHexString, ByteArrayToHexString, HexStringToByteArray
from interfaces import *


def main(args):
	test=NewEbusInterface(name="warmtepomp", auto_start=False)
	while True:
		try:
			data =    input("HEX test string: ")
			decoder = input("Dataconverter  : ")
			result=test.data_FROM_convertor(decoder, HexStringToByteArray(data))
			print("result = ", result)
		except Exception as err:
			print (str(err))
	return 0


if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
