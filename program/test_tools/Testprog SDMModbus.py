import program.sdm_modbus
import pymodbus

if __name__ == "__main__":
	print (pymodbus.__version__)

	laadpaal = program.sdm_modbus.ALFEN_NG9xx(
		host='192.168.178.140',
		port=502,
		timeout=1,
		framer=None,
		unit=1,
		udp=False 
	)
	
	print(f"{laadpaal}:")
	
	# print(laadpaal.registers)
	
	print("\ndirect access excamples..")
	print(f"{laadpaal.read('l1_voltage')}")
	# print(f"{laadpaal.read('l2_voltage')}")
	# print(f"{laadpaal.read('l3_voltage')}")
	
	# print(f"{laadpaal.read('max_current_setpoint')}")
	# print(f"{laadpaal.read('setpoint_accepted')}")
	# print(f"{laadpaal.read('charging_phases')}")
	
	# print("\nInput Registers:")
	#
	# for k, v in laadpaal.read_all(program.sdm_modbus.registerType.INPUT, scaling=True).items():
	# 	address, length, rtype, dtype, vtype, label, fmt, batch, sf = laadpaal.registers[k]
	#
	# 	if type(fmt) is list or type(fmt) is dict:
	# 		print(f"\t{k}: {fmt[str(v)]}")
	# 	elif vtype is float:
	# 		print(f"\t{k}: {v:.2f}{fmt}")
	# 	else:
	# 		print(f"\t{k}: {v}{fmt}")

	print("\nWrite Holding register:")
	print(laadpaal.registers["max_current_setpoint"])
	# laadpaal._write(laadpaal.registers["max_current_setpoint"], 16768)
	laadpaal.write("max_current_setpoint", 16.0)
	print(laadpaal.read("max_current_setpoint"))

	# print("\nHolding Registers:")

	# for k, v in laadpaal.read_all(program.sdm_modbus.registerType.HOLDING, scaling=True).items():
	# 	address, length, rtype, dtype, vtype, label, fmt, batch, sf = laadpaal.registers[k]
	#
	# 	if type(v) is str:
	# 		print(f"\t{k}: {v}")
	# 	elif type(fmt) is list:
	# 		print(f"\t{k}: {fmt[v]}")
	# 	elif type(fmt) is dict:
	# 		print(f"\t{k}: {fmt[str(v)] if str(v) in fmt else fmt[v]}")
	# 	elif vtype is float:
	# 		print(f"\t{k}: {v:.2f}{fmt}")
	# 	else:
	# 		print(f"\t{k}: {v}{fmt}")

