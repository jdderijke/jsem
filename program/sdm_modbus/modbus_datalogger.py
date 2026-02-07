from program.sdm_modbus import meter

class MODBUS_DATALOGGER(meter.Meter):
	pass


class DATALOGGER_1(MODBUS_DATALOGGER):
	def __init__(self, *args, **kwargs):
		self.model = "MODBUS_DATALOGGER"
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
			"vloer_flow_temp": (0, 1, meter.registerType.INPUT, meter.registerDataType.INT16, int, "Vloer Aanvoer Temp",
						   "°C", 1, 0.01),
			"vloer_ret_temp": (1, 1, meter.registerType.INPUT, meter.registerDataType.INT16, int, "Vloer Return Temp",
								"°C", 1, 0.01)
			}

