#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog Pooltimer Functie.py
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
import datetime as dt

def main(args):
	start_stop_list = [False] * 24
	# Normaal bedrijf, dus op een timer.
	times_str = "0:uit|1:aan|4:uit|18:aan|19:uit|22:aan"
	times = times_str.split("|")
	prev_hour = 0
	prev_action = 0
	for time in times:
		try:
			hour = int(time.split(":")[0])
			if hour < prev_hour: raise Exception
			
			if time.split(":")[1].upper() in ["AAN", "ON", "1"]:
				action = True
			elif time.split(":")[1].upper() in ["UIT", "OFF", "0"]:
				action = False
			else:
				raise Exception
			start_stop_list[prev_hour:hour] = [prev_action for x in range(hour-prev_hour)]
			start_stop_list[hour] = action
			prev_hour = hour
			prev_action = action
		except:
			print("Can not read timer settings, illegal format or not in ascending order: %s" % times_str)
			return
			
	start_stop_list[prev_hour:] = [prev_action for x in range(24-prev_hour)]
	print("pool timer set to: %s" % start_stop_list)
			
	if start_stop_list[dt.datetime.now().hour]:
		print ("AAN")
		# if not pool_filter_pump.value: Logger.info("Switching filterpump from OFF to ON...")
		# pool_filter_pump.write_value(input_value=True)
	else:
		print("UIT")
		# if pool_filter_pump.value: Logger.info("Switching filterpump from ON to OFF...")
		# pool_filter_pump.write_value(input_value=False)
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
