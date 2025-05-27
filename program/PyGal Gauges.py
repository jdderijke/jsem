#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  PyGal Gauge Test.py
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
import pygal 
from pygal import Config
from pygal.style import Style
from JSEM_GUI_classes import JSEM_Label

default_bg_color = "red"
default_font_size = "18px"
default_label_width = 70
default_label_height = 18

class PyGal(gui.Svg):
	def set_content(self, chart):
		self.data = chart.render()
		self.add_child("chart", self.data)

class PyGal_BalancedGauge(Container):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = None
		self.max_value = kwargs.get("max_value", 100)

		self.bgcolor = kwargs.get("bgcolor", "white")
		self.css_position = "absolute"

		self.css_left = kwargs.get("left", "0%")
		self.css_top = kwargs.get("top", "0%")
		self.css_width = kwargs.get("width", "400px")
		self.css_height = kwargs.get("height", "400px")
		self.css_background_color = self.bgcolor
		
		
		SubCont1 = Container()
		SubCont1.css_position = "absolute"
		SubCont1.css_left = "0px"
		SubCont1.css_top = "0px"
		SubCont1.css_width = "50%"
		SubCont1.css_height = "100%"
		SubCont1.css_background_color = self.bgcolor
		SubCont1.css_overflow = "hidden"
		self.Gauge1 = PyGal_SolidGauge	(
										show_y_labels = False,
										show_x_labels = False,
										inner_radius = kwargs.get("inner_radius", 0),
										top="0px", left="0px", width="200%", height="100%", 
										max_value = kwargs.get("max_value", 100),
										parent_width = kwargs.get("width", "400px"),
										parent_height = kwargs.get("height", "400px"),
										gauge_style = dict(colors=["green"])
										)
		self.Gauge1.style["transform"] = "scale(-1,1)"
		SubCont1.append(self.Gauge1)
		
		SubCont2 = Container()
		SubCont2.css_position = "absolute"
		SubCont2.css_left = "50%"
		SubCont2.css_top = "0%"
		SubCont2.css_width = "50%"
		SubCont2.css_height = "100%"
		SubCont2.css_background_color = self.bgcolor
		SubCont2.css_overflow = "hidden"
		self.Gauge2 = PyGal_SolidGauge	(
										show_y_labels = False,
										show_x_labels = False,
										inner_radius=kwargs.get("inner_radius", 0),
										top="0px", left="0px", width="200%", height="100%", 
										max_value = self.max_value,
										parent_width = kwargs.get("width", "400px"),
										parent_height = kwargs.get("height", "400px"),
										gauge_style = dict(colors=["red"])
										)
		self.Gauge2.style["transform"] = "translate(-50%,0px)"
		SubCont2.append(self.Gauge2)
		
		self.append(SubCont1)
		self.append(SubCont2)
		

	def update(self, value=0, *args, **kwargs):
		if value == 0:
			self.Gauge1.update(0)
			self.Gauge0.update(0)
		elif value > 0:
			self.Gauge1.update(0)
			self.Gauge2.update(value)
		elif value < 0:
			self.Gauge2.update(0)
			self.Gauge1.update(abs(value))
		


class PyGal_SolidGauge(gui.Svg):
	def __init__(self, *args, **kwargs):
		try:
			print ("PyGal_SolidGauge init called")
			super().__init__(*args, **kwargs)
			self.css_position = "absolute"
			
			# Check optional parameters in kwargs
			self.attributes["title"]=kwargs.get("tooltip","")
			self.css_font_size = kwargs.get("fontsize", "20px")
			kwargs.pop("fontsize",None)
			
	
			# get font, top, left, width and height and background color, these entries are then removed from kwargs
			# as they are ONLY meant for the SVG container, not for the pygal element
			self.css_top= kwargs.get("top", "0px")
			kwargs.pop("top",None)
			self.css_left= kwargs.get("left", "0px")
			kwargs.pop("left",None)
			self.css_width = kwargs.get("width", "100%")
			kwargs.pop("width",None)
			self.css_height = kwargs.get("height", "100%")
			kwargs.pop("height",None)
			self.css_background_color=kwargs.get("bgcolor", "transparent")
			kwargs.pop("bgcolor",None)
			
			# certain kwargs (elements for the config object in pygal) need a default value
			kwargs["legend_at_bottom"] = kwargs.get("legend_at_bottom",True)
			kwargs["show_legend"] = kwargs.get("show_legend",False)
			kwargs["human_readable"] = kwargs.get("human_readable",True)

			# certain elements need to be translated for pygal, pygal only accepts px size, not %
			if "parent_width" in kwargs and kwargs["parent_width"].endswith("px"):
				kwargs["width"] = int(kwargs["parent_width"].rstrip("px"))
				kwargs["explicit_size"] = True
				kwargs.pop("parent_width")
			if "parent_height" in kwargs and kwargs["parent_height"].endswith("px"):
				kwargs["height"] = int(kwargs["parent_height"].rstrip("px"))
				kwargs["explicit_size"] = True
				kwargs.pop("parent_height")
				

			gauge_style = kwargs.get("gauge_style", {})
			gauge_style["background"]=gauge_style.get("background","transparent")
			gauge_style["plot_background"]=gauge_style.get("plot_background","transparent")
			gauge_style["colors"]=gauge_style.get("colors",["red", "blue", "green", "black"])
			gauge_style["value_colors"]=gauge_style.get("value_colors",["red", "blue", "green", "black"])
			gauge_style["legend_font_size"]=gauge_style.get("legend_font_size",20)
			gauge_style["label_font_size"]=gauge_style.get("label_font_size",20)
			gauge_style["title_font_size"]=gauge_style.get("title_font_size",30)
			# self.custom_style = pygal.style.styles['default'](**gauge_style)
			self.custom_style = Style(**gauge_style)
			print(self.custom_style.background, self.custom_style.plot_background)

			kwargs.pop("gauge_style",None)
			self.custom_config = kwargs
			# force an update en breng de chart alive....
			
			self.update()
			
			


		except Exception as err:
			raise Exception(str(err))

	def set_content(self, chart):
		self.data = chart.render()
		self.add_child("chart", self.data)
		

	def update(self, value=0):
		
		print ("Pygal update called with value: " + str(value))
		print (self.custom_config)
			
		self.gauge_chart = pygal.SolidGauge(
											**self.custom_config,
											style = self.custom_style
											)
		self.gauge_chart.add('Power', value)
		self.set_content(self.gauge_chart)



class PyGal_Gauge(gui.Svg):
	def __init__(self, *args, **kwargs):
		try:
			print ("Pygal init called")
			super().__init__(*args, **kwargs)
			self.css_position = "absolute"
			self.title = kwargs["title"] if "title" in kwargs else ""
			# Check optional parameters in kwargs
			if "tooltip" in kwargs: self.attributes["title"]=kwargs["tooltip"]
			
			self.bgcolor = kwargs["bgcolor"] if "bgcolor" in kwargs else "transparent"
				
			# get font, top, left, width and height
			if "fontsize" in kwargs:
				try:
					# default to px
					self.css_font_size = str(int(kwargs["fontsize"])) + "px"
				except:
					# px or %
					self.css_font_size = str(kwargs["fontsize"])
					
			if "top" in kwargs:
				try:
					# default to px
					self.css_top = str(int(kwargs["top"])) + "px"
				except:
					# px or %
					self.css_top = str(kwargs["top"])
			
			if "left" in kwargs:
				try:
					# default to px
					self.css_left = str(int(kwargs["left"])) + "px"
				except:
					# px or %
					self.css_left = str(kwargs["left"])
	
			self.width = kwargs["width"] if "width" in kwargs else "100%"
			self.height = kwargs["height"] if "height" in kwargs else "95%"
			self.css_width = str(self.width)
			self.css_height = str(self.height)
			self.css_position = "static"

			# definieer nu de config class voor de algemene chart setup en de Style voor de weergave
			self.chart_title = kwargs["title"] if "title" in kwargs else ""
			self.custom_config = Config(
										title = self.chart_title,
										x_label_rotation=90,
										x_value_formatter=lambda dt: dt.strftime("%d-%m %H:%M"),
										legend_at_bottom=True,
										human_readable=True,
										range = (-20.0, 20.0)
										)
			# eventueel nog aan custom_config toevoegen: (explicit_size=True)
			self.custom_style = Style(
									background=self.bgcolor,
									plot_background=self.bgcolor,
									legend_font_size=20,
									label_font_size=20,
									major_label_font_size=20, 
									title_font_size=30,
									)
			
			self.colors = kwargs["colors"] if "colors" in kwargs else ["red", "blue", "green", "black"]
			self.custom_style.colors = self.colors
			# force a update en breng de chart alive....
			self.update()
		except Exception as err:
			raise Exception(str(err))

	def set_content(self, chart):
		self.data = chart.render()
		self.add_child("chart", self.data)

	def update(self, *args, **kwargs):

		print ("Pygal update called")
		self.gauge_chart = pygal.Gauge(self.custom_config, style=self.custom_style)
		self.gauge_chart.title = self.title
		# self.gauge_chart.range = [-20.0, 20.0]
		self.gauge_chart.add('Power', -10.5)
		
		
		# self.gauge_chart.add('Firefox', 8099)
		# self.gauge_chart.add('Opera', 2933)
		# self.gauge_chart.add('IE', 41)
		
		# for charted_dp in self.datapoints:
		# self.datavalues = []
		# result = get_values_from_database(charted_dp, maxrows=Max_Chart_Points, data_selection=self.dataselection, start=startdate)
		# self.datavalues.append(result)
		# x_labels = [datetime.fromtimestamp(x) for x in result["timestamp"]]
		# self.line_chart.add(charted_dp.name + " (" + str(charted_dp.unit) + ")", 
							# list(zip(x_labels, result["value"])), 
							# stroke_style={'width': 20}, 
							# show_dots=False, 
							# secondary = True if charted_dp.unit != self.datapoints[0].unit else False)  
							   
		self.set_content(self.gauge_chart)





class test(App):
	def __init__(self, *args, **kwargs):
		#DON'T MAKE CHANGES HERE, THIS METHOD GETS OVERWRITTEN WHEN SAVING IN THE EDITOR
		if not 'editing_mode' in kwargs.keys():
			super(test, self).__init__(*args, static_file_path={'my_res':'./res/'})

	def idle(self):
		#idle function called every update cycle
		pass
	
	def main(self):
		return E_mainscreen()

def E_mainscreen():
	
	TopCont = Container()
	TopCont.css_left = "2%"
	TopCont.css_top = "2%"
	TopCont.css_width = "95%"
	TopCont.css_height = "95%"
	TopCont.css_background_color = "lightgrey"
	TopCont.css_position = "absolute"
	test = PyGal_BalancedGauge	(
								half_pie=False,
								inner_radius=0.7,
								top="0%", left="0%", width="400px", height="400px", 
								max_value=20,
								fontsize="20px",
								gauge_style=dict	(
											colors=["green,red"],
											label_font_size=40,
											value_font_size=40
											)
								)
	test.update(+15)
	TopCont.append(test)
	
	test2 = PyGal_SolidGauge	(
								half_pie=True,
								inner_radius=0.7,
								max_value=40,
								top="50%", left="50%", width="300px", height="300px", 
								fontsize="20px",
								gauge_style=dict	(
											colors=["blue"],
											value_colors=["green"],
											label_font_size=40,
											value_font_size=40
											)
								)

	test2.update(15)
	TopCont.append(test2)

								
	print ("Mainscreen build...")
	return TopCont

#Configuration
configuration = {'config_multiple_instance': False, 'config_address': '192.168.178.108', 'config_start_browser': False, 'config_enable_file_cache': True, 'config_project_name': 'test', 'config_resourcepath': './res/', 'config_port': 8081}

if __name__ == "__main__":
	# Logger.info ("Starting Remi web interface")
	# start(MyApp,address='127.0.0.1', port=8081, multiple_instance=False,enable_file_cache=True, update_interval=0.1, start_browser=True)
	print("Starting Remi")
	start(test, address=configuration['config_address'], port=configuration['config_port'], 
						multiple_instance=configuration['config_multiple_instance'], 
						enable_file_cache=configuration['config_enable_file_cache'],
						start_browser=configuration['config_start_browser'])
