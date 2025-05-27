#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog get newest file.py
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
import os
import glob
CWD=(os.path.dirname(os.path.realpath(__file__)))
DAYAHEAD_PRICES = "/DayAHeadPrices"
POWERSTATS = "/Powerstats"

# def get_newest_file(path):
	# files = os.listdir(path)
	# paths = [os.path.join(path, basename) for basename in files]
	# return max(paths, key=os.path.getctime)

def get_newest_file(path):
	print("path plus pattern = %s" % path)
	files = glob.glob(path)
	if files == []:
		return None
	else:
		return max(files, key=os.path.getctime)



def main(args):
	print(get_newest_file(CWD+DAYAHEAD_PRICES+"/*.pip"))
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
