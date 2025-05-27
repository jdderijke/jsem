#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Alfen.py
#  
#  Copyright 2024  <pi@raspberrypi>
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



from sdm_modbus import meter


class ALFEN(meter.Meter):
	pass


class ALFEN_NG9xx_info(ALFEN):

	def __init__(self, *args, **kwargs):
		self.model = "ALFEN_NG9xx_unit200"
		self.baud = 9600

		super().__init__(*args, **kwargs)

		'''
		De registers dictionary consists of the key:value pairs where the key is the name of the register and the value is a tuple consisting of:
		registeraddress, length, registertype, datatype, python_type, label, fmt, batch, scaling_factor
		
		met batch bepaal je welke registers bij een read_all in 1 sweep kunnen worden uitgelezen, bedenk hierbij dat 1 sweep
		maximaal 125 aaneengesloten adressen mag bevatten, 
		Dus: bij registers binnen dezelfde batch worden ook alle tussenliggende adressen uitgelezen door de read_all
		
		fmt: wordt NIET door sdm_modbus gebruikt, kan wel external gebruikt worden... bijvoorbeeld:
			als fmt een list of dictionary is dan kan de register value gebruikt worden als index (in geval van integer) of key...
			anders zal fmt als unit worden gezien
		scaling_factor: wordt alleen toegepast bij een read_all (wanneer expliciet scaling = True wordt meegegeven)
		'''
		self.registers = {
			"name": (100, 17, meter.registerType.HOLDING, meter.registerDataType.STRING, str, "Name", "", 1, 1),
			"timestamp": (117, 5, meter.registerType.HOLDING, meter.registerDataType.STRING, str, "Manufacturer", "", 1, 1),
			"modbus_table_version": (122, 1, meter.registerType.HOLDING, meter.registerDataType.INT16, int, "Modbus Table Version", "", 1, 1),
			"firmware_version": (123, 17, meter.registerType.HOLDING, meter.registerDataType.STRING, str, "Firmware Version", "", 1, 1),
			"platform_type": (140, 17, meter.registerType.HOLDING, meter.registerDataType.STRING, str, "Platform Type", "", 1, 1),
			"station_serial_number": (157, 11, meter.registerType.HOLDING, meter.registerDataType.STRING, str, "Station Serial Number", "", 1, 1),
			"year": (168, 1, meter.registerType.HOLDING, meter.registerDataType.INT16, int, "Year", "", 1, 1),
			"month": (169, 1, meter.registerType.HOLDING, meter.registerDataType.INT16, int, "Month", "", 1, 1),
			"day": (170, 1, meter.registerType.HOLDING, meter.registerDataType.INT16, int, "Day", "", 1, 1),
			"hour": (171, 1, meter.registerType.HOLDING, meter.registerDataType.INT16, int, "Hour", "", 1, 1),
			"minute": (172, 1, meter.registerType.HOLDING, meter.registerDataType.INT16, int, "Minute", "", 1, 1),
			"second": (173, 1, meter.registerType.HOLDING, meter.registerDataType.INT16, int, "Second", "", 1, 1),
			"uptime": (174, 4, meter.registerType.HOLDING, meter.registerDataType.UINT64, int, "Uptime", "ms", 1, 1),
			"time_zone": (178, 1, meter.registerType.HOLDING, meter.registerDataType.INT16, int, "Time Zone", "UTC offset (min)", 1, 1),
			
			"station_active_max_current": (1100, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Station Active Max Current", "A", 2, 1),
			"temperature": (1102, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Board Temperature", "C", 2, 1),
			"ocpp_state": (1104, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "OCPP State", "", 2, 1),
			"nr_sockets": (1105, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Nr Sockets", "", 2, 1),

			"scn_name": (1400, 4, meter.registerType.HOLDING, meter.registerDataType.STRING, str, "SCN Name", "", 3, 1),
			"scn_sockets": (1404, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, str, "SCN Sockets", "", 3, 1),
			"scn_l1_total_consumption": (1405, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "SCN L1 Total Consumption", "A", 3, 1),
			"scn_l2_total_consumption": (1407, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "SCN L2 Total Consumption", "A", 3, 1),
			"scn_l3_total_consumption": (1409, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "SCN L3 Total Consumption", "A", 3, 1),

			"scn_l1_actual_max_current": (1411, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "SCN L1 Actual Max Current", "A", 3, 1),
			"scn_l2_actual_max_current": (1413, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "SCN L2 Actual Max Current", "A", 3, 1),
			"scn_l3_actual_max_current": (1415, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "SCN L3 Actual Max Current", "A", 3, 1),

			"scn_l1_setpoint_max_current": (1417, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "SCN L1 Setpoint Max Current", "A", 3, 1),
			"scn_l2_setpoint_max_current": (1419, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "SCN L2 Setpoint Max Current", "A", 3, 1),
			"scn_l3_setpoint_max_current": (1421, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "SCN L3 Setpoint Max Current", "A", 3, 1),

			"scn_l1_remaining_valid_time": (1423, 2, meter.registerType.HOLDING, meter.registerDataType.UINT32, int, "SCN L1 Remaining Valid Time", "s", 3, 1),
			"scn_l2_remaining_valid_time": (1425, 2, meter.registerType.HOLDING, meter.registerDataType.UINT32, int, "SCN L2 Remaining Valid Time", "s", 3, 1),
			"scn_l3_remaining_valid_time": (1427, 2, meter.registerType.HOLDING, meter.registerDataType.UINT32, int, "SCN L3 Remaining Valid Time", "s", 3, 1),
			
			"scn_safe_current": (1429, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "SCN Safe Current", "A", 3, 1),
			"scn_modbus_slave_max_current_enable": (1431, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, 
																	"SCN Modbus Slave Max Current Enable", {0:'disabled', 1:'enabled'}, 3, 1)
			}





class ALFEN_NG9xx(ALFEN):

	def __init__(self, *args, **kwargs):
		self.model = "ALFEN_NG9xx_unit1"
		self.baud = 9600

		super().__init__(*args, **kwargs)

		'''
		De registers dictionary consists of the key:value pairs where the key is the name of the register and the value is a tuple consisting of:
		registeraddress, length, registertype, datatype, python_type, label, fmt, batch, scaling_factor
		
		met batch bepaal je welke registers bij een read_all in 1 sweep kunnen worden uitgelezen, bedenk hierbij dat 1 sweep
		maximaal 125 aaneengesloten adressen mag bevatten, 
		Dus: bij registers binnen dezelfde batch worden ook alle tussenliggende adressen uitgelezen door de read_all
		
		fmt: wordt NIET door sdm_modbus gebruikt, kan wel external gebruikt worden... bijvoorbeeld:
			als fmt een list of dictionary is dan kan de register value gebruikt worden als index (in geval van integer) of key...
			anders zal fmt als unit worden gezien
		scaling_factor: wordt alleen toegepast bij een read_all (wanneer expliciet scaling = True wordt meegegeven)
		'''
		self.registers = {
			"meter_state": (300, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Meter State", "", 1, 1),
			"timestamp": (301, 4, meter.registerType.HOLDING, meter.registerDataType.UINT64, int, "time since last measurement", "ms", 1, 1),
			"meter_type": (305, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Meter type", ["RTU", "TCP", "UDP", "P1", "other"], 1, 1),

			"l1_voltage": (306, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L1 Voltage", "V", 1, 1),
			"l2_voltage": (308, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L1 Voltage", "V", 1, 1),
			"l3_voltage": (310, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L1 Voltage", "V", 1, 1),

			# "l12_voltage": (312, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L1-L2 Voltage", "V", 1, 1),
			# "l23_voltage": (314, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L2-L3 Voltage", "V", 1, 1),
			# "l31_voltage": (316, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L3-L1 Voltage", "V", 1, 1),

			# "N_current": (318, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "N Current", "A", 1, 1),
			"l1_current": (320, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L1 Current", "A", 1, 1),
			"l2_current": (322, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L2 Current", "A", 1, 1),
			"l3_current": (324, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L3 Current", "A", 1, 1),
			# "total_current": (326, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Total Line Current", "A", 1, 1),

			# "l1_power_factor": (328, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L1 Power Factor", "", 1, 1),
			# "l2_power_factor": (330, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L2 Power Factor", "", 1, 1),
			# "l3_power_factor": (332, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L3 Power Factor", "", 1, 1),
			"total_pf": (334, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Total Power Factor", "", 1, 1),

			"frequency": (336, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Frequency", "Hz", 1, 1),
			
			# "l1_power_active": (338, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L1 Power (Active)", "W", 1, 1),
			# "l2_power_active": (340, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L2 Power (Active)", "W", 1, 1),
			# "l3_power_active": (342, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L3 Power (Active)", "W", 1, 1),
			"total_power": (344, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Total Power", "W", 1, 1),

			# "l1_power_apparent": (346, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L1 Power (Apparent)", "VA", 1, 1),
			# "l2_power_apparent": (348, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L2 Power (Apparent)", "VA", 1, 1),
			# "l3_power_apparent": (350, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L3 Power (Apparent)", "VA", 1, 1),
			# "total_power_apparent": (352, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Total Power (Apparent)", "VA", 1, 1),

			# "l1_power_reactive": (354, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L1 Power (Reactive)", "VAr", 1, 1),
			# "l2_power_reactive": (356, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L2 Power (Reactive)", "VAr", 1, 1),
			# "l3_power_reactive": (358, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "L3 Power (Reactive)", "VAr", 1, 1),
			# "total_power_reactive": (360, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Total Power (Reactive)", "VAr", 1, 1),

			# "L1_energy_delivered": (362, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L1 Energy Delivered", "Wh", 1, 1),
			# "L2_energy_delivered": (366, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L2 Energy Delivered", "Wh", 1, 1),
			# "L3_energy_delivered": (370, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L3 Energy Delivered)", "Wh", 1, 1),
			"total_energy_delivered": (374, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "Total Energy Delivered", "Wh", 1, 1),

			# "L1_energy_consumed": (378, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L1 Energy Consumed", "Wh", 1, 1),
			# "L2_energy_consumed": (382, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L2 Energy Consumed", "Wh", 1, 1),
			# "L3_energy_consumed": (386, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L3 Energy Consumed)", "Wh", 1, 1),
			# "total_energy_consumed": (390, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "Total Energy Consumed", "Wh", 1, 1),

			# "L1_energy_apparent": (394, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L1 Energy Apparent", "VAh", 1, 1),
			# "L2_energy_apparent": (398, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L2 Energy Apparent", "VAh", 1, 1),
			# "L3_energy_apparent": (402, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L3 Energy Apparent)", "VAh", 1, 1),
			# "total_energy_apparent": (406, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "Total Energy Apparent", "VAh", 1, 1),

			# "L1_energy_reactive": (410, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L1 Energy Reactive", "VArh", 1, 1),
			# "L2_energy_reactive": (414, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L2 Energy Reactive", "VArh", 1, 1),
			# "L3_energy_reactive": (418, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "L3 Energy Reactive)", "VArh", 1, 1),
			# "total_energy_reactive": (422, 4, meter.registerType.HOLDING, meter.registerDataType.FLOAT64, float, "Total Energy Reactive", "VArh", 1, 1),

			"availability": (1200, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Availability", {1:"Operative", 0: "Inoperative"}, 2, 1),
			"mode_3_state": (1201, 5, meter.registerType.HOLDING, meter.registerDataType.STRING, str, "Mode 3 State", "", 2, 1),
			"actual_max_current": (1206, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Actual Max Current", "A", 2, 1),
			"remaining_valid_time": (1208, 2, meter.registerType.HOLDING, meter.registerDataType.UINT32, int, "Remaining Valid Time", "s", 2, 1),
			"max_current_setpoint": (1210, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Max Current Setpoint", "A", 2, 1),
			"alb_safe_current": (1212, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "ALB Safe Current", "A", 2, 1),
			"setpoint_accepted": (1214, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Setpoit Accepted", "", 2, 1),
			"charging_phases": (1215, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Charging Phases", "", 2, 1)
		}

