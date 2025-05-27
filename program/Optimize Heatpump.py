#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Optimize Heatpump.py
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

# Input data
energy_needed = np.array([6, 6, 6, 7, 8, 9, 6, 5, 4, 3, 3, 2]) # in Kwh
electricity_price = np.array([10, 11, 12, 15, 11, 8, 5, 8, 2, 9, 10, 15]) # in ct/Kwh
heatpump_power = 18 # in Kwh
heatpump_consumption = 4 # in Kwh
buffer_capacity = 50 # in Kwh
buffer_initial = 3 # in Kwh

# Define the dynamic programming function
def dynamic_programming(energy_needed, electricity_price, heatpump_power, heatpump_consumption, buffer_capacity, buffer_initial):
	n = len(energy_needed)
	# Initialize the table to store the optimal values and decisions
	value_table = np.zeros((n, buffer_capacity+1))
	decision_table = np.zeros((n, buffer_capacity+1))
	# Fill in the table from right to left
	for t in range(n-1, -1, -1):
		for b in range(buffer_capacity+1):
			# Compute the maximum value and decision for the current state
			max_value = 0
			max_decision = 0
			for h in range(0, min(heatpump_power, energy_needed[t]+b)+1):
				# Compute the net value of using the heat pump at this hour
				net_value = (heatpump_power - h) * electricity_price[t] - heatpump_consumption * electricity_price[t+1]
				if t < n-1:
					net_value += value_table[t+1, min(b+h-heatpump_consumption, buffer_capacity)]
				if net_value > max_value:
					max_value = net_value
					max_decision = h
			# Update the table with the optimal value and decision for the current state
			value_table[t, b] = max_value
			decision_table[t, b] = max_decision
	# Trace back the optimal decisions
	optimal_decisions = []
	b = buffer_initial
	for t in range(n):
		optimal_decisions.append(decision_table[t, b])
		b = min(b+optimal_decisions[-1]-heatpump_consumption, buffer_capacity)
	# Return the optimal decisions and the corresponding total cost
	total_cost = sum([optimal_decisions[t] * electricity_price[t] for t in range(n)]) / 100 # convert to euro
	return optimal_decisions, total_cost


def main(args):
	# Call the dynamic programming function
	optimal_decisions, total_cost = dynamic_programming(energy_needed, electricity_price, heatpump_power, heatpump_consumption, buffer_capacity, buffer_initial)
	
	# Print the optimal decisions and the corresponding total cost
	print("Optimal decisions:", optimal_decisions)
	print("Total cost:", total_cost, "euro")
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
