#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Conversion_Routines.py
#  
#  Copyright 2022  <pi@raspberrypi>
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
import __main__
if __name__ == "__main__": __main__.logfilename = "Conversion_Routines.log"

from datetime import datetime
# from LogRoutines import Logger
from collections import OrderedDict
from pyModbusTCP.utils import decode_ieee, encode_ieee
import csv
import socket

def csv_to_ordereddict(csvfile, sep=",", indexfield=None):
	result = OrderedDict()
	with open(csvfile, mode='r') as csv_file:
		# wrinfo ("Opened cvs file "+ csvfile + " to read.")
		csv_reader = csv.DictReader(csv_file, delimiter=sep)
		print (csv_reader.fieldnames)
		line_count = 0
		for row in csv_reader:
			# check if we need to use a field from the csv file as a unique key / rowindex, if not we will use the line_count
			if indexfield is None:
				newrowindex = line_count
			else:
				newrowindex = row[indexfield]
				
			result[newrowindex] = OrderedDict()
			
			# csv_reader fucks up the order of the fields, therefore we need to manually create each entry in the result
			# the .fieldnames attribute in the reader has the correct fieldname order
			for item in csv_reader.fieldnames:
				result[newrowindex][item] = row[item]
				
			line_count += 1
		# wrinfo("Processed " + str(line_count) + " lines.") 
	return result


"""
Conversion Routines

"""



def From_ASCII(data):
	try:
		datastring = str(data, 'ascii')
		return datastring
	except Exception as err:
		Logger.error("From_ASCII failed on inputdata: %s" % data)
		Logger.exception(str(err))
	
def From_BINSTR(data):
	try:
		# data is een bytearray van 0 of meer bytes:
		result = ''
		for x in data:
			result += bin(x)[2:] + ' '
		return result.strip()
	except Exception as err:
		Logger.exception(str(err))
		return None
	
def From_HEXSTR(data):
	try:
		# data is een bytearray van 0 of meer bytes:
		return ByteArrayToHexString(data)
	except Exception as err:
		Logger.exception(str(err))
		return None
	
	
def From_BCD(num):
	# BDC uses 4 bits per digit (0-9), to decode take 10* the high nibble(4bits) and add the low nibble
	try:
		if num > 255: raise Exception("Invalid input for conversion....num > 255")
		highnibble = (num & 0x00F0) >> 4
		if highnibble > 9: raise Exception("Invalid input for conversion....highnibble > 9")
		lownibble = num & 0x000F
		if lownibble > 9: raise Exception("Invalid input for conversion....lownibble > 9")
		return 10*highnibble + lownibble
	except Exception as err:
		Logger.exception(str(err))
		
def To_ASCII(inputstr):
	return inputstr
		
def To_BCD(num):
	num = int(num)
	# num is gewoon een integer16
	try:
		if num > 99 or num < 0:
			raise Exception("Invalid ToBCD conversion: Input = " + str(num))
		else:
			lownibble = num % 10
			highnibble = (num - (num % 10)) / 10
			return (highnibble << 4) + lownibble
	except Exception as err:
		Logger.exception(str(err))
	
	
def From_DATA1B(num):
	try:
		if num > 255: raise Exception("Invalid input for conversion....num > 255")
		if num == 128: return -128
		elif num > 128: return -128 + (num-128)
		else: return num
	except Exception as err:
		raise Exception("From_DATA1B: " + str(err))

def To_DATA1B(num):
	num = int(num)
	try:
		if num > 127 or num < -128:
			raise Exception("Invalid ToData1B conversion: Input = " + str(num))
		else:
			if num < 0:
				return (128 + num) + 128
			else:
				return num
	except Exception as err:
		Logger.error(str(err))


	
def From_DATA1C(num):
	try:
		if (num/2) > 100: raise Exception("Invalid input for conversion....(num/2) > 100")
		else:
			return float(num)/2
	except Exception as err:
		raise Exception("From_DATA1C: " + str(err))


def To_DATA1C(num):
	num = int(num)
	try:
		if num < 0 or num > 100:
			raise Exception("Invalid ToData1C conversion: Input = " + str(num))
		else:
			# Afronden en converteren
			return int(num * 2)
	except Exception as err:
		Logger.error(str(err))




def From_BIN8(num):
	try:
		if num > 255: raise Exception("Invalid input for conversion....num > 255")
		return '{:08b}'.format(num)
	except Exception as err:
		raise Exception("From_BIN8: " + str(err))
		
def From_BIN16(num):
	try:
		if num > 65535: raise Exception("Invalid input for conversion....num > 65535")
		return '{:016b}'.format(num)
	except Exception as err:
		raise Exception("From_BIN16: " + str(err))

			
def From_DATA2B(num):
	'''
	In this coding the low byte containes the post comma digits (in 1/256 increments)
	This leads to a range of -128 to + 127.996
	'''
	try:
		highbyte = num >> 8
		lowbyte = num & 0x00FF
		return float(From_DATA1B(highbyte) + (float(lowbyte)/256))
	except Exception as err:
		raise Exception("From_DATA2B: " + str(err))
		
def To_DATA2B(num):
	try:
		# make sure we deal with a float number
		num = float(num)
		# round to the nearest 1/256 fraction
		num = round(num/0.00390625)*0.00390625
		pass
	except Exception as err:
		raise Exception("To_DATA2B: " + str(err))
	
	
	

def From_DATA2C(num):
	'''
	In this coding the low nibble of the input represents the numbers after the decimal point (in 1/16 increments)
	This leads to a range of -2047.9 to +2048
	'''
	try:
		lowbyte = num & 0x00FF
		lownibble = lowbyte & 0xF
		highnibble = (lowbyte & 0xF0) >> 4
		if num >= 32768:
			# negatief getal
			highbyte = (num-32768) >> 8
			return float(-2048 + highbyte*16 + highnibble + (float(lownibble)/16))
		else:
			# positief getal
			highbyte = num >> 8
			return float(highbyte * 16 + highnibble +(float(lownibble)/16))
	except Exception as err:
		raise Exception("From_DATA2C: " + str(err))
		
def To_DATA2C(num):
	try:
		# make sure we deal with a float number
		num = float(num)
		# round to the nearest 1/16 fraction
		num = round(num/0.0625)*0.0625
		if num >= 0:
			# positief getal
			fraction = num - int(num)
			lownibble = int(fraction/0.0625)
			result = (int(num)<<4) + lownibble
		else:
			# negatief getal
			num += 2048
			fraction = num - int(num)
			lownibble = int(fraction/(1/16))
			result = (int(num)<<4) + lownibble
			result = result | 0x8000
		return result
	except Exception as err:
		raise Exception("To_DATA2C: " + str(err))
		
	

def From_INT32REV(num):
	return num
	
def From_INT16REV(num):
	return num & 0x0000FFFF
	
def From_FLOAT32(num):
	try:
		# num must be a LONG word (32 bits long), clip to 32 bits
		num2 = num & 0xFFFFFFFF
		if num2 != num: raise Exception("Conversion Error, argument must be long_word (32bits)")
		return decode_ieee(num2)
	except Exception as err:
		raise Exception("From_FLOAT32: " + str(err))

def From_FLOAT64(num):
	try:
		# num must be a LONG word (64 bits long), clip to 64 bits
		num2 = num & 0xFFFFFFFFFFFFFFFF
		if num2 != num: raise Exception("Conversion Error, argument must be long_word (32bits)")
		return decode_ieee(num2, double=True)
	except Exception as err:
		raise Exception("From_FLOAT32: " + str(err))



def To_FLOAT32(num):
	try:
		return encode_ieee(num)
	except Exception as err:
		raise Exception("To_FLOAT32: " + str(err))


	
def From_INT16(num):
	return num & 0x0000FFFF
	
def To_INT16REV(num):
	return int(num)
	
def To_INT16(num):
	return int(num)
	
def From_INT8(num):
	return num & 0x000000FF

def To_INT8(num):
	# print ("To_INT8 called")
	return int(num)





		
def From_HEX8(hexstring):
	return hexstring 
	 
def From_HEX16(hexstring):
	return hexstring  
  
def From_EBUSDATETIME(databytes):
	second=From_BCD(databytes[0])
	minute=From_BCD(databytes[1])
	hour=From_BCD(databytes[2])
	day=From_BCD(databytes[3])
	month=From_BCD(databytes[4])
	dayofweek=From_BCD(databytes[5])
	year=From_BCD(databytes[6])
	
	# print ("From_EBUSDATETIME----CALLED:  " + str(hour) + str(minute) + str(second))
	
	return str(datetime((2000+year), month, day, hour, minute, second))
	
def From_MBUSDATETIME(databytes):
	# print ("From_MBUSDATETIME received: " + str(databytes))
	minute = int(databytes[0]) & 0x003F
	hour = int(databytes[1]) & 0x001F
	day = int(databytes[2]) & 0x001F
	month = int(databytes[3]) & 0x000F
	# dont know if the following logic makes any sense....
	tmp = (int(databytes[2]) & 0x00E0) >> 1
	tmp2 = (int(databytes[3]) & 0x00F0) >> 4
	# the | operator stands for bitwise OR, the ^ operator stands for bitwise XOR
	year = tmp | tmp2
	return str(datetime((2000-46+year), month, day, hour, minute, 0))
	
def From_STATUS(num):
	if num == 0: return "OK"
	elif num == 1: return "ERROR"
	else: return "NONE"
	
def From_PUMPPOWER(num):
	if num == 7: return "OFF"
	else: return str(float(num))
	
def From_ONOFF(num):
	if num == 0: return "OFF"
	elif num == 1: return "ON"
	else: return "ERROR"
	
def From_EBUSID(databytes):
	id_string = ""
	databytes = databytes.strip().split(" ")
	# print ("From_EBUSID called with databytes: ", databytes)
	if databytes[0]=="B5":
		id_string += "Vaillant"
	else: 
		id_string += "Code " + databytes[0]
		
	for teller in range(1,6):
		id_string += chr(int(databytes[teller], 16))
		
	id_string += ",S:"
	for teller in range(6,8):
		tmp = int(databytes[teller], 16)
		id_string += str(From_BCD(tmp)) + "."
	id_string.strip(".")
	
	id_string += ",H:"
	# for teller in range(8,10):
	for teller in range(9,7,-1):
		tmp = int(databytes[teller], 16)
		id_string += str(From_BCD(tmp))
	# id_string.strip(".")
	return id_string
		
def From_MBUSID(databytes):
	# gaat ervan uit dat databytes een HEX string is......
	# print ("From_MBUSID received: " + databytes)
	databytes = databytes.strip().split(" ")
	# print (databytes)
	id_string = "ID:"
	# python has a strange way to indica something like (for teller=3 step -1 to 0 do)
	for teller in range(3,-1,-1):
		id_string += databytes[teller]
	id_string +=", "
	manuf = int(databytes[5] + databytes[4], 16)
	letter1 = chr((manuf & 0x001F) + 64)
	letter2 = chr(((manuf >> 5) & 0x001F) + 64)
	letter3 = chr(((manuf >> 10) & 0x001F) + 64)
	id_string += letter1 + letter2 + letter3
	id_string += ", Vs:" + databytes[6]
	id_string += ", Medium Code:" + str(int(databytes[7], 16) & 0x000F)
	id_string += ", Access/Response counter:" + str(int(databytes[8], 16))
	id_string += ", Status(Hex): " + databytes[9] + ", Sign: " + databytes[10] + databytes[11]
	return id_string









  
"""
HexByteConversion

Convert a byte string to it's hex representation for output or visa versa.
ByteToHexString converts a single byte into a hex string i.e. 10 into '0A'
ByteArrayToHexString converts an array (list) of bytes into a hex string i.e. [1,5,15,10] into '01 05 FF 0A'

ByteStringToHexString converts byte string "\xFF\xFE\x00\x01" to the string "FF FE 00 01"
HexStringToByteString converts string "FF FE 00 01" to the byte string "\xFF\xFE\x00\x01"
"""
import binascii


#-------------------------------------------------------------------------------
def ByteToHexString(Byte):
	"""
	ByteToHexString converts a single byte into a hex string i.e. 10 into '0A'
	"""
	# result = binascii.hexlify(bytearray([Byte])).upper()
	result = ''.join('{:02x}'.format(Byte)).upper()
	return result
#-------------------------------------------------------------------------------
def ByteArrayToHexString(ByteArray):
	"""
	ByteArrayToHexString converts an array (list) of bytes into a hex string i.e. [1,5,15,10] into '01 05 FF 0A'
	"""
	# result = binascii.hexlify(bytearray(ByteArray)).upper()
	result = ' '.join('{:02x}'.format(x) for x in ByteArray).upper().strip()
	return result

#-------------------------------------------------------------------------------

def ByteStringToHexString( byteStr ):
	"""
	Convert a byte string to it's hex string representation e.g. for output.
	"""
	
	# Uses list comprehension which is a fractionally faster implementation than
	# the alternative, more readable, implementation below
	#   
	#    hex = []
	#    for aChar in byteStr:
	#        hex.append( "%02X " % ord( aChar ) )
	#
	#    return ''.join( hex ).strip()        

	return ''.join( [ "%02X " % ord( x ) for x in byteStr ] ).strip()

#-------------------------------------------------------------------------------

def HexStringToByteString( hexStr ):
	"""
	Convert a string hex byte values into a byte string. The Hex Byte values may
	or may not be space separated.
	"""
	# The list comprehension implementation is fractionally slower in this case    
	#
	#    hexStr = ''.join( hexStr.split(" ") )
	#    return ''.join( ["%c" % chr( int ( hexStr[i:i+2],16 ) ) \
	#                                   for i in range(0, len( hexStr ), 2) ] )
 
	bytes = []

	hexStr = ''.join( hexStr.split(" ") )

	for i in range(0, len(hexStr), 2):
		bytes.append( chr( int (hexStr[i:i+2], 16 ) ) )

	return ''.join( bytes )

#-------------------------------------------------------------------------------

def HexStringToByteArray(hexstr):
	try:
		return bytearray.fromhex(hexstr)
	except Exception as err:
		Logger.error("Problems converting HEXSTRING: " + hexstr)
		Logger.error(str(err))

# # test data - different formats but equivalent data
# __hexStr1  = "FFFFFF5F8121070C0000FFFFFFFF5F8129010B"
# __hexStr2  = "FF FF FF 5F 81 21 07 0C 00 00 FF FF FF FF 5F 81 29 01 0B"
# __byteStr = "\xFF\xFF\xFF\x5F\x81\x21\x07\x0C\x00\x00\xFF\xFF\xFF\xFF\x5F\x81\x29\x01\x0B"


# if __name__ == "__main__":
	# print ("\nHex To Byte and Byte To Hex Conversion")

	# # print "Test 1 - ByteToHex - Passed: ", ByteToHex( __byteStr ) == __hexStr2
	# # print "Test 2 - HexToByte - Passed: ", HexToByte( __hexStr1 ) == __byteStr
	# # print "Test 3 - HexToByte - Passed: ", HexToByte( __hexStr2 ) == __byteStr


	# print ("Test 1 - "), ByteToHexString(15)
	# print ("Test 2 - "), ByteArrayToHexString([1,2,3,10,100,123,200,12])
	# print ("Test 3 - "), ByteStringToHexString( __byteStr )
	# print ("Test 4 - "), HexStringToByteString( __hexStr1 )
	

    # Public Function ToData2B(Num As Single) As UInt16
        # Try
            # If Num < -128 Or Num > 127.996 Then
                # Throw New ApplicationException("Invalid ToData2B conversion: Input = " & Num.ToString)
            # Else

                # Dim IntPart As Integer = Int(Num)
                # Dim Fraction As Single = Math.Abs(Num - IntPart)
                # Dim StepSize As Single = 1 / 256
                # Dim NmrSteps As Integer = Int(Fraction / StepSize)

                # Dim HighByte As Byte = ToData1B(Int(Num))
                # Dim LowByte As Byte = NmrSteps

                # ToData2B = ShiftLeft(HighByte, 8) + LowByte
            # End If
        # Catch ex As Exception
            # WrInfo(MyModuleName & ":  " & Reflection.MethodBase.GetCurrentMethod().Name & "> " & ex.Message, WrinfoType.InfoMessage)
            # ToData2B = 0

        # End Try
    # End Function


    # Public Function ToData2C(Num As Single) As UInt16
        # Try
            # If Num > 2047.9 Or Num < -2048 Then Throw New ApplicationException("Invalid ToData2C conversion: Input = " & Num.ToString)

            # Dim AbsNum As Single
            # If Num < 0 Then
                # AbsNum = Math.Abs(-2048 - Num)
            # Else
                # AbsNum = Num
            # End If

            # Dim IntPart As Integer = Int(AbsNum)
            # Dim Fraction As Single = AbsNum - IntPart
            # Dim StepSize As Single = 1 / 16
            # Dim LowNibble As Integer = Int(Fraction / StepSize)

            # Dim HighByte As Integer = Int(IntPart / 16)
            # Dim HighNibble As Integer = IntPart Mod 16
            # Dim LowByte As Integer = ShiftLeft(IntPart Mod 16, 4) + LowNibble

            # If Num < 0 Then
                # 'HighByte = BITWISE_OR(HighByte, &H80)
                # ToData2C = BITWISE_OR(ShiftLeft(HighByte, 8) + LowByte, &H8000)

            # Else

                # ToData2C = ShiftLeft(HighByte, 8) + ShiftLeft(HighNibble, 4) + LowNibble
            # End If
        # Catch ex As Exception
            # WrInfo(MyModuleName & ":  " & Reflection.MethodBase.GetCurrentMethod().Name & "> " & ex.Message, WrinfoType.InfoMessage)
            # ToData2C = 0
        # End Try


    # End Function

def From_ByteArray_converter(datacodec, databytes):
	# print ("data_converter called with codec " + datacodec + " and datatype " + str(datatype) + " and databytes ", databytes)
	
	dataindex=0
	arg = None
	try:
		if   datacodec.upper() in ["ASCII"]:						arg = databytes
		elif datacodec.upper() in ["BCD","DATA1B","DATA1C","INT8"]: arg = databytes[dataindex]
		elif datacodec.upper() in ["DATA2B","DATA2C","INT16REV"]:   arg = (databytes[dataindex+1] * 256) + (databytes[dataindex])
		elif datacodec.upper() in ["INT16"]:                        arg = (databytes[dataindex] * 256) + (databytes[dataindex+1])
		# elif datacodec.upper() in ["INT32REV"]:                     arg = (databytes[dataindex+3] * (256*256*256) + 
																		   # databytes[dataindex+2] * (256*256) + 
																		   # databytes[dataindex+1] * (256) + 
																		   # databytes[dataindex])
		elif datacodec.upper() in ["INT32REV"]:                     arg = int.from_bytes(databytes, byteorder='little', signed=False)
		# elif datacodec.upper() in ["FLOAT32"]:                      arg = (databytes[dataindex] * (256*256*256) + 
																		   # databytes[dataindex+1] * (256*256) + 
																		   # databytes[dataindex+2] * (256) + 
																		   # databytes[dataindex+3])
		elif datacodec.upper() in ["FLOAT32"]:                      arg = int.from_bytes(databytes, byteorder='big', signed=False)
		elif datacodec.upper() in ["FLOAT64"]:                      arg = int.from_bytes(databytes, byteorder='big', signed=False)
		elif datacodec.upper() in ["HEX8"]:                         arg = ByteArrayToHexString(databytes[dataindex:dataindex+1])
		elif datacodec.upper() in ["HEX16"]:                        arg = ByteArrayToHexString(databytes[dataindex:dataindex+2])
		elif datacodec.upper() in ["HEXSTR"]:                       arg = databytes
		elif datacodec.upper() in ["BIN8"]:                         arg = databytes[dataindex]
		elif datacodec.upper() in ["BIN16"]:                        arg = (databytes[dataindex] * 256) + (databytes[dataindex+1])
		elif datacodec.upper() in ["BINSTR"]:                       arg = databytes
		elif datacodec.upper() in ["EBUSDATETIME"]:                 arg = databytes[dataindex:dataindex+7]
		elif datacodec.upper() in ["MBUSDATETIME"]:					arg = databytes[dataindex:dataindex+4]
		elif datacodec.upper() in ["STATUS","PUMPPOWER","ONOFF"]:   arg = databytes[dataindex]
		elif datacodec.upper() in ["EBUSID"]:                       arg = ByteArrayToHexString(databytes[dataindex:dataindex+10])
		elif datacodec.upper() in ["MBUSID"]:                       arg = ByteArrayToHexString(databytes[dataindex:dataindex+12])
		elif datacodec.upper() in ["ERRORHISTORY"]:                 return None
	except Exception as err:
		# Logger.error("%s, while trying to run datacodec %s with databytes %s" % (err, datacodec, databytes))
		Logger.debug("%s, while trying to run datacodec %s with databytes %s" % (err, datacodec, databytes))
		return None
	
	try:  
		convertor = globals()['From_' + datacodec.upper()]
		# convertor = getattr(Conversion_Routines, "From_" + datacodec.upper())
	except Exception as err:
		Logger.error("No convertor found for " + datacodec.upper() + " : " + str(err))
		return None
		
	try:
		result = convertor(arg)
		# print (str(result))
		return result
	except Exception as err:
		Logger.error("Conversion problems for " + datacodec.upper() + " : " + str(arg))
		Logger.error(str(err))
		return None

def To_ByteArray_converter(datacodec, value):
	# print ("To_ByteArray_converter called with codec " + datacodec + " and value ", value)
	
	# dataindex=0
	# arg = None
	
	try:  
		convertor = globals()['To_' + datacodec.upper()]
	except Exception as err:
		Logger.error("No convertor found for " + datacodec.upper() + " : " + str(err))
		return None
		
	try:
		if   datacodec.upper() in ["ASCII"]:						result=bytearray(str(value).encode('ascii'))
		elif datacodec.upper() in ["BCD","DATA1B","DATA1C","INT8"]: result=convertor(value).to_bytes(1, byteorder="big")
		elif datacodec.upper() in ["DATA2B","DATA2C","INT16REV"]:   result=convertor(value).to_bytes(2, byteorder="little")
		elif datacodec.upper() in ["INT16"]:						result=convertor(value).to_bytes(2, byteorder="big")
		elif datacodec.upper() in ["FLOAT32"]:						result=encode_ieee(value).to_bytes(4, byteorder="big")
		# elif datacodec.upper() in ["INT16"]:                        arg = (databytes[dataindex] * 256) + (databytes[dataindex+1])
		# elif datacodec.upper() in ["INT32REV"]:                     arg = (databytes[dataindex+3] * (256*256*256) + 
																		   # databytes[dataindex+2] * (256*256) + 
																		   # databytes[dataindex+1] * (256) + 
																		   # databytes[dataindex])
		# elif datacodec.upper() in ["HEX8"]:                         arg = ByteArrayToHexString(databytes[dataindex:dataindex+1])
		# elif datacodec.upper() in ["HEX16"]:                        arg = ByteArrayToHexString(databytes[dataindex:dataindex+2])
		# elif datacodec.upper() in ["BIN8"]:                         arg = databytes[dataindex]
		# elif datacodec.upper() in ["BIN16"]:                        arg = (databytes[dataindex] * 256) + (databytes[dataindex+1])
		# elif datacodec.upper() in ["EBUSDATETIME"]:                 arg = databytes[dataindex:dataindex+7]
		# elif datacodec.upper() in ["MBUSDATETIME"]:					arg = databytes[dataindex:dataindex+4]
		# elif datacodec.upper() in ["STATUS","PUMPPOWER","ONOFF"]:   arg = databytes[dataindex]
		# elif datacodec.upper() in ["EBUSID"]:                       arg = ByteArrayToHexString(databytes[dataindex:dataindex+10])
		# elif datacodec.upper() in ["MBUSID"]:                       arg = ByteArrayToHexString(databytes[dataindex:dataindex+12])
		# elif datacodec.upper() in ["ERRORHISTORY"]:                 return
		# print("result is:", result)
		return result
	except Exception as err:
		Logger.error("Conversion problems for " + datacodec.upper() + " : " + str(err))
		return None


def main(args):
	while True:
		try:
			print ("The following dataconversion routines are available in this module:")
			print ('')
			for funct_name in globals():
				if (
					not funct_name.startswith("__") and 
					(funct_name.upper().startswith('TO_') or funct_name.upper().startswith('FROM_')) and
					'CONVERTER' not in funct_name.upper()
					):
					print(funct_name + ", ", end='')
			print ('')
			print ('')
			tofrom = input("T(o) or F(rom) bytearray?: ")
			if tofrom.upper().startswith("T"):
				data = input ("Conversion TO bytearray: Enter input value: ")
				decoder = input("Select Dataconverter  : ")
				result = To_ByteArray_converter(decoder, data)
				print("result = ", ByteArrayToHexString(result))
			elif tofrom.upper().startswith("F"):
				data = input("Conversion FROM bytearray: HEX test string: ")
				decoder = input("Select Dataconverter  : ")
				result = From_ByteArray_converter(decoder, HexStringToByteArray(data))
				print("result = ", result)
		except Exception as err:
			print (str(err))
	return 0


if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))



