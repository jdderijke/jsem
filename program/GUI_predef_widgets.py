#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  GUI_predef_widgets.py
#  
#  Copyright 2024  <pi@raspberrypi>
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
from typing import Union

from LogRoutines import Logger
import remi.gui as gui
from remi.gui import *
from datetime import datetime
from Common_Enums import *

import Common_Data
from Common_Data import DATAPOINTS_NAME, DATAPOINTS_ID
from Datapoint_IDs import *
from JSEM_GUI_classes import JSEM_Label, JSEM_Stacked_Bar, JSEM_BalancedGauge, JSEM_Map_Chart, JSEM_ChartCont
from JSEM_GUI_classes import JSEM_Bar_Chart, JSEM_Line_Chart, JSEM_Rect, JSEM_Arrow, JSEM_Buffer, JSEM_MultiArrow, JSEM_WeatherIcon
from remi_addons import Switch, PushBtn

from DataPoint import Datapoint

DataCont = Common_Data.DATA_PARENT_CONTAINER

class Heat_widget(Container):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		# apply default style elements, these can be overruled by kwargs
		self.style.update({'background-color':'transparent', 'position':'absolute'})
		
		# # Om top, left height en width gewoon als getal op te kunnen geven worden deze kwargs binnengehaald, geconverteerd en in kwargs teruggezet
		for attr_name in ['height', 'width', 'top', 'left']:
			if attr_name in kwargs:
				attr = kwargs[attr_name]
				if type(kwargs[attr_name]) == str:	pass
				else:								kwargs[attr_name] = "%spx" % kwargs[attr_name]
		
		# alle kwargs worden nagelopen en ze vervangen de args in de default config en style dictionaries
		for arg in list(kwargs.keys()):
			try:
				self.style[arg.replace("_", "-")] = kwargs[arg]
			except Exception as err:
				Logger.error(f'Problem handling kwarg {arg} with value {kwargs[arg]}: {err}')
		self.build()
		return
		
	def build(self, **kwargs):
		dp = DATAPOINTS_ID
		try:
			arrow_style = {'line-stroke':'green', 'line-stroke-width':'50%', 'arrow-ratio':'35'}
			
			rect_style = {'background-color':'grey', 'border-radius':"5px", 'text-color':"white", 'text-font-size':"2cqh"}
			
			buff_style = 	{	
						'fill-background-color':"green", 'text-position':'absolute', 'text-top': '40%', 'text-left':'30%', 'text-font-size':"3cqh", 
						'text-color':'grey', 'text-rotate':'90deg',
						'border-style':"solid", 'border-width':"2px", 'border-color':"grey", 'border-radius':"5px", 
						'value-color':'purple', 'value-font-size':"2cqh", 
						'minlbl-font-size':"1cqh", 'minlbl-color':"black", 'maxlbl-font-size':"1cqh", 'maxlbl-color':"black"
							}
			buff_config = dict(show_minmax=True, unit='%')
			buff_cond_format =	[
								dict(cond="gte", check_value=0.95 * dp[Max_Energy_Buf].value, true="red", false="green", qit=True),
								dict(cond="gte", check_value=0.9 * dp[Max_Energy_Buf].value, true="orange", false="green", qit=True),
								dict(cond="ste", check_value=5.0, true="red", false="green", qit=True),
								dict(cond="ste", check_value=10.0, true="orange", false="green", qit=True)
								]
								
			lbl_config = dict(show_name=False, show_subcat=False, show_value=True, show_unit=False, enable_RW=False)
			lbl_style = {'value-font-size':'2.0cqh', 'value-width':'100%', 'width':'10%', 'height':'6%', 'background-color':'transparent'}
	
			# Houtkachel
			htkln = JSEM_Arrow(self, dp[Act_Power_02], top='72%', left='27%', width='10%', height='10%', style=arrow_style, line_stroke='red',
								cond_format = dict(cond=">", check_value=0.0, prop='line-stroke', true="red", false="grey"))
			houtk = JSEM_Rect(self, dp[Act_Power_02], top='70%', left='0%', width='25%', height='15%', text="Houtkachel", style=rect_style,
								cond_format = dict(cond=">", check_value=0.0, true="red", false="grey"))
			JSEM_Label(self,dp[Act_Power_02], top='81%', left='28%', config=lbl_config, style=lbl_style,
								cond_format = dict(cond=">", check_value=0.0, prop='value-color', true="black", false="grey"))
										
										
			# Buffervat
			buff = JSEM_Buffer(self, dp[Act_Energy_Buf], top='50%', left='37%', width='25%', height='50%', text='Buffervat', 
								config=buff_config, style=buff_style, min_value=0.0, max_value=dp[Max_Energy_Buf].value,
								cond_format=buff_cond_format)
			
			# Woning met vloerverwarming
			woning = JSEM_Rect(self, top='0%', left='0%', width='100%', height='16%', text="Woning", style=rect_style) 
			vloer = JSEM_Buffer(self, top='16%', left='0%', width='100%', height='16%', value=50, text='Vloer', text_rotate='0deg',
								config=buff_config, style=buff_style)
			vloerin = JSEM_Arrow(self, dp[Act_Power_01], top='32%', left='45%', width='10%', height='17%', orientation='vertical', arrow='begin', style=arrow_style, line_stroke='red',
								cond_format = dict(cond=">", check_value=0.0, prop='line-stroke', true="red", false="grey"))
			JSEM_Label(self, dp[Act_Power_01], top='40%', left='56%', config=lbl_config, style=lbl_style, value_color='black', 
								cond_format = dict(cond=">", check_value=0.0, prop='value-color', true="black", false="grey"))


	
	
			# Heatpump als verwarmer of als cooling
			wpheatln = JSEM_Arrow(self, dp[hp_power], top='72%', left='62%', width='12%', height='10%', arrow='begin', style=arrow_style, line_stroke='red',
								cond_format = dict(cond=">", check_value=0.0, prop='line-stroke', true="red", false="grey"))
								# cond_format = dict(cond=">", check_value=0.0, prop='visibility', true="visible", false="visible"))
								
			JSEM_Label(self,dp[hp_power], top='81%', left='67%', config=lbl_config, style=lbl_style, value_color='black',
								cond_format = dict(cond=">", check_value=0.0, prop='visibility', true="visible", false="hidden"))
			
			
			wpcoolln = JSEM_Arrow(self, dp[Act_Power_01], top='35%', left='82%', width='10%', height='35%', orientation='vertical', style=arrow_style, line_stroke='blue', 
								cond_format = dict(cond="<", check_value=0.0, prop='line-stroke', true="blue", false="grey"))
								# cond_format = dict(cond="<", check_value=0.0, prop='visibility', true="visible", false="visible"))
								
			JSEM_Label(self,dp[Act_Power_01], top='40%', left='93%', config=lbl_config, style=lbl_style, value_color='blue',
								cond_format = dict(cond="<", check_value=0.0, prop='visibility', true="visible", false="hidden"))
			wpomp = JSEM_Rect(self, dp[hp_power], top='70%', left='75%', width='25%', height='15%', text="Warmtepomp",  style=rect_style,
								cond_format = 	[
												dict(cond=">", check_value=0.0, true="red", false="grey", qit=True),
												dict(cond="<", check_value=0.0, true="blue", false="grey")
												])
		except Exception as err:
			Logger.error(err)
			


class E_widget(Container):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		# apply default style elements, these can be overruled by kwargs
		self.style.update({'background-color':'transparent', 'position':'absolute'})
		
		# # Om top, left height en width gewoon als getal op te kunnen geven worden deze kwargs binnengehaald, geconverteerd en in kwargs teruggezet
		for attr_name in ['height', 'width', 'top', 'left']:
			if attr_name in kwargs:
				attr = kwargs[attr_name]
				if type(kwargs[attr_name]) == str:	pass
				else:								kwargs[attr_name] = "%spx" % kwargs[attr_name]
		
		# alle kwargs worden nagelopen en ze vervangen de args in de default config en style dictionaries
		for arg in list(kwargs.keys()):
			try:
				self.style[arg.replace("_", "-")] = kwargs[arg]
			except Exception as err:
				Logger.error(f'Problem handling kwarg {arg} with value {kwargs[arg]}: {err}')
		self.build()
		return
		
	def build (self, **kwargs):
		dp = DATAPOINTS_ID
		try:
			
			e_arrow_style = {'line-stroke':'red', 'line-stroke-width':'60%', 'arrow-ratio':'35'}
			e_rect_style = {'background-color':'red', 'border-radius':"5px", 'text-color':"white", 'text-font-size':"1.0em"}
			
			lbl_style = {
						'value-font-size':'0.8em', 'value-width':'70%', 
						'unit-font-size':'0.5em', 'unit-width':'30%', 
						'width':'12%', 'height':'6%', 'font-size':'100%'
						}
			
			lbl_config = dict(show_name=False, show_subcat=False, show_value=True, show_unit=True, enable_RW=False)
			
			solar_bx = JSEM_Rect(self, dp[solar_AC_Power], top="0%", left="0%", width='20%', height='30%', text="Solar", style=e_rect_style, background_color='green',
									cond_format = [dict(cond="gt", check_value=0.0, true="green", false="darkgrey")])
	
			grid_bx = JSEM_Rect(self, dp[grid_netto], top='0%', left='80%', width='20%', height='30%', text="Grid", style=e_rect_style,
								cond_format = 	[
											dict(cond="gt", check_value=0.0, true="red", qit=True),
											dict(cond="eq", check_value=0.0, true="darkgrey", qit=True),
											dict(cond="st", check_value=0.0, true="green", qit=True),
												])

			arr0 = JSEM_MultiArrow(self, dp[solar_AC_Power], left='22%', top='9%', width='23%',height='50%', line_fill='green', 
										arrow1= dict(ap=15, sl=130, al=0, sw=20, aw=0),
										arrow2= dict(ap=130, sl=50, al=20, sw=0, aw=0),
										line_stroke_width='0',
										cond_format = [dict(cond="gt", check_value=0.0, prop="line-fill", true="green", false="darkgrey")])
										
			arr1 = JSEM_MultiArrow(self, dp[grid_netto], left='44%', top='9%', width='35%',height='50%', line_fill='red', 
										arrow1= dict(ap=15, sl=100, al=0, sw=20, aw=0),
										arrow2= dict(ap=100, sl=50, al=20, sw=20, aw=30),
										flip='horizontal',
										line_stroke_width='0',
										cond_format = [dict(cond="gte", check_value=0.0, prop="visibility", true="visible", false="hidden")])
	
			arr2 = JSEM_MultiArrow(self, dp[grid_netto], left='22%', top='9%', width='57%',height='50%', line_fill='green', 
										arrow1= dict(ap=15, sl=100, al=30, sw=20, aw=30),
										arrow2= dict(ap=65, sl=50, al=20, sw=20, aw=30),
										line_stroke_width='0',
										cond_format = [dict(cond="st", check_value=0.0, prop="visibility", true="visible", false="hidden")])
			JSEM_Label(self, dp[solar_AC_Power], top='12%', left='25%', config=lbl_config, style=lbl_style)
			JSEM_Label(self,dp[grid_netto],top='12%', left='55%',config=lbl_config, style=lbl_style)
			JSEM_Label(self,dp[woning_netto], top='35%', left='55%', config=lbl_config, style=lbl_style)
			
			hp_bx = JSEM_Rect(self, dp[hp_ACpower], top='80%', left='0%', width='20%', height='20%', text="WarmtePmp", style=e_rect_style,
								cond_format = [dict(cond="gt", check_value=0.0, true="red", false="darkgrey")])
			hp_arr = JSEM_MultiArrow(self, dp[hp_ACpower], left='5%', top='60%', width='45%',height='20%', line_fill='red', line_stroke_width='0',
										arrow1= dict(ap=10, sl=100, al=0, sw=20, aw=0),
										arrow2= dict(ap=100, sl=60, al=20, sw=9, aw=13),
										flip='horizontal',
										cond_format = [dict(cond="gt", check_value=0.0, prop="line-fill", true="red", false="darkgrey")])
			JSEM_Label(self,dp[hp_ACpower],top='81%', left='5%', config=lbl_config, style=lbl_style)
			
			
			ev_bx = JSEM_Rect(self, dp[ev_ACpower], top='80%', left='25%', width='20%', height='20%', text="Laadpaal", style=e_rect_style,
								cond_format = [dict(cond="gt", check_value=0.0, true="red", false="darkgrey")])
			ev_arr = JSEM_MultiArrow(self, dp[ev_ACpower], left='30%', top='60%', width='20%',height='20%', line_fill='red', line_stroke_width='0',
										arrow1= dict(ap=20, sl=100, al=0, sw=20, aw=0),
										arrow2= dict(ap=100, sl=50, al=20, sw=20, aw=30),
										flip='horizontal',
										cond_format = [dict(cond="gt", check_value=0.0, prop="line-fill", true="red", false="darkgrey")])
			JSEM_Label(self,dp[ev_ACpower], top='81%', left='30%', config=lbl_config, style=lbl_style)
	
		
			woning_bx = JSEM_Rect(self, dp[rest_ACpower], top='80%', left='80%', width='20%', height='20%', text="Woning", style=e_rect_style, 
								cond_format = [dict(cond="gt", check_value=0.0, true="red", false="darkgrey")])
			woning_arr = JSEM_MultiArrow(self, dp[rest_ACpower], left='50%', top='60%', width='45%',height='20%', line_fill='red', line_stroke_width='0',
										arrow1= dict(ap=10, sl=100, al=0, sw=20, aw=0),
										arrow2= dict(ap=100, sl=60, al=20, sw=9, aw=13),
										cond_format = [dict(cond="gt", check_value=0.0, prop="line-fill", true="red", false="darkgrey")])
			JSEM_Label(self,dp[rest_ACpower], top='81%', left='85%', config=lbl_config, style=lbl_style)


			pool_bx = JSEM_Rect(self, dp[pool_ACpower], top='80%', left='55%', width='20%', height='20%', text="Zwembad", style=e_rect_style,
								cond_format = [dict(cond="gt", check_value=0.0, true="red", false="darkgrey")])
			pool_arr = JSEM_MultiArrow(self, dp[pool_ACpower], left='50%', top='60%', width='20%',height='20%', line_fill='red', line_stroke_width='0',
										arrow1= dict(ap=20, sl=100, al=0, sw=20, aw=0),
										arrow2= dict(ap=100, sl=50, al=20, sw=20, aw=30),
										cond_format = [dict(cond="gt", check_value=0.0, prop="line-fill", true="red", false="darkgrey")])
			JSEM_Label(self,dp[pool_ACpower], top='81%', left='60%', config=lbl_config, style=lbl_style)
			
		except Exception as err:
			Logger.exception(str(err))
	

class E_simple_widget(Container):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		# apply default style elements, these can be overruled by kwargs
		self.style.update({'background-color':'transparent', 'position':'absolute'})
		
		# # Om top, left height en width gewoon als getal op te kunnen geven worden deze kwargs binnengehaald, geconverteerd en in kwargs teruggezet
		for attr_name in ['height', 'width', 'top', 'left']:
			if attr_name in kwargs:
				attr = kwargs[attr_name]
				if type(kwargs[attr_name]) == str:	pass
				else:								kwargs[attr_name] = "%spx" % kwargs[attr_name]
		
		# alle kwargs worden nagelopen en ze vervangen de args in de default config en style dictionaries
		for arg in list(kwargs.keys()):
			try:
				self.style[arg.replace("_", "-")] = kwargs[arg]
			except Exception as err:
				Logger.error(f'Problem handling kwarg {arg} with value {kwargs[arg]}: {err}')
		self.build()
		return
		
	def build (self, **kwargs):
		dp = DATAPOINTS_ID
		try:
			
			e_arrow_style = {'line-stroke':'red', 'line-stroke-width':'60%', 'arrow-ratio':'35'}
			e_rect_style = {
						'background-color':'red', 'border-radius':"5px", 
						'text-color':"white", 'text-font-size':"1em",
						'font-size':'100%'
						}
			
			lbl_style = {
						'value-font-size':'0.8em', 'value-width':'70%', 
						'unit-font-size':'0.5em', 'unit-width':'30%', 
						'width':'17%', 'height':'6%', 'font-size':'100%'
						}
			
			lbl_config = dict(show_name=False, show_subcat=False, show_value=True, show_unit=True, enable_RW=False)
			
									
			solar_bx = JSEM_Rect(self, dp[solar_AC_Power], top="0%", left="0%", width='20%', height='30%', text="Solar", style=e_rect_style, background_color='green',
									cond_format = [dict(cond="gt", check_value=0.0, true="green", false="darkgrey")])
	
			grid_bx = JSEM_Rect(self, dp[grid_netto], top='0%', left='80%', width='20%', height='30%', text="Grid", style=e_rect_style,
								cond_format = 	[
											dict(cond="gt", check_value=0.0, true="red", qit=True),
											dict(cond="eq", check_value=0.0, true="darkgrey", qit=True),
											dict(cond="st", check_value=0.0, true="green", qit=True)])

			woning_bx = JSEM_Rect(self, dp[rest_ACpower], top='60%', left='30%', width='40%', height='30%', text="Woning", style=e_rect_style, 
								cond_format = [dict(cond="gt", check_value=0.0, true="red", false="darkgrey")])
	


			arr0 = JSEM_MultiArrow(self, dp[solar_AC_Power], left='22%', top='9%', width='23%',height='50%', line_fill='green', 
										arrow1= dict(ap=15, sl=130, al=0, sw=20, aw=0),
										arrow2= dict(ap=130, sl=50, al=20, sw=0, aw=0),
										line_stroke_width='0',
										cond_format = [dict(cond="gt", check_value=0.0, prop="line-fill", true="green", false="darkgrey")])
			
			arr1 = JSEM_MultiArrow(self, dp[grid_netto], left='44%', top='9%', width='35%',height='50%', line_fill='red', 
										arrow1= dict(ap=15, sl=100, al=0, sw=20, aw=0),
										arrow2= dict(ap=100, sl=50, al=20, sw=20, aw=30),
										flip='horizontal',
										line_stroke_width='0',
										cond_format = [dict(cond="gte", check_value=0.0, prop="visibility", true="visible", false="hidden")])
			
			arr2 = JSEM_MultiArrow(self, dp[grid_netto], left='22%', top='9%', width='57%',height='50%', line_fill='green', 
										arrow1= dict(ap=15, sl=105, al=25, sw=20, aw=30),
										arrow2= dict(ap=65, sl=50, al=20, sw=20, aw=30),
										line_stroke_width='0',
										cond_format = [dict(cond="st", check_value=0.0, prop="visibility", true="visible", false="hidden")])
			
			
			JSEM_Label(self, dp[solar_AC_Power], top='13%', left='25%', config=lbl_config, style=lbl_style)
			JSEM_Label(self,dp[grid_netto],top='13%', left='55%',config=lbl_config, style=lbl_style)
			JSEM_Label(self,dp[woning_netto], top='61%', left='35%', config=lbl_config, style=lbl_style)

			
		except Exception as err:
			Logger.exception(str(err))





class Hp_widget(Container):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		# apply default style elements, these can be overruled by kwargs
		self.style.update({'background-color':'transparent', 'position':'absolute'})
		
		# # Om top, left height en width gewoon als getal op te kunnen geven worden deze kwargs binnengehaald, geconverteerd en in kwargs teruggezet
		for attr_name in ['height', 'width', 'top', 'left']:
			if attr_name in kwargs:
				attr = kwargs[attr_name]
				if type(kwargs[attr_name]) == str:	pass
				else:								kwargs[attr_name] = "%spx" % kwargs[attr_name]
		
		# alle kwargs worden nagelopen en ze vervangen de args in de default config en style dictionaries
		for arg in list(kwargs.keys()):
			try:
				self.style[arg.replace("_", "-")] = kwargs[arg]
			except Exception as err:
				Logger.error(f'Problem handling kwarg {arg} with value {kwargs[arg]}: {err}')
		self.build()
		return
	
	def build(self, **kwargs):
		from JSEM_Commons import Load_Images
		from Config import IMAGES_LOCATION
		dps = DATAPOINTS_ID
		
		def on_btn_switched(switch, state, dp_id, if_true, if_false, **kwargs):
			# now send the new value to the interface
			DATAPOINTS_ID[dp_id].write_value('0' if state else '4')
			
		def on_btn_update(btn_widg:Union[Switch, PushBtn], dp:Datapoint):
			nw_state = (dp.value[0]=='0')
			if btn_widg.get_value() != nw_state:
				btn_widg.set_value(nw_state)

		def up_dwn_btn_clicked(*args, **kwargs):
			incr = kwargs.get('incr', 0.0)
			nw_value = dps[sl_temp_corr].value + incr
			dps[sl_temp_corr].write_value(nw_value)

		
		ind_config = {}
		ind_style = {} 
		
		rect_config={}
		rect_style={'border-style':'none', 'border-radius':'0px', 'text-color':"white"}

		buff_config = dict(show_minmax=False, unit='%')
		buff_cond_format =	[
							dict(cond="gte", check_value=0.95 * dps[Max_Energy_Buf].value, true="red", false="green", qit=True),
							dict(cond="gte", check_value=0.9 * dps[Max_Energy_Buf].value, true="orange", false="green", qit=True),
							dict(cond="ste", check_value=5.0, true="red", false="green", qit=True),
							dict(cond="ste", check_value=10.0, true="orange", false="green", qit=True)
							]
		buff_style = 	{	
					'fill-background-color':"green", 
					'border-style':"solid", 'border-width':"2px", 'border-color':"grey", 'border-radius':"5px", 
					'value-color':'purple', 'value-font-size':"2cqh", 
						}
		
		
		lbl_config = dict(show_name=False, show_subcat=False, show_value=True, show_unit=True, enable_RW=False)
		lbl_style = {	
						'value-color':'white', 'value-width':'70%', 'value-text-align':"left", 'value-background':'transparent',
						'unit-color':'white', 'unit-font-size':'0.8em', 'unit-width':'30%', 
						'width':'15px', 'height':'8px', 'font-size':'100%'
					}
		try:
			topline = JSEM_Rect(self, top='0%', left='0%', width='100%', height='20%', background_color='grey', style=rect_style, config=rect_config)
			
			weather = JSEM_WeatherIcon(topline, dps[frcst_icoon], top='0%', left='3%', height='100%', width='94%',
										lookahead=8, interval=3, svg_images=False, image_source='Weathericons')
			
			status = JSEM_Rect(self, top='22%', left='0%', width='70%', height='20%', background_color='black', style=rect_style, config=rect_config)
			heat_ind = JSEM_Rect(status, dps[Act_Power_01], top='20%', left='5%', width='15%', height='60%', style=rect_style, config=rect_config,
									cond_format = [dict(cond="gt", check_value=0.0, prop='visibility', true="visible", false="hidden")])
			heat_ind.type='img'
			heat_ind.attributes['src']=Load_Images('heating')
			
			cool_ind = JSEM_Rect(status, dps[Act_Power_01], top='20%', left='5%', width='15%', height='60%', style=rect_style, config=rect_config,
									cond_format = [dict(cond="st", check_value=0.0, prop='visibility', true="visible", false="hidden")])
			cool_ind.type='img'
			cool_ind.attributes['src']=Load_Images('cooling')
			
			thrm_ind = JSEM_Label(status, dps[sl_temp_corr], config=lbl_config, style=lbl_style, top='10%', left='25%', width='35%', height='80%',
									value_font_weight='bold', value_font_size='1.5em')
						
			hp_ind = gui.Label(text='hp', style=f'position:absolute;top:25%;left:65%;width:10%;height:25%;font-size:0.7em;background:green;'
									 f'visibility:{"hidden" if (dps[mode_verwarmen].value=="4: uit") else "visible"}')
			hp_ind.refresh = lambda dp:hp_ind.set_style(f'visibility:{"hidden" if (dp.value=="4: uit") else "visible"}')
			dps[mode_verwarmen].subscribed_widgets.append(hp_ind)
			
			hpbst_ind = gui.Label(text='bst', style=f'position:absolute;top:50%;left:65%;width:10%;height:25%;font-size:0.7em;background:red;'
										f'visibility:{"visible" if (dps[use_hp_strategy].value and dps[hp_plan].value) else "hidden"}')
			hpbst_ind.refresh = lambda dp:hpbst_ind.set_style(f'visibility:{"visible" if (dps[use_hp_strategy].value and dps[hp_plan].value) else "hidden"}')
			dps[use_hp_strategy].subscribed_widgets.append(hpbst_ind)
			dps[hp_plan].subscribed_widgets.append(hpbst_ind)
			
			status.append([hp_ind, hpbst_ind])


			# Bediening/ Controls
			up_btn = Button()
			up_btn.style.update({	'position':'absolute', 'top':'44%', 'left':'0%', 'width':'22%', 'height':'24%', 'background-color':'black',
									'background-image': f"url({Load_Images('up')})", 'background-position': '50% 50%', 
									'background-repeat':'no-repeat', 'background-size':'100% 80%'})
			# up_btn.onclick.connect(lambda *args: dps[sl_temp_corr].write_value(dps[sl_temp_corr].value + 0.5))
			up_btn.onclick.connect(up_dwn_btn_clicked, incr=1.0)

			dwn_btn = Button()
			dwn_btn.style.update({	'position':'absolute', 'top':'68%', 'left':'0%', 'width':'22%', 'height':'24%', 'background-color':'black',
									'background-image': f"url({Load_Images('down')})", 'background-position': '50% 50%', 
									'background-repeat':'no-repeat', 'background-size':'100% 80%'})
			dwn_btn.onclick.connect(up_dwn_btn_clicked, incr=-1.0)

			
			on_btn = Switch(on_text='AUT', off_text='UIT',initial_state=(dps[mode_verwarmen].value.strip()[0]=='0'),
							style="position:absolute; top:44%; left:24%; width:20%; height:47%")
			# on_btn.onswitched.connect(on_btn_switched)
			on_btn.onswitched.connect(lambda widg, state:dps[mode_verwarmen].write_value('0' if state else '4'))
			on_btn.refresh = lambda dp: on_btn.set_value(dp.value[0]!='4')
			dps[mode_verwarmen].subscribed_widgets.append(on_btn)
			
			smart_btn = PushBtn(text='SMART', initial_state=dps[use_hp_strategy].value,
								style = 'position:absolute; top:44%; left:48%; width:20%; height:15%')
			smart_btn.onpushed.connect(lambda widg, state:dps[use_hp_strategy].write_value(state))
			smart_btn.refresh = lambda dp:smart_btn.set_value(dp.value)
			dps[use_hp_strategy].subscribed_widgets.append(smart_btn)

		
			self.append([up_btn, dwn_btn, on_btn, smart_btn])

			# Buffervat
			buff_cont = JSEM_Rect(self, top='22%', left='72%', width='28%', height='70%', background_color='black', style=rect_style, config=rect_config)
			buff = JSEM_Buffer(buff_cont, dps[Act_Energy_Buf], top='10%', left='10%', width='80%', height='80%',
								config=buff_config, style=buff_style, min_value=0.0, max_value=dps[Max_Energy_Buf].value,
								cond_format=buff_cond_format)
			
			# Bottomline
			btmline = JSEM_Rect(self, top='94%', left='0%', width='100%', height='6%', background_color='grey', style=rect_style, config=rect_config)
			# time = JSEM_Label(btmline, dps[EBUS_Timestamp_1], config=lbl_config, style=lbl_style, top='10%', left='3%', width='35%', height='80%',
			# 						value_font_weight='bold', value_font_size='0.7em', show_unit=False, value_width='100%')
			temp = JSEM_Label(btmline, dps[BuitenTemperatuur_act], config=lbl_config, style=lbl_style, top='10%', left='85%', width='15%', height='80%',
									value_font_weight='bold', value_font_size='0.7em')
									
									
	
			
		except Exception as err:
			Logger.exception(str(err))

class BarChart_widget(Container):
	
	def __init__(self, datapoints=[], title='', **kwargs):
		super().__init__(**kwargs)
		# apply default style elements, these can be overruled by kwargs
		self.style.update({'background-color':'transparent', 'position':'absolute'})
		
		# # Om top, left height en width gewoon als getal op te kunnen geven worden deze kwargs binnengehaald, geconverteerd en in kwargs teruggezet
		for attr_name in ['height', 'width', 'top', 'left']:
			if attr_name in kwargs:
				attr = kwargs[attr_name]
				if type(kwargs[attr_name]) == str:	pass
				else:								kwargs[attr_name] = "%spx" % kwargs[attr_name]
		
		# alle kwargs worden nagelopen en ze vervangen de args in de default config en style dictionaries
		for arg in list(kwargs.keys()):
			try:
				self.style[arg.replace("_", "-")] = kwargs[arg]
			except Exception as err:
				Logger.error(f'Problem handling kwarg {arg} with value {kwargs[arg]}: {err}')
		self.title = title
		self.datapoints = datapoints
		if datapoints: self.build()
		self.onclick.connect(self.maximize_chart)
		return
		
	def build(self, *args, **kwargs):
		dp = DATAPOINTS_ID
		try:
			
			style = 	{
						# svg style elements
						'margin':'0px', 'background-color':'transparent', 'border-style':'none', 'font-size':'100%', 
						'position':'absolute', 'top':'0%', 'left':'0%', 'width':'100%', 'height':'100%'
							}
			config = dict(allow_dragdrop=False, always_refresh=True, highlight_now=True)

			chart_config = dict(
									title = self.title,
									x_label_rotation=90,
									show_legend = False,
									print_values = False, 
									x_title = "Uur"
								)

			barchart = JSEM_Bar_Chart(self, datapoints=self.datapoints, dataselection = DataSelection.Day, selecteddate=datetime.now(),
											config=config, style=style, chart_config=chart_config)
		except Exception as err:
			Logger.exception(str(err))

	def maximize_chart(self, *args, **kwargs):
		chart_cont = JSEM_ChartCont(DataCont, self.datapoints, show_controlbox=True, show_legendbox=True, load_extra_datapoints=False,
						top='10%', left='10%', height='80%', width='80%', 
						ctrlbox_background_color='darkgrey',
						background_color='white', border_style='solid', border_color='black')


class LineChart_widget(Container):
	def __init__(self, datapoints=[], title='', **kwargs):
		super().__init__(**kwargs)
		# apply default style elements, these can be overruled by kwargs
		self.style.update({'background-color':'transparent', 'position':'absolute'})
		
		# # Om top, left height en width gewoon als getal op te kunnen geven worden deze kwargs binnengehaald, geconverteerd en in kwargs teruggezet
		for attr_name in ['height', 'width', 'top', 'left']:
			if attr_name in kwargs:
				attr = kwargs[attr_name]
				if type(kwargs[attr_name]) == str:	pass
				else:								kwargs[attr_name] = "%spx" % kwargs[attr_name]
		
		# alle kwargs worden nagelopen en ze vervangen de args in de default config en style dictionaries
		for arg in list(kwargs.keys()):
			try:
				self.style[arg.replace("_", "-")] = kwargs[arg]
			except Exception as err:
				Logger.error(f'Problem handling kwarg {arg} with value {kwargs[arg]}: {err}')
				
		self.title = title
		self.datapoints = datapoints
		if datapoints: self.build()
		self.onclick.connect(self.maximize_chart)
		return
		
	def build(self, *args, **kwargs):
		dp = DATAPOINTS_ID
		try:
			style = 	{
						# svg style elements
						'margin':'0px', 'background-color':'transparent', 'border-style':'none', 'font-size':'100%', 
						'position':'absolute', 'top':'0%', 'left':'0%', 'width':'100%', 'height':'100%'
							}
			config = dict(allow_dragdrop=False, always_refresh=True, highlight_now=False)

			chart_config = dict(
									title = self.title,
									x_label_rotation=90,
									show_legend = False,
									print_values = False, 
									x_title = "Uur"
								)

			linechart = JSEM_Line_Chart(self, datapoints=self.datapoints, dataselection = DataSelection.Day, selecteddate=datetime.now(),
											config=config, style=style, chart_config=chart_config)
		except Exception as err:
			Logger.exception(str(err))

	def maximize_chart(self, *args, **kwargs):
		chart_cont = JSEM_ChartCont(DataCont, self.datapoints, show_controlbox=True, show_legendbox=True, load_extra_datapoints=False,
						top='10%', left='10%', height='80%', width='80%', 
						ctrlbox_background_color='darkgrey',
						background_color='white', border_style='solid', border_color='black')

	
def main(args):
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
