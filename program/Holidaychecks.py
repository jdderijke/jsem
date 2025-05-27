#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  holidaychecks.py
#  
#  Copyright 2023 jandirk <jandirk@linux-develop>
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
from datetime import datetime

dutch_holidays=[
				datetime(2020,1,1),
				datetime(2020,4,10),
				datetime(2020,4,12),
				datetime(2020,4,13),
				datetime(2020,4,27),
				datetime(2020,5,5),
				datetime(2020,5,21),
				datetime(2020,5,31),
				datetime(2020,6,1),
				datetime(2020,12,25),
				datetime(2020,12,26),
				datetime(2020,12,31),
				#
				datetime(2021,1,1),
				datetime(2021,4,2),
				datetime(2021,4,4),
				datetime(2021,4,5),
				datetime(2021,4,27),
				datetime(2021,5,5),
				datetime(2021,5,13),
				datetime(2021,5,23),
				datetime(2021,5,24),
				datetime(2021,12,25),
				datetime(2021,12,26),
				datetime(2021,12,31),
				#
				datetime(2022,1,1),
				datetime(2022,4,15),
				datetime(2022,4,17),
				datetime(2022,4,18),
				datetime(2022,4,27),
				datetime(2022,5,5),
				datetime(2022,5,26),
				datetime(2022,6,5),
				datetime(2022,6,6),
				datetime(2022,12,25),
				datetime(2022,12,26),
				datetime(2022,12,31),
				#
				datetime(2023,1,1),
				datetime(2023,4,7),
				datetime(2023,4,9),
				datetime(2023,4,10),
				datetime(2023,4,27),
				datetime(2023,5,5),
				datetime(2023,5,18),
				datetime(2023,5,28),
				datetime(2023,5,29),
				datetime(2023,12,25),
				datetime(2023,12,26),
				datetime(2023,12,31)
				]
dutch_holidays = [x.date() for x in dutch_holidays]


	
dutch_schoolvacations = [
						('voorjaarsvakantie noord', datetime(2020,2,15), datetime(2020,2,23), 1),
						('voorjaarsvakantie midden', datetime(2020,2,22), datetime(2020,3,1), 1),
						('voorjaarsvakantie zuid', datetime(2020,2,22), datetime(2020,3,1), 1),
						('meivakantie', datetime(2020,4,25), datetime(2020,5,3), 3),
						('zomervakantie noord', datetime(2020,7,4), datetime(2020,8,16), 1),
						('zomervakantie midden', datetime(2020,7,18), datetime(2020,8,30), 1),
						('zomervakantie zuid', datetime(2020,7,11), datetime(2020,8,23), 1),
						('bouwvak noord', datetime(2020,7,18), datetime(2020,8,8), 1),
						('bouwvak midden', datetime(2020,8,1), datetime(2020,8,22), 1),
						('bouwvak zuid', datetime(2020,7,25), datetime(2020,8,15), 1),
						('herfstvakantie noord', datetime(2020,10,10), datetime(2020,10,18), 1),
						('herfstvakantie midden', datetime(2020,10,17), datetime(2020,10,25), 1),
						('herfstvakantie zuid', datetime(2020,10,17), datetime(2020,10,25), 1),
						('kerstvakantie', datetime(2020,12,19), datetime(2021,1,3), 3),
						#
						('voorjaarsvakantie noord', datetime(2021,2,20), datetime(2021,2,28), 1),
						('voorjaarsvakantie midden', datetime(2021,2,20), datetime(2021,2,28), 1),
						('voorjaarsvakantie zuid', datetime(2021,2,13), datetime(2021,2,21), 1),
						('meivakantie', datetime(2021,5,1), datetime(2021,5,9), 3),
						('zomervakantie noord', datetime(2021,7,10), datetime(2021,8,22), 1),
						('zomervakantie midden', datetime(2021,7,17), datetime(2021,8,29), 1),
						('zomervakantie zuid', datetime(2021,7,24), datetime(2021,9,5), 1),
						('bouwvak noord', datetime(2021,7,24), datetime(2021,8,14), 1),
						('bouwvak midden', datetime(2021,7,31), datetime(2021,8,21), 1),
						('bouwvak zuid', datetime(2021,8,7), datetime(2021,8,28), 1),
						('herfstvakantie noord', datetime(2021,10,16), datetime(2021,10,24), 1),
						('herfstvakantie midden', datetime(2021,10,16), datetime(2021,10,24), 1),
						('herfstvakantie zuid', datetime(2021,10,23), datetime(2021,10,31), 1),
						('kerstvakantie', datetime(2021,12,25), datetime(2022,1,9), 3),
						#
						('voorjaarsvakantie noord', datetime(2022,2,19), datetime(2022,2,27), 1),
						('voorjaarsvakantie midden', datetime(2022,2,26), datetime(2022,3,6), 1),
						('voorjaarsvakantie zuid', datetime(2022,2,26), datetime(2022,3,6), 1),
						('meivakantie', datetime(2022,4,30), datetime(2022,5,8), 3),
						('zomervakantie noord', datetime(2022,7,16), datetime(2022,8,28), 1),
						('zomervakantie midden', datetime(2022,7,9), datetime(2022,8,21), 1),
						('zomervakantie zuid', datetime(2022,7,23), datetime(2022,9,4), 1),
						('bouwvak noord', datetime(2022,7,30), datetime(2022,8,20), 1),
						('bouwvak midden', datetime(2022,7,23), datetime(2022,8,13), 1),
						('bouwvak zuid', datetime(2022,8,6), datetime(2022,8,27), 1),
						('herfstvakantie noord', datetime(2022,10,15), datetime(2022,10,23), 1),
						('herfstvakantie midden', datetime(2022,10,22), datetime(2022,10,30), 1),
						('herfstvakantie zuid', datetime(2022,10,22), datetime(2022,10,30), 1),
						('kerstvakantie', datetime(2022,12,24), datetime(2023,1,8), 3),
						#
						('voorjaarsvakantie noord', datetime(2023,2,25), datetime(2023,3,5), 1),
						('voorjaarsvakantie midden', datetime(2023,2,25), datetime(2023,3,5), 1),
						('voorjaarsvakantie zuid', datetime(2023,2,18), datetime(2023,2,26), 1),
						('meivakantie', datetime(2023,4,29), datetime(2023,5,7), 3),
						('zomervakantie noord', datetime(2023,7,22), datetime(2023,9,3), 1),
						('zomervakantie midden', datetime(2023,7,8), datetime(2023,8,20), 1),
						('zomervakantie zuid', datetime(2023,7,15), datetime(2023,8,27), 1),
						('bouwvak noord', datetime(2023,8,5), datetime(2023,8,26), 1),
						('bouwvak midden', datetime(2023,7,22), datetime(2023,8,12), 1),
						('bouwvak zuid', datetime(2023,7,29), datetime(2023,8,19), 1),
						('herfstvakantie noord', datetime(2023,10,21), datetime(2023,10,29), 1),
						('herfstvakantie midden', datetime(2023,10,14), datetime(2023,10,22), 1),
						('herfstvakantie zuid', datetime(2023,10,14), datetime(2023,10,22), 1),
						('kerstvakantie', datetime(2023,12,23), datetime(2024,1,7), 3),
						]
dutch_schoolvacations = [(x[0], x[1].date(), x[2].date(), x[3]) for x in dutch_schoolvacations]

def is_school_holiday(check_date = datetime.now):
	total_count = 0
	for vac in dutch_schoolvacations:
		vac_start = vac[1]
		vac_end = vac[2]
		if vac_start <= check_date.date() <= vac_end: total_count += vac[3]
		
	return total_count

def is_public_holiday(check_date = datetime.now):
	if check_date.date() in dutch_holidays:
		return 1
	else:
		return 0


def main(args):
	while True:
		check_date = datetime.now()
		check_str = input('Check date : ')
		if check_str: check_date = datetime.strptime(check_str, "%Y-%m-%d")
		
		print ('Datum %s is een publieke feestdag: %s' % (check_date.date(), bool(is_public_holiday(check_date))))
		print ('Datum %s is een schoolvakantie (waarde): %s' % (check_date.date(), is_school_holiday(check_date)))
		print ()
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))

