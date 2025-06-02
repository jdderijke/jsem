#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog Calculate Timerset.py
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
if __name__ == "__main__":
	 __main__.logfilename = "TEST.log"
	 __main__.backupcount = 1
import os
import sys


from Common_Routines import Calculate_Timerset
import time
from datetime import datetime

def main(args):
	while True:
		
		start_str = input('Geef het referentietijdstip op (dd-mm-YYYY HH:MM:SS), of niets voor NU: ')
		# We bepalen de timestamp van het referentietijdstip
		if start_str != "":
			start_ts = int(datetime.strptime(start_str, "%d-%m-%Y %H:%M:%S").timestamp())
		else:
			start_ts = time.time()

		inputstr = input("Geef een geldige input voor de interval parameter van de Calculate_Timerset module: ")
		timerset, repeat = Calculate_Timerset(start_timestamp=start_ts, interval=inputstr)
		uren, rest = divmod(timerset, 3600)
		minuten, seconden = divmod(rest, 60)
		print('Initiele timer wordt gezet voor %s uur %s minuten en %s seconden, en zal dus afgaan op %s' % 
							(uren, minuten, seconden, datetime.fromtimestamp(int(time.time()) + timerset)))
		# print('Initiele timer wordt gezet voor %s uur %s minuten en %s seconden' % (uren, minuten, seconden))

		uren, rest = divmod(repeat, 3600)
		minuten, seconden = divmod(rest, 60)
		print("De repeat timerset wordt dan %s uren, %s minuten en %s seconden, en zal dus afgaan op %s" % 
							(uren, minuten, seconden, datetime.fromtimestamp(int(time.time()) + timerset + repeat)))
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
