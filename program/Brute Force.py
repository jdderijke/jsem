#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Brute Force.py
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
import time

# uur          1    2    3    4    5    6    7    8    9    10    11    12    13    14    15    16    17    18    19    20    21    22    23    24
# epex_prijs = [9.0, 7.5, 8.3, 1.5, 1.0, 1.0, 3.0, 5.0, 7.0, 10.0, 12.0, 11.0, 13.0, 14.0, 20.0, 18.0, 17.0, 12.0, 11.0, 10.0, 14.0, 16.0, 14.0, 12.0]	# ct/Kwh
# kwh_usage = [6.0, 5.9, 4.2, 0.0, 5.0, 5.0, 6.0, 7.0, 7.0, 8.5,  9.5,  10.1,  9.0,  6.0, 14.0, 10.0,  8.0,  6.0,  6.5,  5.6,  6.0,  4.5,  4.0,  4.5]		# Kwh
# # epex_prijs = [9.0, 7.5, 8.3, 1.5, 1.0, 1.0, 3.0, 5.0, 7.0, 10.0, 12.0, 11.0, 13.0, 14.0, 20.0, 18.0, 17.0, 12.0, 11.0, 10.0]	# ct/Kwh
# # kwh_usage =  [6.0, 5.9, 4.2, 0.0, 5.0, 5.0, 6.0, 7.0, 7.0, 8.5,  9.5,  10.1,  9.0,  6.0, 14.0, 10.0,  8.0,  6.0,  6.5,  5.6]		# Kwh
# hp_power = 18.0		# Kw
# hp_usage = 3.9		# Kw
# buf_min = 5.0		# Kwh
# buf_max = 50.0		# Kwh
# buf_init = 5.0		# Kwh

# Johan test set...
hp_power = 14.5		# Kw
hp_usage = 3.5		# Kw
buf_min = 3.0		# Kwh
buf_max = 40.0		# Kwh
buf_init = 5.1		# Kwh
# uur          0      1     2     3     4     5     6     7     8     9    10    11     12     13    14    15    16    17     18     19    20    21    22    23
epex_prijs = [5.50, 4.38, 4.07, 3.99, 3.51, 4.02, 6.24, 8.12, 8.12, 6.24, 2.13, 0.00, -1.00, -1.14, 6.21, 8.21, 2.93, 7.94, 10.08, 11.62, 9.67, 8.25, 7.62, 6.49]
kwh_usage  = [0.42, 0.75, 0.90, 1.21, 1.75, 1.62, 1.85, 1.95, 2.03, 2.56, 1.43, 1.30,  0.42,  0.00, 2.50, 3.00, 1.65, 2.36,  2.48,  2.50, 2.56, 3.20, 3.42, 3.50]


def max_bits(b):
	return (1 << b) - 1
	
def clever_force():
	# Uiteindelijk hoeven we alleen voor het uur NU te bepalen of we gaan draaien of niet.
	# Als dan de kwh_usage voor het komende uur hoger is dan wat er in het buffer zit (incl minimum eis), dan MOETEN we wel draaien
	# Als we zouden draaien en daardoor zou (incl kwh_usage) het buffer boven het maximum uitkomen, dan mogen we NIET draaien.
	# Verder, kijken we of er een laagste prijspunt in de toekomst is die ook lager dan nu is, zo nee, dan draaien maar
	# ZO ja, kunnen we dat punt bereiken met de huidige buffer? Als dat zo is, dan wachten we op dat punt, dus niet draaien nu
	# Als we dat punt niet kunnen bereiken, kunnen we dan het één na laagste punt wat nog steeds lager is dan nu bereiken? etc. etc.
	# omdat we epex moeten gaan sorteren op prijs...maken we de gegevens daar meer geschikt voor, door ze in een tuples list onder te brengen
	# de tuples zijn nu (uur, epex_prijs)
	data = list(zip([x for x in range(len(epex_prijs))], epex_prijs))
	# print(data)
	# input("any key")
	
	# We maken ook een list waarin we de buffer nivos kunnen opslaan, te beginnen met buf_init
	buf_cap = [None for x in range(len(epex_prijs))]
	buf_cap[0] = buf_init
	# En we maken een draaien lijst die aangeeft of we moeten draaien (per uur)
	draaien = [False for x in range(len(epex_prijs))]
	# En ook een cost lijst voor de kosten (per uur)
	cost = [0.0 for x in range(len(epex_prijs))]

	for cur_hour in range(len(epex_prijs)):
		if kwh_usage[cur_hour] > buf_cap[cur_hour] - buf_min:
			# Als dan de kwh_usage voor het komende uur hoger is dan wat er in het buffer zit (incl minimum eis), dan MOETEN we wel draaien
			# AAN
			draaien[cur_hour] = True
		elif buf_cap[cur_hour] + hp_power - kwh_usage[cur_hour] > buf_max:
			# Als we zouden draaien en daardoor zou (incl kwh_usage) het buffer boven het maximum uitkomen, dan mogen we NIET draaien.
			# UIT
			draaien[cur_hour] = False
		else:
			# Verder, kijken we of er een laagste prijspunt in de toekomst is
			# hiervoor sorteren we het restant van de epex data list in oplopende epex_prijs
			sorted_data = sorted(data[cur_hour:], key=lambda x: x[1])
			# print(sorted_data)
			# input("any key")
			# ZO ja, kunnen we dat punt bereiken met de huidige buffer? Als dat zo is, dan wachten we op dat punt, dus niet draaien nu
			# Als we dat punt niet kunnen bereiken, kunnen we dan het één na laagste punt wat nog steeds lager is dan nu bereiken? etc. etc.
			for cheaper_fit in range(len(sorted_data)):
				if sorted_data[cheaper_fit][0] == cur_hour and cur_hour != (len(epex_prijs) - 1):
					# We zijn bij het zoeken naar goedkope uren dit huidige uur tegen gekomen. Dat is natuurlijk altijd zo als we 
					# in het laatste uur zitten, in dat geval hoeft hij niet aan...anders wel
					draaien[cur_hour] = True
					break
				# we tellen nu het verbruik op van alle uren tussen NU en de cheaper_fit
				if sum(kwh_usage[cur_hour:sorted_data[cheaper_fit][0]]) <= buf_cap[cur_hour] - buf_min:
					# UIT, we kunnen het goedkoopste tijdstip halen met ons huidige buffer en wachten dus daarop
					draaien[cur_hour] = False
					break
						
		# admin
		cost[cur_hour] = (hp_usage * epex_prijs[cur_hour]) if draaien[cur_hour] else 0.0
		if cur_hour < (len(epex_prijs) - 1):
			if draaien[cur_hour]:
				buf_cap[cur_hour+1] = buf_cap[cur_hour] + hp_power - kwh_usage[cur_hour]
			else:
				buf_cap[cur_hour+1] = buf_cap[cur_hour] - kwh_usage[cur_hour]
		
		# print ("uur %s, gaat HP %s, buf_init = %s, cost = %s, cum_cost = %s" % 
			# (cur_hour, 'AAN' if draaien[cur_hour] else 'UIT', round(buf_cap[cur_hour],1), 
			 # round(cost[cur_hour],1), round(sum(cost[0:cur_hour+1]), 1)))
		
	result = dict(draaien=draaien, buf_cap=buf_cap, cost=cost)
	return result

def brute_force():
	# Deze methode kost relatief veel processor tijd, bovendien wordt de duur van de berekening in principe verdubbeld 
	# bij ieder extra uur wat vooruit gekeken moet worden..... Niet optimaal dus en een beetje bruut...
	uren = len(epex_prijs)
	# In principe kunnen we ieder interval (uur) beslissen of we WEL of NIET draaien, als we dat voorstellen door een bit (1 of 0)
	# dan geven ALLE integers van x bits (waarbij x het aantal intervallen is) dus ALLE mogelijke combinaties van wel of niet draaien aan/ 
	max_getal = max_bits(uren)
	results = []
	# bereken ALLE mogelijke combinaties van WEL of NIET draaien door domweg alle integers af te lopen en reken uit wat de kosten zijn...
	for getal in range(0, max_getal + 1):
		buf_cap = buf_init
		is_valid = True
		cost_verloop = []
		buf_verloop = [buf_init]
		# voor ieder uur is er een mogelijkheid om WEL of NIET te draaien.
		for hour in range(uren):
			# Of er in een bepaald uur gedraaid wordt kan aangegeven worden met een 1 of een 0, op die manier ontstaat een
			# integer (getal) met x bits, waarbij x het aantal uren is dat meegenomen wordt. Door de range (0, getal) af te lopen
			# worden alle mogelijke combinaties meegenomen.
			if (getal >> hour) & 1 == 1:
				# pomp AAN
				# dit heeft gevolgen voor de start_buffer capaciteit voor het volgende uur
				buf_cap = buf_cap + hp_power - kwh_usage[hour]
				cost = hp_usage * epex_prijs[hour]
			else:
				# pomp UIT
				buf_cap = buf_cap - kwh_usage[hour]
				cost = 0.0
				
			# Echter, wanneer op enig moment de buffer inhoud kleiner dan een ondergrens (buf_min) of groter dan een bovengrens (buf_max)
			# wordt dan is dat getal ongeldig en wordt de poging verder afgebroken.
			if buf_cap > buf_max or buf_cap < buf_min: 
				is_valid = False
				break
			else:
				# Als de buffer wel binnen de grenzen blijft dan kunnen we doorgaan naar het volgende uur
				buf_verloop.append(buf_cap)
				cost_verloop.append(cost)
				
		if is_valid: results.append((getal, cost_verloop, buf_verloop, sum(cost_verloop)))
	# Op die manier ontstaat een lijst met alle mogelijke en geldige getallen, met hun bijbehorende kosten en verloop van de buffer.
	# Het getal met de laagste kosten is de optimale oplossing.
	return min(results, key = lambda t: t[3])
	

def main(args):
	start=time.time()
	clever_result = clever_force()
	print("clever_force() took %s s" % (time.time() - start))
	for cur_hour in range(len(epex_prijs)):
		print ("Clever___uur %s, gaat HP %s, buf_init = %s, cost = %s, cum_cost = %s" % 
			(cur_hour, 'AAN' if clever_result["draaien"][cur_hour] else 'UIT', round(clever_result["buf_cap"][cur_hour],2), 
			 round(clever_result["cost"][cur_hour],2), round(sum(clever_result["cost"][0:cur_hour+1]), 2)))
	
	input("Any key to continue...")
	
	start=time.time()
	brute_result = brute_force()
	print("brute_force() took %s s" % (time.time() - start))
	for teller in range(len(epex_prijs)):
		print ("Bruut___uur %s, gaat HP %s, buf_init = %s, cost = %s, cum_cost = %s" % 
			(teller, 'AAN' if (brute_result[0] >> teller) & 1 == 1 else 'UIT', 
			round(brute_result[2][teller],2), round(brute_result[1][teller], 2), round(sum(brute_result[1][0:teller+1]), 2)))
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
