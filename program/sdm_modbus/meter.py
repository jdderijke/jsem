import enum
import time

from pymodbus.constants import Endian
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.register_read_message import ReadInputRegistersResponse
from pymodbus.register_read_message import ReadHoldingRegistersResponse

class ModbusNotResponding(Exception):
	def __init__(self, msg:str='Modbus not responding...'):
		self.msg = msg
		super().__init__(self.msg)
		
	def __str__(self):
		return f'{self.msg}'

class connectionType(enum.Enum):
	RTU = 1
	TCP = 2


class registerType(enum.Enum):
	INPUT = 3
	HOLDING = 4
	COIL = 0
	DISCR_INPUT = 1


class registerDataType(enum.Enum):
	BIT = 0
	BITS16 = 1
	UINT8 = 2
	UINT16 = 3
	UINT32 = 4
	UINT64 = 5
	INT8 = 6
	INT16 = 7
	INT32 = 8
	INT64 = 9
	FLOAT16 = 10
	FLOAT32 = 11
	FLOAT64 = 12
	STRING = 13


RETRIES = 2
TIMEOUT = 1
UNIT = 1


class Meter:
	model = "Generic"
	registers = {}

	stopbits = 1
	parity = "N"
	baud = 38400

	wordorder = Endian.Big
	byteorder = Endian.Big

	def __init__(self, **kwargs):
		parent = kwargs.get("parent")

		if parent:
			self.client = parent.client
			self.mode = parent.mode
			self.timeout = parent.timeout
			self.retries = parent.retries

			unit = kwargs.get("unit")

			if unit:
				self.unit = unit
			else:
				self.unit = parent.unit

			if self.mode is connectionType.RTU:
				self.device = parent.device
				self.stopbits = parent.stopbits
				self.parity = parent.parity
				self.baud = parent.baud
			elif self.mode is connectionType.TCP:
				self.host = parent.host
				self.port = parent.port
			else:
				raise NotImplementedError(self.mode)
		else:
			self.timeout = kwargs.get("timeout", TIMEOUT)
			self.retries = kwargs.get("retries", RETRIES)
			self.unit = kwargs.get("unit", UNIT)

			device = kwargs.get("device")

			if device:
				self.device = device

				stopbits = kwargs.get("stopbits")

				if stopbits:
					self.stopbits = stopbits

				parity = kwargs.get("parity")

				if (parity
						and parity.upper() in ["N", "E", "O"]):
					self.parity = parity.upper()
				else:
					self.parity = False

				baud = kwargs.get("baud")

				if baud:
					self.baud = baud

				self.mode = connectionType.RTU
				self.client = ModbusSerialClient(
					method = 'rtu',
					port=self.device,
					stopbits=self.stopbits,
					parity=self.parity,
					baudrate=self.baud,
					timeout=self.timeout
				)
			else:
				self.host = kwargs.get("host")
				self.port = kwargs.get("port", 502)
				self.mode = connectionType.TCP

				self.client = ModbusTcpClient(
					host=self.host,
					port=self.port,
					timeout=self.timeout
				)

		self.connect()

	def __repr__(self):
		if self.mode == connectionType.RTU:
			return f"{self.model}({self.device}, {self.mode}: stopbits={self.stopbits}, parity={self.parity}, baud={self.baud}, timeout={self.timeout}, retries={self.retries}, unit={hex(self.unit)})"
		elif self.mode == connectionType.TCP:
			return f"{self.model}({self.host}:{self.port}, {self.mode}: timeout={self.timeout}, retries={self.retries}, unit={hex(self.unit)})"
		else:
			return f"<{self.__class__.__module__}.{self.__class__.__name__} object at {hex(id(self))}>"

	
	def _read_input_registers(self, address, length):
		for i in range(self.retries):
			if not self.connected():
				self.connect()
				time.sleep(0.1)
				continue
			
			result = self.client.read_input_registers(address=address, count=length, unit=self.unit)
			
			if not isinstance(result, ReadInputRegistersResponse):
				continue
			if len(result.registers) != length:
				continue

			return BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=self.byteorder, wordorder=self.wordorder)

		# raise ModbusNotResponding
		return None
	
	def _read_coils(self, address, length):
		for i in range(self.retries):
			if not self.connected():
				self.connect()
				time.sleep(0.1)
				continue

			result = self.client.read_coils(address, length)
			return result
		
		return None
	

	def _read_discr_inputs(self, address, length):
		for i in range(self.retries):
			if not self.connected():
				self.connect()
				time.sleep(0.1)
				continue
				
			result = self.client.read_discrete_inputs(address, length)
			return result
		
		return None

	def _read_holding_registers(self, address, length):
		for i in range(self.retries):
			if not self.connected():
				self.connect()
				time.sleep(0.1)
				continue

			result = self.client.read_holding_registers(address=address, count=length, unit=self.unit)

			if not isinstance(result, ReadHoldingRegistersResponse):
				continue
			if len(result.registers) != length:
				continue

			return BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=self.byteorder, wordorder=self.wordorder)

		# raise ModbusNotResponding
		return None

	def _write_coil(self, address, value):
		for i in range(self.retries):
			if not self.connected():
				self.connect()
				time.sleep(0.1)
				continue
				
			return self.client.write_coil(address=address, value=value, slave=self.unit)
		
		return None

	def _write_holding_register(self, address, value):
		for i in range(self.retries):
			if not self.connected():
				self.connect()
				time.sleep(0.1)
				continue

			return self.client.write_registers(address=address, values=value, slave=self.unit)
		
		return None

	def _encode_value(self, data, dtype, sf):
		builder = BinaryPayloadBuilder(byteorder=self.byteorder, wordorder=self.wordorder)
		sf = float(1/sf)
		try:
			if dtype == registerDataType.FLOAT64:
				builder.add_64bit_float(float(data) * sf)
			if dtype == registerDataType.FLOAT32:
				builder.add_32bit_float(float(data) * sf)
			elif dtype == registerDataType.INT64:
				builder.add_64bit_int(int(float(data) * sf))
			elif dtype == registerDataType.UINT64:
				builder.add_64bit_uint(int(float(data) * sf))
			elif dtype == registerDataType.INT32:
				builder.add_32bit_int(int(float(data) * sf))
			elif dtype == registerDataType.UINT32:
				builder.add_32bit_uint(int(float(data) * sf))
			elif dtype == registerDataType.INT16:
				builder.add_16bit_int(int(float(data) * sf))
			elif dtype == registerDataType.UINT16:
				builder.add_16bit_uint(int(float(data) * sf))
			elif dtype == registerDataType.STRING:
				builder.add_string(str(data))
			else:
				raise NotImplementedError(dtype)
		except NotImplementedError:
			raise

		return builder.to_registers()
	

	def _decode_value(self, data, length, rtype, dtype, vtype, fmt):
		"""
		This routine has been adapted for JSEM to include the fmt functionality where fmt is a list or
		dictionary and the value is the index in the list or the key in the dictionary
		The extra argument fmt was added. This routine is called by self._read and self._read_all
		"""
		try:
			tmp_value = None
			if rtype in[registerType.COIL, registerType.DISCR_INPUT]:
				# coils and discrete inputs are always first converted to integer
				tmp_value = int(data)
			elif dtype == registerDataType.BITS16:
				tmp_value = vtype(data.decode_16bit_uint())
			elif dtype == registerDataType.INT64:
				tmp_value = vtype(data.decode_64bit_int())
			elif dtype == registerDataType.UINT64:
				tmp_value = vtype(data.decode_64bit_uint())
			elif dtype == registerDataType.FLOAT32:
				tmp_value = vtype(data.decode_32bit_float())
			elif dtype == registerDataType.FLOAT64:
				tmp_value = vtype(data.decode_64bit_float())
			elif dtype == registerDataType.INT32:
				tmp_value = vtype(data.decode_32bit_int())
			elif dtype == registerDataType.UINT32:
				tmp_value = vtype(data.decode_32bit_uint())
			elif dtype == registerDataType.INT16:
				tmp_value = vtype(data.decode_16bit_int())
			elif dtype == registerDataType.UINT16:
				tmp_value = vtype(data.decode_16bit_uint())
			elif dtype == registerDataType.STRING:
				# Careful.. length is specified in words... not bytes or characters
				tmp_value = (data.decode_string(size=length * 2)).decode()
				# sometimes strings contain non ASCII characters, the build in decode_string then returns a bytestring
				tmp_value = tmp_value.replace('\x00', '')
			else:
				raise NotImplementedError(dtype)
			
			# See if the result must be presented as text
			if type(fmt) in [list, dict]:
				# only convert to string if so defined in the modbus register definitions
				tmp_value = self._convert_to_text(tmp_value, dtype, fmt)
			
			return tmp_value
		
		except NotImplementedError:
			raise
	
	def _convert_to_text(self, data, dtype, fmt):
		
		if dtype == registerDataType.BITS16 and type(fmt) is list:
			bin_str = format(data, '#016b')
			bin_str = bin_str[2:]  # get rid of 0b intro on string
			result = ''
			for i, bit in enumerate(bin_str[::-1]):
				# enumerate over the string BACKWARDS to get the bit numbering correct
				if int(bit) == 1:
					if len(fmt) > i + 1:
						result += f'| {fmt[i]}'
					else:
						result += f'| bit {i}={bit}'
			return result
		elif type(fmt) is dict:
			return fmt.get(data, "not_found")
		elif type(fmt) is list and type(data) is int:
			if data + 1 > len(fmt): raise IndexError("list index out of range")
			return fmt[data]
		else:
			# do nothing
			return data
	


	def _read(self, register):
		"""
		Returns the (unscaled) value of 1 entry from the datapoints register dictionary
		Any type of modbus datapoint will do: coils, discrete inputs, input registers or holding registers
		:param register:	The datapoint register entry to read
		:returns:		The unscaled value
		:raises		NotImplementedError for non-supported modbus register types
		"""
		address, length, rtype, dtype, vtype, label, fmt, batch, sf = register

		try:
			if rtype == registerType.INPUT:
				data = self._read_input_registers(address, length)
			elif rtype == registerType.HOLDING:
				data = self._read_holding_registers(address, length)
			elif rtype == registerType.COIL:
				data = self._read_coils(address, length)
			elif rtype == registerType.DISCR_INPUT:
				data = self._read_discr_inputs(address, length)
			else:
				raise NotImplementedError(rtype)
			
			if not data:
				return None
			
			if rtype in [registerType.COIL, registerType.DISCR_INPUT]:
				# coils and discrete inputs dont come in BinaryPayload decoder... just in a list
				return data.bits[0]
			else:
				return self._decode_value(data, length, rtype, dtype, vtype, fmt)
			
		except NotImplementedError:
			raise

	def _read_all(self, registers, rtype):
		"""
		Gets the values of all entries in the registers parameter, all entries must be of modbus register
		type of the rtype parameter.
		:param registers:	A (subset) of the modbus datapoint registers dictionary.
						All entries must be of the same register type (coil, discrete, input or holding)
		:param rtype:			The modbus register type of all entries in the registers parameter
		:returns:		A dictionary with the modbus datapoint name as key and its (unscaled) value
		:raises		NotImplementedError for non-supported modbus register types
		"""
		addr_min = False
		addr_max = False

		# Entries can be non-contingent in the address space. First calculate the lowest address and the length
		# of the modbus registers to read
		for k, v in registers.items():
			v_addr = v[0]
			v_length = v[1]

			if addr_min is False:
				addr_min = v_addr
			if addr_max is False:
				addr_max = v_addr + v_length

			if v_addr < addr_min:
				addr_min = v_addr
			if (v_addr + v_length) > addr_max:
				addr_max = v_addr + v_length

		results = {}
		offset = addr_min
		length = addr_max - addr_min
		# print(f'offset = {offset}, length = {length}')
		
		try:
			if rtype == registerType.INPUT:
				data = self._read_input_registers(offset, length)
			elif rtype == registerType.HOLDING:
				data = self._read_holding_registers(offset, length)
			elif rtype == registerType.COIL:
				data = self._read_coils(offset, length)
			elif rtype == registerType.DISCR_INPUT:
				data = self._read_discr_inputs(offset, length)
			else:
				raise NotImplementedError(rtype)

			if not data:
				return results
			
			for k, v in registers.items():
				address, length, rtype, dtype, vtype, label, fmt, batch, sf = v
				
				if rtype in [registerType.COIL, registerType.DISCR_INPUT]:
					# coils and discrete inputs dont come in BinaryPayload decoder... just in a list
					target_index = address-offset
					results[k] = self._decode_value(data.bits[target_index], length, rtype, dtype, vtype, fmt)
				else:
					# Because in BinaryPayload decoder reads data and moves to the next entry,
					# it will also read the data from registers that are not in the values parameter... to skip
					# those entries and still make use of the data decoding functionality of the payload decoder we have to
					# manually move the payload decoder further
					if address > offset:
						skip_bytes = address - offset
						offset += skip_bytes
						data.skip_bytes(skip_bytes * 2)
					results[k] = self._decode_value(data, length, rtype, dtype, vtype, fmt)
					offset += length
		except NotImplementedError:
			raise

		return results

	def _write(self, register, data):
		"""
		
		"""
		address, length, rtype, dtype, vtype, label, fmt, batch, sf = register

		try:
			if rtype == registerType.HOLDING:
				data = self._encode_value(data, dtype, sf)
				return self._write_holding_register(address, data)
			if rtype == registerType.COIL:
				if type(data) == str:
					data = data.lower() in ['on', 'aan', 'true', 'open', '1']
				elif type(data) in [bool, int, float]:
					data = bool(int(data))
				else:
					raise TypeError(f'Trying to write to coil with datatype: {type(data)}')
				
				return self._write_coil(address, data)
			else:
				raise NotImplementedError(rtype)
		except NotImplementedError:
			raise

	def connect(self):
		return self.client.connect()

	def disconnect(self):
		self.client.close()

	def connected(self):
		return self.client.is_socket_open()

	def get_scaling(self, key):
		address, length, rtype, dtype, vtype, label, fmt, batch, sf = self.registers[key]
		return sf

	def read(self, key, scaling=False):
		"""
		Reads and returns the value of the modbus register specified by the key parameter
		:param key:		The name (in the modbus register definition dictionary for this modbus device) of
						the register to read
		:param scaling:	Optionally return the scaled value
		:returns:		The (optionally scaled) value of the register.
		:raises			KeyError key not found in the modbus register definition dictionary
		"""
		if key not in self.registers:
			raise KeyError(key)

		data = self._read(self.registers[key])
		if not data: return None
		if scaling: return data * self.get_scaling(key)
		else: return data

	def write(self, key, data):
		"""
		Writes data to the modbus register specified by the key parameter, the data will be scaled before written.
		:param key:		The name (in the modbus register definition dictionary for this modbus device) of
						the register to write to
		:raises			KeyError key not found in the modbus register definition dictionary
		"""
		if key not in self.registers:
			raise KeyError(key)
		
		return self._write(self.registers[key], data)
		



	def read_all(self, rtype:registerType, scaling=False):
		"""
		Reads all registers from 1 specific modbus register type.
		The reads will be done in batches, registers with the same batch number will be read together
		:param rtype:	The modbus register type for which all registers (specified in the
						modbus register definition dictionary) will be read
		:param scaling:	Optionally scale the results
		:returns		A dictionary with the register names as keys and their (optionally scaled) values
		"""
		# registers = {k: v for k, v in self.registers.items() if (v[2] == rtype)}
		registers = {}
		for k,v in self.registers.items():
			if v[2] == rtype:
				registers[k] = v
		
		results = {}
		
		for batch in range(1, max(len(registers), 2)):
			register_batch = {k: v for k, v in registers.items() if (v[7] == batch)}

			if not register_batch:
				break

			results.update(self._read_all(register_batch, rtype))

		if scaling:
			return {k: v * self.get_scaling(k) for k, v in results.items()}
		else:
			return {k: v for k, v in results.items()}
