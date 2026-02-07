from program.sdm_modbus import meter


class ALPHA_INNOTEC(meter.Meter):
	pass


class ALPHA_INNOTEC_SW172_H3(ALPHA_INNOTEC):
	def __init__(self, *args, **kwargs):
		self.model = "ALPHA_INNOTEC_SW172_H3"
		self.baud = 9600
		
		super().__init__(*args, **kwargs)
		
		'''
		De registers dictionary consists of the key:value pairs where the key is the name of the register and the value is a tuple consisting of:
		registeraddress, length, meter.registerType, datatype, python_type, label, fmt, batch, scaling_factor

		--------address, length, meter.registerType, datatype, python_type, label, fmt, batch, scaling_factor--------------

		met batch bepaal je welke registers bij een read_all in 1 sweep kunnen worden uitgelezen, bedenk hierbij dat 1 sweep
		maximaal 125 aaneengesloten adressen mag bevatten,
		Dus: bij registers binnen dezelfde batch worden ook alle tussenliggende adressen uitgelezen door de read_all

		fmt: wordt NIET door sdm_modbus gebruikt, kan wel external gebruikt worden... bijvoorbeeld:
			als fmt een list of dictionary is dan kan de register value gebruikt worden als index (in geval van integer) of key...
			anders zal fmt als unit worden gezien
		scaling_factor: wordt alleen toegepast bij een read_all (wanneer expliciet scaling = True wordt meegegeven)
		'''
		self.registers = {
			"butemp_gem": (0, 1, meter.registerType.INPUT, meter.registerDataType.INT16, int, "Gemiddelde Buiten Temp", "°C", 1, 0.1),
			"hp_buf_flow_temp": (1, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Actuele aanvoer temp naar buffervat", "°C", 1, 0.1),
			"hp_buf_ret_temp": (2, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Actuele returns temp vanaf buffervat", "°C", 1, 0.1),
			"buf_low_temp": (3, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Temperatuur onderin buffervat", "°C", 1, 0.1),
			"hc1_flow_temp": (5, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Menggroep1 actuele flow temperatuur", "°C", 1, 0.1),
			"hc2_flow_temp": (6, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Menggroep2 actuele flow temperatuur", "°C", 1, 0.1),
			"buf_high_temp": (7, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Temperatuur bovenin buffervat", "°C", 1, 0.1),

			"warmgas_temp": (8, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Warmgas temperatuur", "°C", 1, 0.1),

			"brine_flow_temp": (9, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Brine aanvoer temperatuur", "°C", 1, 0.1),
			"brine_ret_temp": (10, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Brine return temperatuur", "°C", 1, 0.1),

			"open_bron_flow_temp": (14, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Bron aanvoer temperatuur", "°C", 1, 0.1),
			"open_bron_ret_temp": (15, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Bron return temperatuur", "°C", 1, 0.1),

			"compr_aanz_temp": (19, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Temperatuur aanzuiging cxompressor", "°C", 1, 0.1),
			"evap_aanz_temp": (20, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Temperatuur aanzuiging verdamper", "°C", 1, 0.1),
			"overheat_act": (22, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Oververhitting", "°C", 1, 0.1),
			"overheat_setp": (23, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Setpoint oververhitting", "°C", 1, 0.1),

			"roomtemp_act": (24, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "RBE ruimtetemperatuur actueel", "°C", 1, 0.1),
			"roomtemp_setp": (25, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "RBE ruimtetemperatuur setpoint", "°C", 1, 0.1),

			"highpress": (26, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Druk HD", "Bar", 1, 0.1),
			"lowpress": (27, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Druk LD", "Bar", 1, 0.1),

			"compr_hours": (28, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Bedrijfsuren compressor", "h", 1, 1),
			"hp_hours": (33, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Bedrijfsuren warmtepomp", "h", 1, 1),

			"hp_status": (37, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "hp status",
						  {0 :"verwarmen", 1: "warm_tapwater", 2: "zwembad", 3: "EVU_blokkering",
						   4: "ontdooien", 5: "uit", 6: "externe_energiebron", 7: "koeling"}, 1, 1),


			"total_heating_energy": (38, 2, meter.registerType.INPUT, meter.registerDataType.INT32, int, "Cumul verwarmings energie", "kWh", 1, 0.1),
			"Act_hp_power": (47, 1, meter.registerType.INPUT, meter.registerDataType.UINT16, int, "Actueel vermogen", "kW", 1, 0.01),
			"total_cooling_energy": (48, 2, meter.registerType.INPUT, meter.registerDataType.INT32, int, "Cumul verwarmings energie", "kWh", 1, 0.1),
			"total_heating_electr": (50, 2, meter.registerType.INPUT, meter.registerDataType.INT32, int, "Cumul verwarmings electriciteit", "kWh", 1, 0.1),
			"total_cooling_electr": (54, 2, meter.registerType.INPUT, meter.registerDataType.INT32, int, "Cumul koeling electriciteit", "kWh", 1, 0.1),


			"butemp": (0, 1, meter.registerType.HOLDING, meter.registerDataType.INT16, int, "Buitentemperatuur", "°C", 1, 0.1),
			"hp_buf_ret_temp_setp": (1, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Retour temp vanaf buffervat setpoint", "°C", 1, 0.1),
			"hc1_flow_temp_setp": (2, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Menggroep1 flow temp setpoint", "°C", 1, 0.1),
			"hc2_flow_temp_setp": (3, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Menggroep2 flow temp setpoint", "°C", 1, 0.1),

			"hp_block": (6, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Blokkering/vrijgave warmtepomp",
						 {0 :"0: blok_wrmtepmp", 1 :"1: vrijgave_cmp1", 2 :"2: vrijgave_cmp2"}, 1, 1),

			"mode_verwarmen": (7, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Bedrijfsmode verwarmen",
							   {0 :"0: autom", 1 :"1: 2e_opw", 2 :"2: party", 3 :"3: vakantie", 4 :"4: uit"}, 1, 1),

			"mode_menggroep2": (9, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Bedrijfsmode menggroep2",
								{0 :"0: autom", 1 :"1: 2e_opw", 2 :"2: party", 3 :"3: vakantie", 4 :"4: uit"}, 1, 1),

			"mode_koeling": (11, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Bedrijfsmode koeling",
							 {0 :"0: uit", 1 :"1: autom"}, 1, 1),

			"smart_grid": (14, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Smart Grid Status",
						   {0 :"0: EVU_blok", 1 :"1: sg_low", 2 :"2: standard", 3 :"3: sg_high"}, 1, 1),

			"sl_verw_eindpunt": (15, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Stooklijn verwarming eindpunt", "°C", 1, 0.1),
			"sl_verw_versch": (16, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Stooklijn verwarming parallel verschuiving", "°C", 1, 0.1),
			"sl_hc1_eindpunt": (17, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Stooklijn menggroep1 eindpunt", "°C", 1, 0.1),
			"sl_hc1_versch": (18, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Stooklijn menggroep1 parallel verschuiving", "°C", 1, 0.1),
			"sl_hc2_eindpunt": (19, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Stooklijn menggroep2 eindpunt", "°C", 1, 0.1),
			"sl_hc2_versch": (20, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Stooklijn menggroep2 parallel verschuiving", "°C", 1, 0.1),
			"sl_hc3_eindpunt": (21, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Stooklijn menggroep3 eindpunt", "°C", 1, 0.1),
			"sl_hc3_versch": (22, 1, meter.registerType.HOLDING, meter.registerDataType.UINT16, int, "Stooklijn menggroep3 parallel verschuiving", "°C", 1, 0.1),
			"sl_temp_corr": (23, 1, meter.registerType.HOLDING, meter.registerDataType.INT16, int, "Stooklijn temperatuur correctie", "°C", 1, 0.1),

			# coils
			"FLT_RESET": (0, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "Bevestig actieve foutcode", "", 1, 1),
			"HUP": (2, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "CV circulatiepomp (niet in gebruik)", "", 1, 1),
			"VEN": (3, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "Ventilator", "", 1, 1),
			"ZUP": (4, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "CV pomp hp_buf", "", 1, 1),
			"BUP": (5, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "Circ pomp warm tapwater", "", 1, 1),
			"BOSUP": (6, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "Bronpomp", "", 1, 1),
			"ZIP": (7, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "Circ pomp warm tapwater", "", 1, 1),
			"FUP2": (8, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "2e circ pomp woning", "", 1, 1),
			"FUP3": (9, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "3e circ pomp woning", "", 1, 1),
			"SLP": (10, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "Pomp zon-collector", "", 1, 1),
			"SUP": (11, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "Circ pomp zwembad", "", 1, 1),
			"VSK": (12, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "Bypassklep", "", 1, 1),
			"FRH": (13, 1, meter.registerType.COIL, meter.registerDataType.BIT, bool, "Relais defrost verwarming", "", 1, 1),

			# Discrete inputs
			"EVU": (0, 1, meter.registerType.DISCR_INPUT, meter.registerDataType.BIT, bool, "Sper agv energie maatsch", "", 1, 1),
			"EVU2": (1, 1, meter.registerType.DISCR_INPUT, meter.registerDataType.BIT, bool, "Sper agv energie maatsch", "", 1, 1),
			"SWT": (2, 1, meter.registerType.DISCR_INPUT, meter.registerDataType.BIT, bool, "Thermostaat zwembad", "", 1, 1),
			"VD1": (3, 1, meter.registerType.DISCR_INPUT, meter.registerDataType.BIT, bool, "Compressor 1", "", 1, 1),
			"VD2": (4, 1, meter.registerType.DISCR_INPUT, meter.registerDataType.BIT, bool, "Compressor 2", "", 1, 1),
			"ZWE1": (5, 1, meter.registerType.DISCR_INPUT, meter.registerDataType.BIT, bool, "Xtra warmte opwekker", "", 1, 1),
			"ZWE2": (6, 1, meter.registerType.DISCR_INPUT, meter.registerDataType.BIT, bool, "Xtra warmte opwekker", "", 1, 1),
			"ZWE3": (7, 1, meter.registerType.DISCR_INPUT, meter.registerDataType.BIT, bool, "Xtra warmte opwekker", "", 1, 1)
		}

