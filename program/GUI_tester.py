#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  GUI_tester.py
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
import remi.gui as gui
from remi.gui import *
from remi import start, App

from JSEM_GUI_classes import *
from LogRoutines import Logger


class test(App):
	def __init__(self, *args, **kwargs):
		#DON'T MAKE CHANGES HERE, THIS METHOD GETS OVERWRITTEN WHEN SAVING IN THE EDITOR
		if not 'editing_mode' in kwargs.keys():
			super(test, self).__init__(*args, static_file_path={'my_res':'./res/'})

	def idle(self):
		#idle function called every update cycle
		pass
	
	def main(self):
		
		container0 = Container()
		container0.attr_class = "Container"
		container0.attr_editor_newclass = False
		container0.css_height = "250px"
		container0.css_left = "20px"
		container0.css_position = "absolute"
		container0.css_top = "20px"
		container0.css_width = "250px"
		container0.variable_name = "container0"
		label0 = Label()
		label0.attr_class = "Label"
		label0.attr_editor_newclass = False
		label0.css_height = "30px"
		label0.css_left = "20px"
		label0.css_position = "absolute"
		label0.css_top = "20px"
		label0.css_width = "100px"
		label0.text = "label"
		label0.variable_name = "label0"
		container0.append(label0,'label0')
		
		label1 = JSEM_Label(container0,20, 60, 100, 30, background="yellow", text="JSEM label")
		
		
		return container0

#Configuration
configuration = {'config_multiple_instance': False, 'config_address': '192.168.178.220', 'config_start_browser': False, 'config_enable_file_cache': True, 'config_project_name': 'test', 'config_resourcepath': './res/', 'config_port': 8081}

if __name__ == "__main__":
	# start(MyApp,address='127.0.0.1', port=8081, multiple_instance=False,enable_file_cache=True, update_interval=0.1, start_browser=True)
	start(test, address=configuration['config_address'], port=configuration['config_port'], 
						multiple_instance=configuration['config_multiple_instance'], 
						enable_file_cache=configuration['config_enable_file_cache'],
						start_browser=configuration['config_start_browser'])



