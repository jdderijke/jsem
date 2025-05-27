import time
import sdm_modbus


class TCPUDP_Emulator(object):
	def __init__(self, *args, **kwargs):
		self.blocking = True
		self.busfree_byte = kwargs.get('busfree_byte', bytearray([]))
		self.baudrate = kwargs.get('baudrate', 200)
		self.byte_time = 1 / (self.baudrate/10)
		self.echo = kwargs.get('echo', False)
		self.echo_buffer = bytearray([])
		pass
	
	def settimeout(self, timeout):
		pass
	
	def connect(self, *args, **kwargs):
		pass
	
	def bind(self, *args, **kwargs):
		pass
	
	def shutdown(self, *args, **kwargs):
		pass
	
	def close(self):
		pass
	
	def setblocking(self, blocking):
		self.blocking = blocking
		
	def recv(self, buffersize):
		if self.echo and self.echo_buffer:
			if len(self.echo_buffer) >= buffersize:
				response = self.echo_buffer[0:buffersize]
				self.echo_buffer = self.echo_buffer[buffersize:]
				# print(f'recv: response from echo_buffer: {ByteArrayToHexString(response)}, rest echo_buffer: {ByteArrayToHexString(self.echo_buffer)}')
				time.sleep(buffersize * self.byte_time)
				return bytearray(response)
			else:
				response=self.echo_buffer
				self.echo_buffer = bytearray([])
				return response
		
		if self.blocking:
			time.sleep(buffersize * self.byte_time)
			return bytearray(self.busfree_byte*buffersize)
		else:
			#TODO:	Generate an IOError with errno 11 to indicate empty buffer
			if self.busfree_byte == bytearray([]):
				# No busfree bytes
				raise IOError(11, "")
			else:
				time.sleep(self.byte_time)
				return self.busfree_byte
			
	def recvfrom(self, buffersize):
		return self.recv(buffersize), None

	def send(self, sendbytes):
		if self.echo:
			self.echo_buffer += sendbytes
			
		if self.blocking:
			# Emulate the sending of the bytes and block the thread while sending
			time.sleep(len(sendbytes) * self.byte_time)
			
		# print(f'send: echo_buffer: {ByteArrayToHexString(self.echo_buffer)}')
		return
	
	def sendto(self, sendbytes, *args, **kwargs):
		self.send(sendbytes)
		
	
	
class TCPModbus_Emulator(object):
	def __init__(self,	**kwargs):
		self.awake_registername = kwargs.get('awake_registername', None)
		self.is_connected = True
		self.input_registers = {'inp_1':1, 'inp_2':2}
		self.holding_registers = {'hol_1':11, 'hol_2':12}
	def close(self):
		self.is_connected = False
		
	def connected(self):
		return self.is_connected
	
	
	def read(self, registername):
		if registername == self.awake_registername: return 999999
		
		result = id(registername)
		print(f'Read {registername}, returns {result}')
		return result
	
	def read_all(self, register_type:sdm_modbus.registerType):
		if register_type == sdm_modbus.registerType.INPUT:
			return self.input_registers
		elif register_type == sdm_modbus.registerType.HOLDING:
			return self.holding_registers
		else:
			return {}
		
	def write(self, registername, value):
		if registername == self.awake_registername:
			print (f'Awake_register pinged with value {value}')
		
	
	
	
def ByteArrayToHexString(ByteArray):
	"""
	ByteArrayToHexString converts an array (list) of bytes into a hex string i.e. [1,5,15,10] into '01 05 FF 0A'
	"""
	# result = binascii.hexlify(bytearray(ByteArray)).upper()
	result = ' '.join('{:02x}'.format(x) for x in ByteArray).upper().strip()
	return result


if __name__ == '__main__':
	test = TCPUDP_Emulator(echo=True)
	test.setblocking(False)
	test.send(bytearray([0xFF, 0xBA, 0xBB]))
	try:
		while True:
			print(ByteArrayToHexString(test.recv(1)))
			input('any key..')
	except IOError as err:
		print (f'IOError with errno: {err.errno}')
		
		