#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Optimization_Routines.py
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
Deze set routines zijn hulproutines voor het berekenen van allerlei optimalisatie problemen
'''

def calculate_hc52_watersetpoint(outside_temperatures=[], thermostat_settings=[]):
	pass
	return
	
	
	
	
def calc_house_heat_usage(thermostaat=18, heatcurve=0.4):
	'''
	Haal eerst alle meetgegevens uit de DB voor watersetpoint_52 en Act_Power_01 en ook DayTempSetpoint_52 en HeatCurve_52 en de buitentemperatuur
	Al deze gegevens hebben timestamps, middel de gegevens op de serie met de laagste frequentie (de minste resultaten in de result dictionary)
	Middelen door de gegevens vanaf de traagste timestamp serie in de andere serie te middelen vanaf de vorige trage timestamp
	Dit levert gelijke dictionaries op qua lengte, allemaal even lang als de kortste serie en allemaal met de timestamp van die kortste serie.
	Gooi alle waardes weg waarbij de heatcurve niet correct is en/of de thermostaat niet correct is.
	Middel vervolgens de Power over de periodes dat de watersetpoint_52 constant is (niet wijzigt), nu ontstaat dus een serie
	met alleen verschillende watersetpoints en daarbij behorende power, noteer daar ook de bijbehorende buitentemperatuur bij...
	Maak een dictionary met watersetpoints als keys en power en buitentemp als value
	'''
	ws_52 = DATAPOINTS_NAME['WaterSetpoint_52']
	hc_52 = DATAPOINTS_NAME['HeatCurve_52']
	buitentemp = DATAPOINTS_NAME['BuitenTemperatuur1']
	thermostaat = DATAPOINTS_NAME['DayTempSetpoint_52']
	power_01 = DATAPOINTS_NAME['Act_Power_01']
	
	result=query_values_from_database("select timestamp,value from 'Values' where datapointID=%s order by timestamp asc" % ws_52.ID)
	return
	
	
	
def learn_house_heat_usage(outside_temperatures=[], windspeeds=[], hc52_watersetpoints=[], thermostat_settings=[]):
	'''
	Deze routine kijkt terug in de DB en berekent voor ieder hc52 watersetpoint (wat dus gerelateerd is aan de buitentemperatuur)
	het actuele gebruik (in Kw) van heet cv water door het huis en gastenverblijf. De routine returnt een dictionary met de 
	hc52 watersetpoints als key en het verbruik als value
	'''
	
	
def main(args):
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
