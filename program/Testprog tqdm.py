#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog tqdm.py
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
from tqdm import tqdm
import time


def main(args):
	timeout = 20.0
	total_time = 0.0
	with tqdm(total=timeout) as pbar:
		while True:
			loop_start = time.time()
			if  total_time > timeout:
				raise Exception('Timeout reached')
			else:
				time.sleep(0.5)
			loop_time = time.time() - loop_start
			pbar.update(loop_time)
			total_time += loop_time
	
	
	# bar = tqdm(range(10))
	# tot = 0
	# for i in bar:
		# time.sleep(2)
		# tot += i
		# bar.set_postfix({"total":tot})
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
