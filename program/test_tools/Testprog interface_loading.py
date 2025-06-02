#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  interface_testjes.py
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
from interfaces import *
from Config import *
from DB_Routines import load_and_configure_datapoints, load_definitions
from LogRoutines import Logger
from Common_Data import CWD

def main(args):
	Logger.info ("Loading datapoints definitions from database: " + CWD + DBFILE)
	load_definitions()
	load_and_configure_datapoints()
	
	
   
	test = ESMR50Interface(ID=4, auto_start=True)
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
