import datetime
import time
import sdm_modbus
import socket as prod_socket

from Config import ENVIRONMENT
from Common_Enums import *

class Socket(prod_socket.socket):
	"""
	In normal operation (ENVIRONMENT=Productie) this socket is just a regular socket.socket instance
	In full test operation (ENVIRONMENT=Test_full) this socket EMULATES a socket.socket instance
	"""
	AF_INET = prod_socket.AF_INET
	SOCK_STREAM = prod_socket.SOCK_STREAM
	SOCK_DGRAM = prod_socket.SOCK_DGRAM
	SHUT_RDWR = prod_socket.SHUT_RDWR
	
	def __init__(self, *args, **kwargs):
		if ENVIRONMENT == Environment.Productie:
			super().__init__(*args)
		
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

class Modbus(object):
	def __init__(self,	**kwargs):
		self.awake_registername = kwargs.pop('awake_registername', None)
		if ENVIRONMENT == Environment.Productie:
			initializer = getattr(sdm_modbus, kwargs.pop('device_type'))
			initializer(**kwargs)
			return
		
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
			# print (f'Awake_register pinged with value {value}')
			pass




# import serial
# from datetime import datetime

class Serial_Emulator(object):
	dummy_sample = """This is sample transmission
	Using the Serial Emulator
	Emulating the esmr50 interface
	This is NO real data
	Since mimicking real data would lead to DB storage
	of datapoints....
	If you want to test with REAL data
	then start the Serial_Emulator with the for_real=True
	argument.
	!
	"""
	esmr50_realdata_sample = """/Ene5\T211 ESMR 5.0 1-3:0.2.8(50)
	0-0:1.0.0(250528103113S)
	0-0:96.1.1(4530303632303030303033313336373231)
	1-0:1.8.1(022829.455*kWh)
	1-0:1.8.2(012399.513*kWh)
	1-0:2.8.1(001992.935*kWh)
	1-0:2.8.2(004507.887*kWh)
	0-0:96.14.0(0002)
	1-0:1.7.0(00.721*kW)
	1-0:2.7.0(01.519*kW)
	0-0:96.7.21(00015)
	0-0:96.7.9(00009)
	1-0:99.97.0(2)(0-0:96.7.19)(240507143439S)(0000000801*s)(221118121252W)(0000000404*s)
	1-0:32.32.0(00003)
	1-0:52.32.0(00004)
	1-0:72.32.0(00003)
	1-0:32.36.0(00004)
	1-0:52.36.0(01912)
	1-0:72.36.0(00521)
	0-0:96.13.0()
	1-0:32.7.0(243.0*V)
	1-0:52.7.0(245.0*V)
	1-0:72.7.0(240.0*V)
	1-0:31.7.0(000*A)
	1-0:51.7.0(006*A)
	1-0:71.7.0(003*A)
	1-0:21.7.0(00.013*kW)
	1-0:41.7.0(00.000*kW)
	1-0:61.7.0(00.708*kW)
	1-0:22.7.0(00.000*kW)
	1-0:42.7.0(01.519*kW)
	1-0:62.7.0(00.000*kW)
	0-1:24.1.0(003)
	0-1:96.1.0(4730303538353330303432353538383230)
	0-1:24.2.1(250528103000S)(00273.506*m3)
	!
	"""
	
	def __init__(self, for_real=False):
		self.for_real = for_real
		self.baudrate = 115200
		self.bytesize = 8
		self.parity = 'N'
		self.stopbits = 1
		self.xonxoff = 0
		self.rtscts = 0
		self.timeout = 20
		# bit confusing but with port a serial COM port is expected, i.e. /dev/ttyUSB0...
		self.port = '/dev/ttyUSB0'
		self.is_open = False
		self.gen = self.generator()
		self.keep_generating = False
		
		
	def open(self):
		self.is_open=True
		self.keep_generating = True
		
	def close(self):
		self.is_open=False
		self.keep_generating = False

	def readline(self):
		if self.is_open:
			try:
				time.sleep(0.1)
				result = next(self.gen)
				return result
			except StopIteration:
				time.sleep(1.0)
				self.flushInput()
		else:
			raise ConnectionError('Serial connection is not open')
	
	def flushInput(self):
		self.gen = self.generator()
	
	def generator(self):
		sample = Serial_Emulator.esmr50_realdata_sample if self.for_real else Serial_Emulator.dummy_sample
		for teller, line in enumerate(sample.splitlines()):
			# Yield a bytes object
			result =  bytes(line, 'utf-8')
			yield result


class device():
	def __init__(self, device_type):
		self.device_type = device_type
		self.state = 0
		
	def turn_on(self):
		self.state = 1
	
	def turn_off(self):
		self.state = 0

class Shelly_Emulator(object):
	def __init__(self):
		self.devices = []
	
	def start(self):
		pass
	
	def add_device_by_ip(self, id, src):
		self.devices = [device('RELAY'), device('SWITCH'), device('SWITCH')]
	
	
	
def ByteArrayToHexString(ByteArray):
	"""
	ByteArrayToHexString converts an array (list) of bytes into a hex string i.e. [1,5,15,10] into '01 05 FF 0A'
	"""
	# result = binascii.hexlify(bytearray(ByteArray)).upper()
	result = ' '.join('{:02x}'.format(x) for x in ByteArray).upper().strip()
	return result



if __name__ == '__main__':
	
	# Test Serial_Emulator
	print ('Cntrl-C to flush inputbuffer (reset), cntrl-C twice to exit...')
	print ()
	test = Serial_Emulator()
	test.open()
	while True:
		try:
			print(f'>>>>> {test.readline()}')
		except KeyboardInterrupt:
			try:
				test.flushInput()
				time.sleep(0.5)
			except KeyboardInterrupt:
				break
	test.close()
	
	
	# # TCPUDP_Emulator test
	# test = TCPUDP_Emulator(echo=True)
	# test.setblocking(False)
	# test.send(bytearray([0xFF, 0xBA, 0xBB]))
	# try:
	# 	while True:
	# 		print(ByteArrayToHexString(test.recv(1)))
	# 		input('any key..')
	# except IOError as err:
	# 	print (f'IOError with errno: {err.errno}')
		
	pass