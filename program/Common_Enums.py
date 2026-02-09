#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Common_Enums.py
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

from enum import Enum


# define some constants for the Event class
class Environment(Enum):
	Productie = 1
	Development = 2
	Testing = 3


# define some constants for the Event class
class Categories(Enum):
	ESMR50 = 1
	Solar = 2
	HP = 3
	Pool = 4
	System = 5


# define the source enums
class DataSource(Enum):
	SENSOR = 1
	METER = 2
	CALCULATED = 3


class Interface(Enum):
	P1port = 1
	Delta = 2
	M_bus = 3
	E_bus = 4


class Dictionary(Enum):
	of_lists = 1
	of_values = 2
	autoselect = 3


class MatchTimestamp(Enum):
	firstnext = 1
	lastprevious = 2
	exact_match = 3


class DataSelection(Enum):
	All = 1
	_Last50 = -1
	_10min = 600
	_30min = 1800
	_1hr = 3600
	_2hr = 7200
	_6hr = 21600
	_12hr = 43200
	_24hr = 86400
	_48hr = 172800
	_72hr = 259200
	_96hr = 345600
	# Hour = 2
	Day = 3
	Week = 4
	Month = 5
	Year = 6


class DatabaseGrouping(Enum):
	All = 1
	_1min = 60
	_10min = 600
	_15min = 900
	_30min = 1800
	Hour = 3600
	Day = 5
	Week = 6
	Month = 7
	Year = 8


class Aggregation(Enum):
	Not = 0
	Sum = 1
	Mean = 2
	Min = 3
	Max = 4
	Std = 5
	Count = 6
	Diff = 7
	Median = 8
	Last = 9
	First = 10
# Ohlc = 11


class Wakeup_Mode(Enum):
	in1hour = 3600
	in2hour = 7200
	in6hour = 21600
	in12hour = 43200
	in24hour = 86400
	in48hour = 172800
	hour = -1
	day = -2
	week = -3
	month = -4
	year = -5


class ConnState(Enum):
	Connecting = 1
	Connected = 2
	DisConnecting = 3
	DisConnected = 4


class Sndstate(Enum):
	Sender_Stopped = 1
	Waiting_For_MsgToSend = 2
	Sending_Msg = 3
	Error = 99


class Recstate(Enum):
	Receiver_Stopped = 1
	Waiting_For_MsgToReceive = 2
	Waiting_For_AckByte = 3
	Waiting_For_Crc = 4
	Waiting_For_NoOfDataBytes = 5
	Waiting_For_NoTotalBytes = 6
	Waiting_For_AnotherSTXByte = 7
	Waiting_For_SYNC_ETX = 8
	Receiving_Msg = 9
	Deconstructing_Msg = 10
	Error = 99


class MsgType(Enum):
	PollMessage = 1
	CommandMessage = 2


class PollState(Enum):
	Polling = 1
	Not_Polling = 2
	Error = 99


class SearchkeyFormat(Enum):
	ASCII = 1
	HEXstring = 2


def main(args):
	return 0


if __name__ == '__main__':
	import sys
	
	sys.exit(main(sys.argv))
