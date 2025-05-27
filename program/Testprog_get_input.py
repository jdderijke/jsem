#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog_get_input.py
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
 
def get_input(prompt="", default=None):
	if default is not None: 
		try:
			if type(default) == float:
				inp = float(input(prompt))
			elif type(default) == int:
				inp = int(float(input(prompt)))
			elif type(default) == bool:
				inp = bool(int(input(prompt)))
			else:
				inp = input(prompt)
		except ValueError:
			inp = default
	else:
		inp = input(prompt)
	return inp


def main(args):
	while True:
		print ("get_input returned: ", get_input("Geef een float getal: ", 12.5))
		print ("get_input returned: ", get_input("Geef een int getal: ", 3))
		print ("get_input returned: ", get_input("Geef een bool getal: ", False))
		print ("get_input returned: ", get_input("Geef een string: ", "pipo"))
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
