#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog PyShelly.py
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
'''
Om het hele pakket pyShelly te re-installen vanaf de sourcefiles:
git clone het pyShelly pakket van Github.....
daarna:
python3 -m pip install /home/pi/pyShelly
'''
from pyShelly import pyShelly
import time
import sys


import sys
import time

def spinning_cursor():
	while True:
		for cursor in '|/-\\':
			yield cursor

def spincursor(duration=1.0):
	spinner = spinning_cursor()
	for _ in range(int(10*duration)):
		sys.stdout.write(next(spinner))
		sys.stdout.flush()
		time.sleep(0.1)
		sys.stdout.write('\b')


def device_added(dev,code):
  print (dev," ",code)

def dump(obj):
	for attr in dir(obj):
		print("obj.%s = %r" % (attr, getattr(obj, attr)))


def main(args):
	shelly1 = pyShelly()
	shelly2 = pyShelly()
	
	print("version:",shelly1.version())
	
	
	# shelly1.cb_device_added.append(device_added)
	shelly1.start()
	# shelly1.discover()
	
	# shelly2.cb_device_added.append(device_added)
	shelly2.start()
	# shelly2.discover()
	# while True:
		# pass
	
	oldlen = len(shelly1.devices)
	print ("Adding pro 1 to shelly1 interface, initial device list length = %s" % oldlen)
	shelly1.add_device_by_ip("192.168.178.218", 'IP-addr')  # this takes some time 
	while len(shelly1.devices) == oldlen:
		spincursor(0.5)
	print ("")
	print ("Added to shelly1, new device list length = %s" % len(shelly1.devices))

	# oldlen = len(shelly2.devices)
	# print ("Adding pro 1 to shelly2 interface, initial device list length = %s" % oldlen)
	# shelly2.add_device_by_ip("192.168.178.218", 'IP-addr')  # this takes some time 
	# while len(shelly2.devices) == oldlen:
		# spincursor(0.5)
	# print ("")
	# print ("Added to shelly2, new device list length = %s" % len(shelly1.devices))




	
	input("any key")
	
	# for device in shelly1.devices:
		# dump(device)
		
	while True:
		for device in shelly1.devices:
			if device.device_type == "RELAY":
				
				device.turn_off()
				print ("Shelly1 interface device status is OFF, name = %s, ip= %s, state = %s" % (device.device_name(), device.ip_addr, device.state))
				time.sleep(3)
				device.turn_on()
				print ("Shelly1 interface device status is ON, state = %s" % device.state)
				time.sleep(3)
				
		# for device in shelly2.devices:
			# if device.device_type == "RELAY":
				# device.turn_off()
				# print ("Shelly2 interface device status is OFF, state = %s" % device.state)
				# time.sleep(3)
				# device.turn_on()
				# print ("Shelly2 interface device status is ON, state = %s" % device.state)
				# time.sleep(3)







	# # print(shelly.devices) # look for Relays
	# n = 0  # index in devices
	# # shelly.devices[n].device_type
	
	# if shelly.devices[n].device_type == 'RELAY':
		# while True:
			# # if not shelly.devices[n].turn_off():
			# shelly.devices[n].turn_off()
			# print (shelly.devices[n].state)
			# time.sleep(3)
			# shelly.devices[n].turn_on()
			# print (shelly.devices[n].state)
			# time.sleep(3)
	
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
