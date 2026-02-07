from program.sdm_modbus import meter


class SOLIS(meter.Meter):
	pass
	

class SOLIS3P5K_4G(SOLIS):
	def __init__(self, *args, **kwargs):
		self.model = "SOLIS3P5K_4G"
		self.baud = 9600
		
		super().__init__(*args, **kwargs)

		'''
		De registers dictionary consists of the key:value pairs where the key is the name of the register and the value is a tuple consisting of:
		registeraddress, length, registertype, datatype, python_type, label, fmt, batch, scaling_factor
		
		--------address, length, registertype, datatype, python_type, label, fmt, batch, scaling_factor--------------
		
		met batch bepaal je welke registers bij een read_all in 1 sweep kunnen worden uitgelezen, bedenk hierbij dat 1 sweep
		maximaal 125 aaneengesloten adressen mag bevatten, 
		Dus: bij registers binnen dezelfde batch worden ook alle tussenliggende adressen uitgelezen door de read_all
		
		fmt: wordt NIET door sdm_modbus gebruikt, kan wel external gebruikt worden... bijvoorbeeld:
			als fmt een list of dictionary is dan kan de register value gebruikt worden als index (in geval van integer) of key...
			anders zal fmt als unit worden gezien
		scaling_factor: wordt alleen toegepast bij een read_all (wanneer expliciet scaling = True wordt meegegeven)
		'''
		self.registers = {
			"product_model": (2999, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Product Model", "", 1, 1),
			"dsp_sw_version": (3000, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "DSP SW Version", "", 1, 1),
			"lcd_sw_version": (3001, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "LCD SW Version", "", 1, 1),
			"ac_output_type": (3002, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "AC Output Type", 
									{0:"single", 1: "3P4_wires", 2: "3P3_wires", 3: "3P4_or_3P3"}, 1, 1),
			"dc_input_type": (3003, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "DC Input Type", 
									{0:"1_dc_input", 1:"2_dc_inputs", 2:"3_dc_inputs", 3:"4_dc_inputs"}, 1, 1),
			
			"active_power": (3004, 2, meter.registerType.INPUT, meter.registerDataType.UINT32, int, "Active Power", "W", 1, 0.001),
			"dc_power": (3006, 2, meter.registerType.INPUT, meter.registerDataType.UINT32, int, "DC Power", "W", 1, 0.001),
			"total_energy": (3008, 2, meter.registerType.INPUT, meter.registerDataType.UINT32, int, "Total Energy", "kWh", 1, 1),
			"energy_this_month": (3010, 2, meter.registerType.INPUT, meter.registerDataType.UINT32, int, "Energy This Month", "kWh", 1, 1),
			"energy_last_month": (3012, 2, meter.registerType.INPUT, meter.registerDataType.UINT32, int, "Energy Last Month", "kWh", 1, 1),
			"energy_today": (3014, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Energy Today", "kWh", 1, 0.1),
			"energy_yesterday": (3015, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Energy Yesterday", "kWh", 1, 0.1),
			"energy_this_year": (3016, 2, meter.registerType.INPUT, meter.registerDataType.UINT32, int, "Energy This Year", "kWh", 1, 1),
			"energy_last_year": (3018, 2, meter.registerType.INPUT, meter.registerDataType.UINT32, int, "Energy Last Year", "kWh", 1, 1),
			

			"dc1_voltage": (3021, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "L1-L2 Voltage", "V", 1, 0.1),
			"dc1_current": (3022, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "L3-L1 Voltage", "A", 1, 0.1),
			"dc2_voltage": (3023, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "L2-L3 Voltage", "V", 1, 0.1),
			"dc2_current": (3024, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "L3-L1 Voltage", "A", 1, 0.1),

			"l1_voltage": (3033, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "L1 Voltage", "V", 1, 0.1),
			"l2_voltage": (3034, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "L1 Voltage", "V", 1, 0.1),
			"l3_voltage": (3035, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "L1 Voltage", "V", 1, 0.1),

			"l1_current": (3036, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "L1 Current", "A", 1, 0.1),
			"l2_current": (3037, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "L2 Current", "A", 1, 0.1),
			"l3_current": (3038, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "L3 Current", "A", 1, 0.1),
			
			"frequency": (3042, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, float, "Frequency", "Hz", 1, 0.01),
			
			"inverter_status": (3043, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Inverter Status", 
					{0:"Waiting",1:"Openrun",2:"Softrun",3:"Generating",61456:"Grid Surge Alarm", 61457:"FAN Fault", 61459:"AC SPD Error", 61460:"DC SPD Error"}, 1, 1),

			"fault_code_01": (3066, 1, meter.registerType.INPUT, meter.registerDataType.BITS16, int, "Fault Code 01", "", 1, 1),
			"fault_code_02": (3067, 1, meter.registerType.INPUT, meter.registerDataType.BITS16, int, "Fault Code 02", "", 1, 1),
			"fault_code_03": (3068, 1, meter.registerType.INPUT, meter.registerDataType.BITS16, int, "Fault Code 03", "", 1, 1),
			"fault_code_04": (3069, 1, meter.registerType.INPUT, meter.registerDataType.BITS16, int, "Fault Code 04", "", 1, 1),
			"fault_code_05": (3070, 1, meter.registerType.INPUT, meter.registerDataType.BITS16, int, "Fault Code 05", "", 1, 1),
			"working_status": (3071, 1, meter.registerType.INPUT, meter.registerDataType.BITS16, int, "Working Status", 
					["normal","Initializing","Grid_Off","Fault_to_Stop","Standby","Derating","Limitating","Backup_OV_Load","Grid_Surge",
					 "Fan_Fault","","AC_SPD_Err","DC_SPD_Err","","",""], 1, 1),
					

			"power_limitation": (3051, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, float, "Power Limitation", "%", 1, 0.01)
		
		}

