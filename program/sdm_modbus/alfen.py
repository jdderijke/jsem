from program.sdm_modbus import meter


class ALFEN(meter.Meter):
	pass



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

			"availability": (1200, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Availability", ["Inoperative","Operative"], 2, 1),
			# "availability": (1200, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Availability", {1:"Operative", 0: "Inoperative"}, 2, 1),
			
			# "mode_3_state": (1201, 5, meter.registerType.HOLDING, meter.registerDataType.STRING, str, "Mode 3 State",
							 # {"A":"A","B1":"B1","B2":"Finished charging","C1":"Vehicle connected", "C2":"Charging",
							  # "D1":"D1", "D2":"D2","E":"No vehicle connected", "F":"No vehicle connected"}, 2, 1),
			"mode_3_state": (1201, 5, meter.registerType.HOLDING, meter.registerDataType.STRING, str, "Mode 3 State", "", 2, 1),
			
			"actual_max_current": (1206, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Actual Max Current", "A", 2, 1),
			"remaining_valid_time": (1208, 2, meter.registerType.HOLDING, meter.registerDataType.UINT32, int, "Remaining Valid Time", "s", 2, 1),
			# "max_current_setpoint": (1210, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Max Current Setpoint", "A", 2, 1),
			"max_current_setpoint": (1210, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "Max Current Setpoint", "A", 2, 1),
			"alb_safe_current": (1212, 2, meter.registerType.HOLDING, meter.registerDataType.FLOAT32, float, "ALB Safe Current", "A", 2, 1),
			"setpoint_accepted": (1214, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Setpoit Accepted", "", 2, 1),
			"charging_phases": (1215, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Charging Phases", "", 2, 1)
		}

