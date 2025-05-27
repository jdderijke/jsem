#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Optimize Heatpump2.py
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
import numpy as np

prices = [10, 11, 12, 15, 11, 8, 5, 8, 2, 9, 10, 15] # hourly electricity prices (ct/Kwh)
needs = [6, 6, 6, 7, 8, 9, 6, 5, 4, 3, 3, 2] # forecasted energy needs (Kwh)
heat_pump_output = 18 # heat pump output (Kwh)
heat_pump_input = 4 # heat pump input (Kwh)
max_buffer_size = 50 # max capacity of hot water buffer (Kwh)
initial_buffer_size = 3 # initial buffer size (Kwh)

# Create a function to calculate the total cost of electricity for a given heat pump operation:
def calculate_cost(buffer_size, needs, prices):
	# This function takes the current buffer size, the forecasted energy needs, 
	# and the electricity prices as inputs and returns the total cost of electricity for that particular operation.
	cost = 0
	for i in range(len(needs)):
		if needs[i] <= buffer_size:
			buffer_size -= needs[i]
			cost += needs[i] * prices[i]
		else:
			cost += buffer_size * prices[i]
			buffer_size = 0
	return cost
	
		
	
def main(args):
	# Create a loop to find the optimal heat pump operation:    
	min_cost = np.inf # initialize the minimum cost to a very large number
	optimal_operation = None # initialize the optimal operation to None
	# This loop goes through all possible heat pump operations starting at each hour in the forecast and 
	# calculates the total cost of electricity for each operation. The optimal operation is the one with the lowest cost.
	for i in range(len(needs)):
		remaining_needs = needs[i:]
		remaining_prices = prices[i:]
		for j in range(1, len(remaining_needs) + 1):
			operation_needs = sum(remaining_needs[:j])
			if operation_needs * heat_pump_output <= max_buffer_size - initial_buffer_size:
				buffer_size = initial_buffer_size + operation_needs * heat_pump_output - operation_needs * heat_pump_input
				cost = calculate_cost(buffer_size, remaining_needs[:j], remaining_prices[:j])
				if cost < min_cost:
					min_cost = cost
					optimal_operation = (i, j, buffer_size)
					
	print("Optimal operation: start at hour {}, run for {} hours with a final buffer size of {} Kwh".format(optimal_operation[0], optimal_operation[1], optimal_operation[2]))
	print("Total cost of electricity: {} ct".format(min_cost))
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
