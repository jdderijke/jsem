#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Testprog Pygal BarChart.py
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
import time
from datetime import datetime
# from Common_Enums import *
# from Common_Routines import dump, Waitkey, Is_NOE
# import Common_Data
# from Config import Default_ChartMode, Max_Chart_Points

 
import remi.gui as gui
from remi.gui import *
from remi import start, App
import pygal 
from pygal import Config
from pygal.style import Style
# from DB_Routines import get_values_from_database

class Test_Bar_Chart(gui.Svg):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		dataseries = [85.8, 84.6, 84.7, 74.5,   66, 58.6, 54.7, 44.8, 36.2, 26.6, 20.1]
		self.bar_chart = pygal.Bar(print_values=True, print_values_position='bottom', print_labels=True)
		self.bar_chart.x_labels = map(str, range(2002, 2013))
		self.bar_chart.add({'title':'test', 'tooltip':'dit is de tooltip van de legend', 'xlink':{'href': 'http://en.wikipedia.org/wiki/First'}}, 
							[{'value':x, 'label':'test', 'tooltip':'mamaloe ' + str(x)} for x in dataseries])
		self.data = self.bar_chart.render()
		self.add_child("chart", self.data)

class test(App):
	def __init__(self, *args, **kwargs):
		#DON'T MAKE CHANGES HERE, THIS METHOD GETS OVERWRITTEN WHEN SAVING IN THE EDITOR
		if not 'editing_mode' in kwargs.keys():
			super(test, self).__init__(*args, static_file_path={'my_res':'./res/'})

	def idle(self):
		#idle function called every update cycle
		pass
	
	def main(self):
		return mainscreen()

def mainscreen():
	TopCont = VBox()
	TopCont.css_left = "2%"
	TopCont.css_top = "2%"
	TopCont.css_width = "95%"
	TopCont.css_height = "95%"
	
	TopCont.css_align_items = "center"
	TopCont.css_display = "flex"
	TopCont.css_flex_direction = "column"
	TopCont.css_justify_content = "space-around"
	TopCont.css_position = "absolute"
	
	TopCont.append(Test_Bar_Chart())
	return TopCont
	

if __name__ == '__main__':
	# start(MyApp,address='127.0.0.1', port=8081, multiple_instance=False,enable_file_cache=True, update_interval=0.1, start_browser=True)
	start(test, address='127.0.0.1', port=8081, 
						multiple_instance=False, 
						enable_file_cache=True,
						start_browser=True)
	
