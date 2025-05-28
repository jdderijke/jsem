import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from Common_Enums import *
from Common_Routines import dump, Waitkey, Is_NOE, IsNot_NOE, expandcollapse, get_days_in_month
from Common_Routines import set_css_sizes, set_mouse, set_widget_colors, first_number, Load_Images
from Datapoint_IDs import *

import Common_Data
from Common_Data import DATAPOINTS_NAME
# from GUI_predef_widgets import DataCont
from LogRoutines import Logger
from Config import *

# from Config import Default_ChartMode, Max_Chart_Points, Best_dtFormat, MaxValuesForBarChart

 
import remi.gui as gui
from remi.gui import *
from remi import start, App
import pygal 
from pygal import Config
from pygal_extras import LineBar
from pygal.style import Style
from DB_Routines import get_values_from_database, get_df_from_database

import pandas as pd
import numpy as np


default_bg_color = "red"
default_font_size = "18px"
default_label_width = 70
default_label_height = 18

class PyGal(gui.Svg):
	def set_content(self, chart):
		# Bij het renderen moet is_unicode op True worden gezet, anders zien we geen special characters (zoals degree signs etc.)
		self.data = chart.render(is_unicode=True)
		self.add_child("chart", self.data)

class DateTimeLine(pygal.DateTimeLine):
	def __init__(self, config=None, **kwargs):
		super(DateTimeLine, self).__init__(config=config, **kwargs)
		self.y_title_secondary = kwargs.get('y_title_secondary')

	def _make_y_title(self):
		super(DateTimeLine, self)._make_y_title()
		
		# Add secondary title
		if self.y_title_secondary:
			yc = self.margin_box.top + self.view.height / 2
			# xc = self.width - 10
			xc = self.width
			text2 = self.svg.node(
				self.nodes['title'], 'text', class_='title',
				x=xc,
				y=yc
			)
			text2.attrib['transform'] = "rotate(%d %f %f)" % (
				-90, xc, yc)
			text2.text = self.y_title_secondary

class Bar(pygal.Bar):
	def __init__(self, config=None, **kwargs):
		super(Bar, self).__init__(config=config, **kwargs)
		self.y_title_secondary = kwargs.get('y_title_secondary')

	def _make_y_title(self):
		super(Bar, self)._make_y_title()
		
		# Add secondary title
		if self.y_title_secondary:
			yc = self.margin_box.top + self.view.height / 2
			# xc = self.width - 10
			xc = self.width
			text2 = self.svg.node(
				self.nodes['title'], 'text', class_='title',
				x=xc,
				y=yc
			)
			text2.attrib['transform'] = "rotate(%d %f %f)" % (
				-90, xc, yc)
			text2.text = self.y_title_secondary


class AxeSelection(Enum):
	primary=1
	secondary=2
	hidden=3

class AxisScales():
	def __init__(self, *args, **kwargs):
		self.y_axis_min = None
		self.y_axis_max = None
		self.is_used = False
		self.unit = None
		
	def scalefit(self, dp, data):
		if not self.is_used: 
			if len(data) > 0:
				self.y_axis_min = min(data)
				self.y_axis_max = max(data)
			self.unit = dp.unit
			self.is_used = True
			return True
		else:
			# Only combine axis with same dp.unit
			if dp.unit != self.unit: return False
			if len(data) == 0: return True
			nw_min = min(data)
			nw_max = max(data)
			# make sure the details of (max-min) remain distinguishable
			if nw_max < 0.2 * self.y_axis_min or self.y_axis_max < 0.2 * nw_max: return False
			# if (nw_max - nw_min) < 0.1 * self.y_axis_max or (self.y_axis_max - self.y_axis_min) < 0.1 * nw_max: return False
			# assign new scale limits
			self.y_axis_min = min(self.y_axis_min, nw_min)
			self.y_axis_max = max(self.y_axis_max, nw_max)
			return True
			
			

class JSEM_GUI(object):
	def __init__(self, parent=None, datapoint=None, default_config={}, default_style={}, *args, **kwargs):
		super().__init__(**kwargs)
		# define the default style and config
		self.style.update(default_style)
		self.config = default_config.copy()
		
		# # Om top, left height en width gewoon als getal op te kunnen geven worden deze als args binnengehaald en geconverteerd
		for attr_name in ['height', 'width', 'top', 'left']:
			if attr_name in kwargs:
				attr = kwargs[attr_name]
				if type(attr) == str:	pass
				else:					kwargs[attr_name] = "%spx" % attr
		# print('nw kwargs %s' % kwargs)
		
		# print(self.style)
		# input('any key')
		
		self.value = None
		self.parent = None
		self.datapoint = None
		self.cond_format = []
		
		# extract the named *arg arguments
		config = kwargs.pop('config',None)
		if config and type(config)==dict: 	self.config.update(config)
		style = kwargs.pop('style',None)
		if style and type(style)==dict: 	self.style.update(style)
		cond_format = kwargs.pop('cond_format',None)
		if cond_format:
			if type(cond_format)==list: 	self.cond_format = cond_format
			else: 							self.cond_format = [cond_format]


		# alle kwargs worden nagelopen en ze vervangen de args in de default config en style dictionaries
		for arg in list(kwargs.keys()):
			if arg in self.config: 			self.config[arg] = kwargs[arg]
			else:
				try:
					self.style[arg.replace("_", "-")] = kwargs[arg]
				except Exception as err:
					Logger.error(f'Problem handling kwarg {arg} with value {kwargs[arg]}: {err}')

		# append to the parent, if any
		self.parent = parent
		if self.parent: self.parent.append(self)
		# subscribe to the datapoint, if any
		self.datapoint = datapoint
		if self.datapoint: self.connect_datapoint()
		

	def refresh (self, *args, **kwargs):
		# Logger.info(f'{type(self)} refresh called, args: {args}, kwargs: {kwargs}')
		dp = kwargs.get('datapoint', None)
		if dp is None: 									dp = kwargs.get('dp', None)
		if dp is None and self.datapoint is not None: 	dp=self.datapoint
		if dp is not None:
			# Logger.info(f'Widget refresh from datapoint {dp.name}, new value = {dp.value}')
			if type(dp.value)==float:
				if dp.decimals: 	self.value = round(dp.value, dp.decimals)
				else:				self.value = round(dp.value, 2)
			else: self.value = dp.value
		else:
			# Logger.info(f'Widget refresh from nwvalue kwarg')
			self.value = kwargs.get("nwvalue", self.value)
			
		# Logger.info(f'new widget value = {self.value}')


	def connect_datapoint(self):
		self.config['unit'] = self.datapoint.unit
		# configure conditional formatting rules based on the sig_rule of the datapoint
		if self.config.get('adopt_dp_signals', False) and self.config.get('dp_signal_prop',False) and self.datapoint.sig_rule: 
			sig_rules = self.datapoint.sig_rule.lower().strip().replace(' ','').split("&")
			prop = self.config['dp_signal_prop']
			false_value = self.style[prop] 
			for sig_rule in sig_rules:
				if sig_rule.startswith('alarm'):
					rest_rule = sig_rule[len('alarm'):]
					true_value = Alarm_bg_color
				elif sig_rule.startswith('warning'):
					rest_rule = sig_rule[len('warning'):]
					true_value = Warning_bg_color
				elif sig_rule.startswith('signal'):
					rest_rule = sig_rule[len('signal'):]
					true_value = Signal_bg_color
				else:
					continue
				cond = rest_rule[:first_number(rest_rule)]
				check_value = float(rest_rule[first_number(rest_rule):])
				self.cond_format.append(dict(cond=cond, check_value=check_value, prop=prop, 
													true=true_value, false=false_value, qit=True))
		# Subscribe this widget to the datapoint for dynamic updates
		self.datapoint.subscribed_widgets.append(self)
		# but to initialize copy the value now, make sure to use the parent method, not the child overwritten method....
		__class__.refresh(self)
		
		# # but to initialize copy the value now
		# dp = self.datapoint
		# if type(dp.value)==float:
			# if dp.decimals: 	self.value = round(dp.value, dp.decimals)
			# else:				self.value = round(dp.value, 2)
		# else: self.value = dp.value
		
	def check_condition(self, cond_format):
		check = False
		prop_nwvalue = None
		# check if the condition is satisfied on the self.value
		if self.value is None: check=False
		elif cond_format is None: check=False
		elif cond_format['cond'] in ["gt",">"] and self.value > cond_format["check_value"]: check=True
		elif cond_format['cond'] in ["gte",">="] and self.value >= cond_format["check_value"]: check=True
		elif cond_format['cond'] in ["st","<"] and self.value < cond_format["check_value"]: check=True
		elif cond_format['cond'] in ["ste","<="] and self.value <= cond_format["check_value"]: check=True
		elif cond_format['cond'] in ["eq","=","=="] and self.value == cond_format["check_value"]: check=True
		elif cond_format['cond'] in ["neq","!="] and self.value != cond_format["check_value"]: check=True
		else: check=False
		
		if check:
			prop_nwvalue = cond_format.get('true', None)
		else:
			prop_nwvalue = cond_format.get('false', None)
			
		return check, prop_nwvalue


				

class JSEM_SolidGauge(gui.Svg):
	def __init__(self, parent=None, datapoint=None, *args, **kwargs):
		try:
			# print ("PyGal_SolidGauge init called")
			super().__init__(*args, **kwargs)
			self.css_position = "absolute"
			
			self.datapoint = datapoint

			self.parent = parent
			if self.parent is not None:
				self.key = self.parent.append(self)
			else:
				self.key=None

			
			
			# Check optional parameters in kwargs
			self.attributes["title"]=kwargs.get("tooltip","")
			self.css_font_size = kwargs.get("fontsize", "20px")
			kwargs.pop("fontsize",None)
			
			self.max_value = kwargs.get("max_value", 100)
	
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

			kwargs.pop("gauge_style",None)
			self.custom_config = kwargs
			# force an update en breng de chart alive....
			

			if self.datapoint != None:
				self.datapoint.subscribed_widgets.append(self)
				self.refresh()
			else:
				self.update()

		except Exception as err:
			raise Exception(str(err))

	def set_content(self, chart):
		self.data = chart.render()
		self.add_child("chart", self.data)
		

	def update(self, value=0.0):
		# print ("Update called with value: ", value)
		self.gauge_chart = pygal.SolidGauge(
											**self.custom_config,
											style = self.custom_style
											)
		self.gauge_chart.add('Series', [{'value': value, 'max_value':self.max_value}])
		self.set_content(self.gauge_chart)

	def refresh(self, *args, **kwargs):
		
		self.gauge_chart = pygal.SolidGauge(
											**self.custom_config,
											style = self.custom_style
											)
		dp = self.datapoint
		dpname = (dp.name[:12] + '..') if len(dp.name) > 12 else dp.name
		self.gauge_chart.add(str(dpname), [{'value': dp.value, 'max_value':self.max_value}])

		self.set_content(self.gauge_chart)
		

		
class JSEM_BalancedGauge(Container):
	def __init__(self, parent=None, datapoint=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.value = None

		self.css_position = "absolute"
		
		self.max_value = kwargs.get("max_value", 100)
		self.datapoint = datapoint

		self.parent = parent
		if self.parent is not None:
			self.key = self.parent.append(self)
		else:
			self.key=None

		self.bgcolor = kwargs.get("bgcolor", "transparent")
		
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
		self.Gauge1 = JSEM_SolidGauge	(
										show_y_labels = False,
										show_x_labels = False,
										show_legend = False,
										inner_radius = kwargs.get("inner_radius", 0),
										top="0px", left="0px", width="200%", height="100%", 
										max_value = self.max_value,
										parent_width = kwargs.get("width", "400px"),
										parent_height = kwargs.get("height", "400px"),
										gauge_style = dict(colors=["red"])
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
		self.Gauge2 = JSEM_SolidGauge	(
										show_y_labels = False,
										show_x_labels = False,
										inner_radius=kwargs.get("inner_radius", 0),
										top="0px", left="0px", width="200%", height="100%", 
										max_value = self.max_value,
										parent_width = kwargs.get("width", "400px"),
										parent_height = kwargs.get("height", "400px"),
										gauge_style = dict(colors=["green"])
										)
		self.Gauge2.style["transform"] = "translate(-50%,0px)"
		SubCont2.append(self.Gauge2)
		
		self.append(SubCont1)
		self.append(SubCont2)
		
		if self.datapoint is not None:
			self.datapoint.subscribed_widgets.append(self)
			self.refresh()
		else:
			self.update()
		

	def refresh(self, *args, **kwargs):
		'''
		A refresh reloads the latest values from the associated datapoints and forces a redraw
		To update the graph when NO datapoints are used: use the update method
		'''
		# print("refresh Balanced Gauge called")
		
		dp = self.datapoint
		if dp.value is None: return
		
		if dp.value == 0.0:
			self.Gauge1.update(0.0)
			self.Gauge2.update(0.0)
		elif dp.value > 0.0:
			self.Gauge1.update(0.0)
			self.Gauge2.update(dp.value)
		elif dp.value < 0.0:
			self.Gauge2.update(0.0)
			self.Gauge1.update(abs(dp.value))
				
	def update(self,value=0.0):
		'''
		An update loads a value and forces a redraw, updates are used when NO datapoints are linked
		When one or more datapoints are linked, use the refresh method
		'''
		if value == 0:
			self.Gauge1.update(0.0)
			self.Gauge2.update(0.0)
		elif value > 0:
			self.Gauge1.update(0.0)
			self.Gauge2.update(value)
		elif value < 0:
			self.Gauge2.update(0.0)
			self.Gauge1.update(abs(value))
		
	
class JSEM_LineBar(gui.Svg, LineBar):
	'''
	The JSEM_LineBar class inherits from Remis Svg and Pygal_extra LineBar classes.
	It adds the following to the Svg class
	- implements a container for the Svg (containing the rendered LineBar) with:
		a date selector
		a DataSelection dropdown
		a close button
		a maximize button
		An interactive legend with clickable datapoints
	Sizing parameters passed will be set to this container. the Svg and buttons will fill up the container
	It adds the following to the LineBar
		click and drop functionality for combining graphs
		refresh functionality for dynamic chart updates
	'''
	def __init__(self, parent=None, datapoints=[], chart_types=[], *args, **kwargs):
		try:
			# Super() calls the parents __init__ function in as specific order (from left to right)
			super().__init__(*args, **kwargs)
			self.css_position = "absolute"
			self.datapoints = datapoints
			self.title = kwargs["title"] if "title" in kwargs else ""
			# Check optional parameters in kwargs
			if "tooltip" in kwargs: self.attributes["title"]=kwargs["tooltip"]
			
			self.bgcolor = kwargs["bgcolor"] if "bgcolor" in kwargs else "transparent"
			
			self.parent = parent
			if self.parent is not None:
				self.key = self.parent.append(self)
			else:
				self.key=None
		except Exception as err:
			pass
	
	
		
class JSEM_Line_Chart(JSEM_GUI, Svg):


	def __init__(self, parent=None, datapoints=[], chartinfo=Chart_Definitions['line'].copy(), dataselection = Default_ChartMode, 
								selecteddate = datetime.now(), chart_title=None, *args, **kwargs):

		# define the default styles and configs
		
		
		default_config = dict(allow_dragdrop=True, always_refresh=False)
									
		default_style = {
						# svg style elements
						'position':'absolute', 'margin':'0px', 'background-color':'transparent', 'border-style':'none', 
						'font-size':'100%','width':'100%', 'height':'100%'
						}
						
		self.chart_config = Config		(
								title = chartinfo['title'] if chart_title is None else chart_title,
								x_label_rotation=90,
								x_value_formatter=lambda dt: dt.strftime("%d-%m %H:%M"),
								show_legend = False,
								legend_at_bottom=True,
								x_title = "DateTime",
										)
										
		self.chart_style = Style		(
								background="transparent",
								plot_background="transparent",
								legend_font_size=20,
								label_font_size=20,
								major_label_font_size=20, 
								title_font_size=30,
								stroke_width = 2,
								colors=["red", "blue", "green", "black", "yellow", "orange", "purple", "darkgrey"]
										)

		# Allow all dataselections here, since its a linechart...  no datagrouping
		self.allowed_dataselections={
									DataSelection._Last50:DatabaseGrouping.All, 
									DataSelection._10min:DatabaseGrouping.All, 
									DataSelection._30min:DatabaseGrouping.All, 
									DataSelection._1hr:DatabaseGrouping.All, 
									DataSelection._2hr:DatabaseGrouping.All,
									DataSelection._6hr:DatabaseGrouping.All,
									DataSelection._12hr:DatabaseGrouping.All, 
									DataSelection._24hr:DatabaseGrouping.All, 
									DataSelection._48hr:DatabaseGrouping.All, 
									DataSelection._72hr:DatabaseGrouping.All,
									DataSelection._96hr:DatabaseGrouping.All,
									DataSelection.Day:DatabaseGrouping.All,
									DataSelection.Week:DatabaseGrouping.All, 
									DataSelection.Month:DatabaseGrouping.All, 
									DataSelection.Year:DatabaseGrouping.All
									}

		try:
			self.selecteddate = selecteddate
			self.dataselection = dataselection
			
			# the user can send arguments for the chart config and chart style, store these and remove them from kwargs
			tmpch_config = kwargs.pop('chart_config', None)
			if tmpch_config and type(tmpch_config)==dict:
				for attr, value in tmpch_config.items():
					if hasattr(self.chart_config, attr):
						setattr(self.chart_config, attr, value)
			
			tmpch_style = kwargs.pop('chart_style', None)
			if tmpch_style and type(tmpch_style)==dict:
				for attr, value in tmpch_style.items():
					if hasattr(self.chart_style, attr):
						setattr(self.chart_style, attr, value)
			# store the initial color scheme locally
			self.colors = self.chart_style.colors
			
			# A chart does NOT link to a single datapoint via the JSEM GUI inheritance
			super().__init__(parent, None, default_config, default_style, **kwargs)
			
			self.chartinfo = chartinfo
			
			# check if the chart belongs to a chart container, 
			self.parent_chartcont = None
			if self.parent is not None and type(self.parent)==JSEM_ChartCont: self.parent_chartcont = parent

			# convert the datapoints to charted_datapoints
			self.charted_datapoints = dict()
			for teller, dp in enumerate(datapoints):
				self.charted_datapoints[dp.name]={"visible": True, "datapoint": dp, "color": self.colors[teller], 'axis':None}
				
			# attach the handlers for the chart combine functionality (by click and drag)
			self.onmousedown.connect(self.chart_selected)
			self.ontouchstart.connect(self.chart_selected)
			self.onmouseup.connect(self.chart_dropped)
			self.ontouchend.connect(self.chart_dropped)

			# force an update and bring the chart alive....
			self.update()
			
		except Exception as err:
			Logger.exception(str(err))
		
	def set_content(self, chart):
		'''
			This method renders a PyGal Chart object into an SVG object that can be handled by Remi
		'''
		# Bij het renderen moet is_unicode op True worden gezet, anders zien we geen special characters (zoals degree signs etc.)
		self.data = chart.render(is_unicode=True)
		self.add_child("chart", self.data)
		# print(f'Number of children = {len(self.children)}')



	def update(self, **kwargs):
		# set waitcursor
		Common_Data.MAIN_CONTAINER.style["cursor"]="wait"
		
		if not kwargs.get('from_refresh', False):
			# update subscriptions
			if self.dataselection in [DataSelection._Last50, DataSelection._10min, DataSelection._30min, DataSelection._1hr] or \
																			self.config['always_refresh']:
				# subscribe deze line chart bij alle charted datapoints als die dat niet al is....
				for dpname in self.charted_datapoints:
					dp = self.charted_datapoints[dpname]["datapoint"]
					if not (self in dp.subscribed_widgets):
						dp.subscribed_widgets.append(self)
			else:
				# unsubscribe deze line_chart bij de datapoints die op de kaart staan. geen refresh gewenst voor deze dataselection
				for dpname in self.charted_datapoints:
					dp = self.charted_datapoints[dpname]["datapoint"]
					if self in dp.subscribed_widgets:
						dp.subscribed_widgets.remove(self)
		
		# get the data
		if self.dataselection == DataSelection._Last50:
			result_df = None
			for dpinfo in self.charted_datapoints.values():
				charted_dp = dpinfo['datapoint']
				if result_df is None: 
					result_df = pd.DataFrame()
					result_df['timestamp'] = charted_dp.last50_timestamps
					result_df[charted_dp.name] = charted_dp.last50_values
				else:
					add_df = pd.DataFrame()
					add_df['timestamp'] = charted_dp.last50_timestamps
					add_df[charted_dp.name] = charted_dp.last50_values
					result_df = pd.merge_asof(result_df, add_df, on="timestamp", direction="backward")
			# because the timestamp is retrieved from the FIRST datapoint last50 values, it is possible that NaN entries show up for merged dp's'
			# result_df = result_df.dropna()
			
		else:
			# get the data
			dpIDs = [dpinfo['datapoint'].ID  for dpinfo in self.charted_datapoints.values()]
			datagrouping = self.allowed_dataselections[self.dataselection]
			# if self.dataselection in [DataSelection._10min, DataSelection._30min, DataSelection._1hr, DataSelection._2hr, DataSelection._6hr,
										# DataSelection._12hr, DataSelection._24hr, DataSelection._48hr]:
				# dataselection_date = datetime.now()
			# else:
				# dataselection_date = self.selecteddate
			dataselection_date = self.selecteddate
			
			result_df = get_df_from_database(
											dpIDs=dpIDs,
											dataselection = self.dataselection,
											datagrouping = datagrouping,
											aggregation = Aggregation[self.chartinfo['aggr']],
											dataselection_date = dataselection_date,
											maxrows = Max_Chart_Points
											)
		
		if result_df is None: return
		result_df = result_df.dropna()
		
		# print (result_df)
		
		
		# initialize
		primary_axis = AxisScales()
		secondary_axis = AxisScales()
		prm_colors, sec_colors = [], []
		prm_title, sec_title = '', ''
		
		for dp_info in self.charted_datapoints.values():
			if not dp_info["visible"]: continue
			charted_dp = dp_info["datapoint"]
			# check if a secondary axis is needed....
			if primary_axis.scalefit(charted_dp,result_df[charted_dp.name].values): 
				dp_info['axis']=AxeSelection.primary
				prm_title = charted_dp.unit
				prm_colors += [dp_info['color']]
			elif secondary_axis.scalefit(charted_dp,result_df[charted_dp.name].values): 
				dp_info['axis']=AxeSelection.secondary
				sec_title = charted_dp.unit
				sec_colors += [dp_info['color']]
			else: 
				dp_info['axis']=AxeSelection.hidden
				# cant display this item at this time, make hidden and redraw legends
				dp_info["visible"] = False
				if self.parent_chartcont: self.parent_chartcont.fill_legendbox()
				continue
				
		self.chart_style.colors = prm_colors + sec_colors
				
		# Create a DateTimeLine chart
		self.chart = DateTimeLine(self.chart_config, style=self.chart_style, y_title=prm_title, y_title_secondary=sec_title)
			
		for dp_info in self.charted_datapoints.values():
			if not dp_info["visible"]: continue
			charted_dp = dp_info["datapoint"]
			
			x_labels = [datetime.fromtimestamp(x) for x in result_df["timestamp"].values]
			
			XY_values = list(zip(x_labels, result_df[charted_dp.name].values))
			# A DateTimeLine expects tuples of x,y values as values argument in the chrt.add
			self.chart.add	(
							charted_dp.name + " (" + str(charted_dp.unit) + ")",
							XY_values,
							show_dots=(self.dataselection in [	DataSelection._Last50, 
																DataSelection._10min, 
																DataSelection._30min, 
																DataSelection._1hr
																]),
							secondary = (dp_info['axis'] == AxeSelection.secondary)
							)
		
		self.chart.value_formatter = lambda x: '%.1f' % x 
		self.chart.x_value_formatter = lambda dt: dt.strftime(Best_dtFormat.get(self.dataselection, "%d-%m %H:%M"))
		self.set_content(self.chart)
		Common_Data.MAIN_CONTAINER.style["cursor"]="default"
		

	def refresh(self, *args, **kwargs):
		try:
			# A call to the refresh of the upper class is not necessary, there is NO value that needs updating
			# super().refresh(*args, **kwargs)
			self.update()

		except Exception as err:
			Logger.exception(str(err))
		
	def chart_selected(self, *args, **kwargs):
		if not self.config['allow_dragdrop']: return
		
		# print('chart selected')
		Common_Data.SELECTED_CHART = self
		Common_Data.SELECTED_DATAPOINTS = self.charted_datapoints

	def chart_dropped(self, *args, **kwargs):
		if not self.config['allow_dragdrop']: return
		
		# anything to drop? dropped in self????
		if not Common_Data.SELECTED_CHART or Common_Data.SELECTED_CHART is self: return

		# check of er dp's zijn die al in de chart staan, zo niet dan toevoegen
		for dpname in Common_Data.SELECTED_DATAPOINTS:
			if dpname in self.charted_datapoints: continue		# oeps it is....dont add twice
			else:
				# add datapoint info to this chart
				self.charted_datapoints[dpname] = Common_Data.SELECTED_DATAPOINTS[dpname]
				# assign the next available color
				nwcolor = self.colors[len(self.charted_datapoints) - 1] if len(self.colors) >= len(self.charted_datapoints) else 'black'
				self.charted_datapoints[dpname]['color'] = nwcolor
				# and add datapoint to the parent ChartCont, if there is one
				if self.parent_chartcont: self.parent_chartcont.datapoints.append(Common_Data.SELECTED_DATAPOINTS[dpname]['datapoint'])

		for dpname in self.charted_datapoints:
			dp = self.charted_datapoints[dpname]["datapoint"]
			# remove old subscriptions for the old chart
			if Common_Data.SELECTED_CHART in dp.subscribed_widgets:
				dp.subscribed_widgets.remove(Common_Data.SELECTED_CHART)
			# (re)subscribe deze line_chart bij de datapoints die op de kaart staan.
			if self not in dp.subscribed_widgets:
				dp.subscribed_widgets.append(self)
				
		# ruim nu de oude chart op, 
		charts_parent = Common_Data.CHARTS_PARENT_CONTAINER
		this_chartcontainer = Common_Data.SELECTED_CHART.get_parent()
		charts_parent.remove_child(this_chartcontainer)

		Common_Data.SELECTED_CHART=None
		Common_Data.SELECTED_DATAPOINTS=None
		# re-generate the legendbox of the parent  chartcont
		if self.parent_chartcont: self.parent_chartcont.fill_legendbox()
		# re-present the chart
		self.update()



class JSEM_Map_Chart(gui.TableWidget):


	# def __get_selecteddate(self):
		# # return the current value
		# return self._selecteddate
	# def __set_selecteddate(self,nwvalue):
		# if nwvalue != self._selecteddate:
			# self._selecteddate = nwvalue
			# self.data_selection_changed()
	# selecteddate = property(__get_selecteddate,__set_selecteddate)



	# def __get_dataselection(self):
		# # return the current value
		# return self._dataselection
	# def __set_dataselection(self,nwvalue):
		# if nwvalue != self._dataselection:
			# if nwvalue in self.allowed_dataselections:
				# self._dataselection = nwvalue
			# else:
				# self.dataselection = DataSelection.Day
			# self.data_selection_changed()
	# dataselection = property(__get_dataselection,__set_dataselection)




	def __init__(self, parent=None, datapoints=[], chartinfo=None, dataselection = DataSelection.Day, selecteddate = datetime.now(), 
						rowheaders=None, columnheaders=None, chart_title=None, *args, **kwargs):
		try:
			self.allowed_dataselections = 	{
											# DataSelection.Hour:DatabaseGrouping.Tenmin,
											DataSelection.Day:DatabaseGrouping.Tenmin,
											DataSelection.Week:DatabaseGrouping.Hour,
											DataSelection.Month:DatabaseGrouping.Hour
											}

			self.selecteddate = selecteddate
			self.dataselection = dataselection if dataselection in self.allowed_dataselections else DataSelection.Day
			
			# Get the chart setup information of the leading datapoint
			if chartinfo is None: self.chartinfo = Chart_Definitions['bar'].copy()
			else: self.chartinfo = chartinfo
			self.chart_title = chart_title
			
			# remember your ancestors, they may come in handy
			self.parent = None
			self.parent_chartcont = None
			if parent is not None: 
				self.parent = parent
				if type(parent)==JSEM_ChartCont: self.parent_chartcont = parent


			# the number of rows and columns, so BEFORE headers etc... The dimensions of a map-chart are determined by
			# te dataselection chosen....
			self.rows = 31
			self.columns = 24
			
			# correct the size of the table for column and row headers
			if rowheaders: self.rowheaders = rowheaders
			elif self.chartinfo["y_row_labels"] != []: self.rowheaders = self.chartinfo["y_row_labels"]
			else: self.rowheaders = None
				
			if columnheaders: self.columnheaders = columnheaders
			elif self.chartinfo["x_col_labels"] != []: self.columnheaders = self.chartinfo["x_col_labels"]
			else: self.columnheaders = None
			
			self.row_offset = 1
			self.col_offset = 1
				
			super().__init__(n_rows=self.rows+self.row_offset, n_columns=self.columns+self.col_offset, *args, **kwargs)
			self.css_display = "table"
			self.css_float = "none"
			self.css_order = "-1"
			self.css_position = "static"
			# self.css_overflow = "scroll"
			self.use_title = False
			self.editable = False
			
			# get font, top, left, width and height for the SVG container
			set_css_sizes(widget=self, *args, **kwargs)
			# disable user selectable data, it does not work together with drag and drop charts/maps
			self.style["user-select"] = "none"

			# Check optional parameters in kwargs
			if "tooltip" in kwargs: self.attributes["title"]=kwargs["tooltip"]
			
			self.css_background_color = kwargs.get("bgcolor","transparent")
			self.css_color = kwargs.get("color","grey")
			self.nodata_color = kwargs.get("nodata_color", "transparent")
			self.active_color = kwargs.get("active_color", "red")
			# self.notactive_color = kwargs.get("notactive_color", "lightgreen")
			self.notactive_color = kwargs.get("notactive_color", "transparent")
			self.header_bgcolor = kwargs.get("header_bgcolor", "transparent")
			self.header_color = kwargs.get("header_color", "grey")


			self.colors = kwargs.get("colors", ["red", "blue", "green", "black", "yellow", "orange", "purple", "darkgrey"])
			
			# convert the datapoints to charted_datapoints
			self.charted_datapoints = dict()
			for teller, dp in enumerate(datapoints):
				if dp.name in DATAPOINTS_NAME: 
					self.charted_datapoints[dp.name]={"visible": True, "datapoint": DATAPOINTS_NAME[dp.name], "color": self.colors[teller]} 

			# # attach the handlers for the chart combine functionality (by click and drag)
			self.onmousedown.connect(self.chart_selected)
			self.ontouchstart.connect(self.chart_selected)
			self.onmouseup.connect(self.chart_dropped)
			self.ontouchend.connect(self.chart_dropped)

			self.custom_style=dict(colors=[])
			
			# een map of schedule hoeft NIET ge-update te worden
			# for dp in self.datapoints:
				# dp.subscribed_widgets.append(self)

			self.update()
			
		except Exception as err:
			Logger.exception(str(err))

	def chart_selected(self, *args, **kwargs):
		# print('chart selected')
		Common_Data.SELECTED_CHART = self
		Common_Data.SELECTED_DATAPOINTS = self.charted_datapoints

	def chart_dropped(self, *args, **kwargs):
		# anything to drop?
		if Common_Data.SELECTED_DATAPOINTS is None or Common_Data.SELECTED_CHART is None: return
		
		# dropped in self????
		if Common_Data.SELECTED_DATAPOINTS == self.charted_datapoints or Common_Data.SELECTED_CHART is self: return
			
		# print ("chartcontainer_dropped")
		# check of er dp's zijn die al in de chart staan, zo niet dan toevoegen
		for dpname in Common_Data.SELECTED_DATAPOINTS:
			if dpname in self.charted_datapoints:
				# oeps it is....dont add twice
				continue
			else:
				# add datapoint info to this chart
				self.charted_datapoints[dpname] = Common_Data.SELECTED_DATAPOINTS[dpname]
				# and to this ChartCont
				if self.parent_chartcont: self.parent_chartcont.datapoints.append(Common_Data.SELECTED_DATAPOINTS[dpname]['datapoint'])

		for dpname in self.charted_datapoints:
			dp = self.charted_datapoints[dpname]["datapoint"]
			# remove old subscriptions for the old chart
			if Common_Data.SELECTED_CHART in dp.subscribed_widgets:
				dp.subscribed_widgets.remove(Common_Data.SELECTED_CHART)
			# (re)subscribe deze line_chart bij de datapoints die op de kaart staan.
			dp.subscribed_widgets.append(self)
				
		# assign the colors to all datapoints on the chart
		for teller, dpinfo in enumerate(self.charted_datapoints.values()): 
			dpinfo["color"] = self.colors[teller]
				
		# ruim nu de oude chart op, 
		charts_parent = Common_Data.CHARTS_PARENT_CONTAINER
		this_chartcontainer = Common_Data.SELECTED_CHART.get_parent()
		charts_parent.remove_child(this_chartcontainer)

		Common_Data.SELECTED_CHART=None
		Common_Data.SELECTED_DATAPOINTS=None
		# re-generate the legendbox of the parent  chartcont
		if self.parent_chartcont: self.parent_chartcont.fill_legendbox()
		# re-present the chart
		self.update()

	def format_and_fill_table(self, dataframe=None):
		if dataframe is None: return
		# print ("Rowheaders: %s" % self.rowheaders)
		# print ("Columnheaders: %s" % self.columnheaders)
		# format the headers for the table:
		row_headers = None
		column_headers = None
		if self.dataselection in [DataSelection.Day, DataSelection._24hr]: 
			row_headers = ["uur %s" % x for x in range(24)] if self.rowheaders is None else (self.rowheaders + 24*[""])[:24]
		elif self.dataselection in [DataSelection._48hr]: 
			row_headers = ["uur %s" % x for x in range(48)] if self.rowheaders is None else (self.rowheaders + 48*[""])[:48]
		elif self.dataselection in [DataSelection._12hr]: 
			row_headers = ["uur %s" % x for x in range(12)] if self.rowheaders is None else (self.rowheaders + 12*[""])[:12]
		elif self.dataselection in [DataSelection._6hr]:
			row_headers = ["uur %s" % x for x in range(6)] if self.rowheaders is None else (self.rowheaders + 6*[""])[:6]
		elif self.dataselection in [DataSelection._2hr]: 
			row_headers = ["uur %s" % x for x in range(2)] if self.rowheaders is None else (self.rowheaders + 2*[""])[:2]
		elif self.dataselection in [DataSelection._1hr]:
			row_headers = [""]
		elif self.dataselection in [DataSelection.Week]: 
			row_headers = ["zondag","maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag"] if self.rowheaders is None else (self.rowheaders + 7*[""])[:7]
		elif self.dataselection in [DataSelection.Month]: 
			days_in_month = get_days_in_month(selecteddate=self.selecteddate)
			row_headers = ["%s" % (x + 1) for x in range(days_in_month)] if self.rowheaders is None else (self.rowheaders + days_in_month*[""])[:days_in_month]
		else: 
			row_headers = None

		if self.dataselection in [DataSelection.Day, DataSelection._24hr]: 
			column_headers = ["min %02d" % (x,) for x in range(0,60,10)] if self.columnheaders is None else (self.columnheaders + 6*[""])[:6]
		elif self.dataselection in [DataSelection._48hr]: 
			column_headers = ["min %s" % x for x in range(0,60,10)] if self.columnheaders is None else (self.columnheaders + 6*[""])[:6]
		elif self.dataselection in [DataSelection._12hr]: 
			column_headers = ["min %s" % x for x in range(0,60,10)] if self.columnheaders is None else (self.columnheaders + 6*[""])[:6]
		elif self.dataselection in [DataSelection._6hr]:
			column_headers = ["min %s" % x for x in range(0,60,10)] if self.columnheaders is None else (self.columnheaders + 6*[""])[:6]
		elif self.dataselection in [DataSelection._2hr]: 
			column_headers = ["min %s" % x for x in range(0,60,10)] if self.columnheaders is None else (self.columnheaders + 6*[""])[:6]
		elif self.dataselection in [DataSelection.Hour, DataSelection._1hr]: 
			column_headers = ["min %s" % x for x in range(0,60,10)] if self.columnheaders is None else (self.columnheaders + 6*[""])[:6]
		elif self.dataselection in [DataSelection.Week]: 
			column_headers = ["uur %s" % x for x in range(24)] if self.columnheaders is None else (self.columnheaders + 24*[""])[:24]
		elif self.dataselection in [DataSelection.Month]: 
			column_headers = ["uur %s" % x for x in range(24)] if self.columnheaders is None else (self.columnheaders + 24*[""])[:24]
		else: 
			column_headers = None
	
		# print(row_headers)
		# print(column_headers)
		# input('headers')
	
		if row_headers is not None and column_headers is not None:
			# we hebben dus een cel (0,0) waar we de title neer kunnen zetten...
			self.item_at(0,0).set_text(self.chartinfo['title'] if self.chart_title is None else self.chart_title)
	
		if row_headers is not None:
			for row_teller in range(self.rows):
				self.item_at(row_teller + self.row_offset,0).css_background_color = self.header_bgcolor
				self.item_at(row_teller + self.row_offset,0).css_color = self.header_color
				self.item_at(row_teller + self.row_offset,0).set_text(str(row_headers[row_teller]))
				
		if column_headers is not None:
			for col_teller in range(self.columns):
				self.item_at(0, col_teller + self.col_offset).css_background_color = self.header_bgcolor
				self.item_at(0, col_teller + self.col_offset).css_color = self.header_color
				self.item_at(0, col_teller + self.col_offset).set_text(str(column_headers[col_teller]))
	
		data_index=0
		for row_teller in range(self.rows):
			# BUG in FIREFOX!!!!---- you need to SET the height of the TableItem (cell) or else the embedded HBOX will get a height of 0%
			# and thus be invisible
			self.item_at(row_teller+self.row_offset, 0).css_height = "10%"
			for col_teller in range(self.columns):
				cell = self.item_at(row_teller+self.row_offset, col_teller+self.col_offset)
				cell.empty()
				cell.css_background_color=self.nodata_color
				# cell.css_background_color="yellow"
				HB = gui.HBox()
				HB.css_background_color=self.nodata_color
				HB.css_width="100%"
				HB.css_height="100%"
				cell.append(HB)


				for dp_info in self.charted_datapoints.values():
					if not dp_info["visible"]: continue
					charted_dp = dp_info["datapoint"]
					# We gaan er nu even van uit dat de Values alleen True of False kunnen zijn. De nummering van de map loopt van linkboven tot rechtsonder
					lbl = Label()
					lbl.css_background_color = dp_info["color"] if bool(dataframe[charted_dp.name][data_index]) == True else self.notactive_color
					lbl.css_width="100%"
					lbl.css_height="100%"
					HB.append(lbl)
					
				data_index +=1



	def calc_map_settings(self):
		# Calculate the dimensions for the table:
		if self.dataselection in [DataSelection.Day, DataSelection._24hr]: table_rows, table_cols = 24, 6
		elif self.dataselection in [DataSelection._48hr]: table_rows, table_cols = 48, 6
		elif self.dataselection in [DataSelection._12hr]: table_rows, table_cols = 12, 6
		elif self.dataselection in [DataSelection._6hr]: table_rows, table_cols = 6, 6
		elif self.dataselection in [DataSelection._2hr]: table_rows, table_cols = 2, 6
		# elif self.dataselection in [DataSelection.Hour, DataSelection._1hr]: table_rows, table_cols = 1, 6
		elif self.dataselection in [DataSelection.Week]: table_rows, table_cols = 7, 24
		elif self.dataselection in [DataSelection.Month]: table_rows, table_cols = get_days_in_month(selecteddate=self.selecteddate), 24
		else: return 0, 0, 0
		
		return table_rows * table_cols, table_rows, table_cols


	def update(self, *args, **kwargs):
		Common_Data.MAIN_CONTAINER.style["cursor"]="wait"

		# we need to create the new chart data
		# Now first calculate the dimensions of the new map and create a template dataframe with the correct dimensions and timestamps
		maxrows, self.rows, self.columns = self.calc_map_settings()
		dpIDs = [dpinfo['datapoint'].ID  for dpinfo in self.charted_datapoints.values()]
		datagrouping = self.allowed_dataselections[self.dataselection]
		result_df = get_df_from_database(
										dpIDs=dpIDs,
										dataselection = self.dataselection,
										datagrouping = datagrouping,
										aggregation = Aggregation[self.chartinfo['aggr']],
										dataselection_date = self.selecteddate
										)

		if result_df is None: return
		# Not existing timestamps will be filled with NaN values, replace those with 0
		# dat is handiger met een map, anders krijg je allemaal nodata meldingen voor momenten dat er nog geen plan is
		result_df = result_df.fillna(0)
		

		# re dim the TableWidget
		self.row_count = self.rows + self.row_offset
		self.column_count = self.columns + self.col_offset

		# build the chart_colors list for the map, skip any invisible datapoints from the colorlist
		chart_colors = []
		for dpinfo in self.charted_datapoints.values():
			if dpinfo["visible"]:
				chart_colors = chart_colors + [dpinfo["color"]]
		self.custom_style['colors'] = chart_colors

		# The dataselection may have changed, reformat the headers of the rows and columns
		self.format_and_fill_table(dataframe=result_df)
				
		Common_Data.MAIN_CONTAINER.style["cursor"]="default"


class JSEM_Bar_Chart(JSEM_GUI, Svg):
	'''
	Bar charts worden normaal gebruikt om een snel overzicht te krijgen in bijvoorbeeld kosten
	Dus (in tegenstelling tot een linechart) moet een barchart bij verschillende dataselections nogal wat rekenwerk verrichten
	Een barchart geeft de SOM of het GEMIDDELDE over de dataselection periode...
	'''
	def __init__(self, parent=None, datapoints=[], chartinfo=Chart_Definitions['bar'].copy(), dataselection = Default_ChartMode, 
								selecteddate = datetime.now(), chart_title=None, *args, **kwargs):

		# define the default styles and configs
		default_config = dict(allow_dragdrop=True, always_refresh=False, highlight_now=True)
									
		default_style = {
						# svg style elements
						'position':'absolute', 'margin':'0px', 'background-color':'transparent', 'border-style':'none', 
						'font-size':'100%','width':'100%', 'height':'100%'
						}
						
		self.chart_config = Config		(
								title = chartinfo['title'] if chart_title is None else chart_title,
								x_label_rotation=90,
								show_legend = False,
								legend_at_bottom=True,
								print_values = True, 
								print_values_position='top',
								x_title = "DateTime"
										)
		self.chart_style = Style		(
								background="transparent",
								plot_background="transparent",
								legend_font_size=20,
								value_font_size = 15,
								label_font_size=20,
								major_label_font_size=20, 
								title_font_size=30,
								colors=["green", "blue", "yellow", "red", "black", "orange", "purple", "darkgrey"]
										)
		# Allow all dataselections here
		self.allowed_dataselections={
									DataSelection._1hr:DatabaseGrouping.Tenmin, 
									DataSelection._2hr:DatabaseGrouping.Tenmin,
									DataSelection._6hr:DatabaseGrouping.Tenmin,
									DataSelection._12hr:DatabaseGrouping.Hour, 
									DataSelection._24hr:DatabaseGrouping.Hour, 
									DataSelection._48hr:DatabaseGrouping.Hour,
									DataSelection._72hr: DatabaseGrouping.Hour,
									DataSelection._96hr:DatabaseGrouping.Hour,
									# DataSelection.Hour:DatabaseGrouping.Tenmin,
									DataSelection.Day:DatabaseGrouping.Hour, 
									DataSelection.Week:DatabaseGrouping.Day, 
									DataSelection.Month:DatabaseGrouping.Day, 
									DataSelection.Year:DatabaseGrouping.Month
									}


		try:
			self.selecteddate = selecteddate
			self.dataselection = dataselection
			
			# the user can send arguments for the chart config and chart style, store these and remove them from kwargs
			tmpch_config = kwargs.pop('chart_config', None)
			if tmpch_config and type(tmpch_config)==dict:
				for attr, value in tmpch_config.items():
					if hasattr(self.chart_config, attr):
						setattr(self.chart_config, attr, value)
			
			tmpch_style = kwargs.pop('chart_style', None)
			if tmpch_style and type(tmpch_style)==dict:
				for attr, value in tmpch_style.items():
					if hasattr(self.chart_style, attr):
						setattr(self.chart_style, attr, value)
			# store the initial color scheme locally
			self.colors = self.chart_style.colors
			
			# A chart does NOT link to a single datapoint via the JSEM GUI inheritance
			super().__init__(parent, None, default_config, default_style, **kwargs)
			
			self.chartinfo = chartinfo
			
			# check if the chart belongs to a chart container, 
			self.parent_chartcont = None
			if self.parent is not None and type(self.parent)==JSEM_ChartCont: self.parent_chartcont = parent

			# convert the datapoints to charted_datapoints
			self.charted_datapoints = dict()
			for teller, dp in enumerate(datapoints):
				self.charted_datapoints[dp.name]={"visible": True, "datapoint": dp, "color": self.colors[teller], 'axis':None}
				
			# attach the handlers for the chart combine functionality (by click and drag)
			self.onmousedown.connect(self.chart_selected)
			self.ontouchstart.connect(self.chart_selected)
			self.onmouseup.connect(self.chart_dropped)
			self.ontouchend.connect(self.chart_dropped)

			# force an update and bring the chart alive....
			self.update()
			
		except Exception as err:
			Logger.exception(str(err))


	def set_content(self, chart):
		'''
			This method renders a PyGal Chart object into an SVG object that can be handled by Remi
		'''
		# Bij het renderen moet is_unicode op True worden gezet, anders zien we geen special characters (zoals degree signs etc.)
		self.data = chart.render(is_unicode=True)
		self.add_child("chart", self.data)


	def update(self, *args, **kwargs):
		# set waitcursor
		Common_Data.MAIN_CONTAINER.style["cursor"]="wait"
		
		if not kwargs.get('from_refresh', False):
			
			# Logger.info(f'Barchart update routine entered: dataselection:{self.dataselection}')
			# Logger.info(f'config:{self.config}')
			# Logger.info(f'style:{self.style}')
			
			# update subscriptions
			if self.dataselection in [DataSelection._Last50, DataSelection._10min, DataSelection._30min, DataSelection._1hr] or \
																			self.config['always_refresh']:
				# subscribe deze line chart bij alle charted datapoints
				for dpname in self.charted_datapoints:
					dp = self.charted_datapoints[dpname]["datapoint"]
					# if dp.ID == 214: Logger.info(f'{dp.name}-- subscription of barchart checked and updated')

					if not (self in dp.subscribed_widgets):
						dp.subscribed_widgets.append(self)
			else:
				# unsubscribe deze line_chart bij de datapoints die op de kaart staan. geen refresh nodig voor deze dataselection
				for dpname in self.charted_datapoints:
					dp = self.charted_datapoints[dpname]["datapoint"]
					if self in dp.subscribed_widgets:
						dp.subscribed_widgets.remove(self)

		# get the data
		dpIDs = [dpinfo['datapoint'].ID  for dpinfo in self.charted_datapoints.values()]
		datagrouping = self.allowed_dataselections[self.dataselection]
		aggregation = Aggregation[self.chartinfo['aggr']]
		# print('dataselection = %s, datagrouping = %s, aggregation = %s' % (self.dataselection, datagrouping, aggregation))
		# Waitkey()
		result_df = get_df_from_database(
										dpIDs=dpIDs,
										dataselection = self.dataselection,
										datagrouping = datagrouping,
										aggregation = aggregation,
										dataselection_date = self.selecteddate,
										maxrows = Max_Chart_Points
										)
										
										
		if result_df is None: return
		# Not existing timestamps will be filled with NaN values, replace those with 0 to avoid loosing the bars for these slots totally
		result_df = result_df.fillna(0)
		# print(result_df)
		
		# Figure our where NOW is in terms of the DatabaseGrouping definition
		if datagrouping == DatabaseGrouping.Hour:
			highlite_now = int(datetime.now().replace(minute=0, second=0).timestamp())
		elif datagrouping == DatabaseGrouping.Day:
			highlite_now = int(datetime.now().replace(hour=0, minute=0, second=0).timestamp())
		elif datagrouping == DatabaseGrouping.Month:
			highlite_now = int(datetime.now().replace(day=1, hour=0, minute=0, second=0).timestamp())
		else:
			highlite_now = None									# indicator for highligthinh the time NOW bar in the chart
		# print(f'highlite_now {highlite_now}')



		# initialize
		primary_axis = AxisScales()
		secondary_axis = AxisScales()
		prm_colors, sec_colors = [], []
		prm_title, sec_title = '', ''
		# Determine the axis and build the color lists for all visible datapoints, make non fitting datapoints invisible
		for dp_info in self.charted_datapoints.values():
			if not dp_info["visible"]: continue
			charted_dp = dp_info["datapoint"]
			# check if a secondary axis is needed....
			if primary_axis.scalefit(charted_dp,result_df[charted_dp.name].values): 
				dp_info['axis']=AxeSelection.primary
				prm_title = charted_dp.unit
				prm_colors += [dp_info['color']]
			elif secondary_axis.scalefit(charted_dp,result_df[charted_dp.name].values): 
				dp_info['axis']=AxeSelection.secondary
				sec_title = charted_dp.unit
				sec_colors += [dp_info['color']]
			else: 
				# cant display this item at this time, make hidden and redraw legends
				dp_info['axis']=AxeSelection.hidden
				dp_info["visible"] = False
				if self.parent_chartcont: self.parent_chartcont.fill_legendbox()
				continue
				
		self.chart_style.colors = prm_colors + sec_colors
				
		# Create a DateTimeLine chart
		self.chart = Bar(self.chart_config, style=self.chart_style, y_title=prm_title, y_title_secondary=sec_title)
		self.chart_style.value_colors = ['black' for x in self.charted_datapoints]
		
		# prepare the x-axis labels
		self.chart.x_labels = [datetime.fromtimestamp(x) for x in result_df["timestamp"].values]
		self.chart.x_value_formatter = lambda dt: dt.strftime(Best_dtFormat.get(self.dataselection, "%d-%m %H:%M"))
		
		
		
		# Build the chart
		for dp_info in self.charted_datapoints.values():
			if not dp_info["visible"]: continue
			charted_dp = dp_info["datapoint"]
			

			values = [{'value':x} for x in result_df[charted_dp.name].values]
			if self.config['highlight_now'] and highlite_now != None:
				# print(f'highlite_now {highlite_now}')
				# print(result_df)
				if highlite_now in result_df["timestamp"].values.tolist():
					# beter zou zijn om ipv een exacte match ook te kijken naar de dichtsbijzijnde of eerst mindere
					idx = result_df["timestamp"].values.tolist().index(highlite_now)
					values[idx]['color']='red'
					# if charted_dp.ID == 214: Logger.info(f'{charted_dp.name}-- timestamp {highlite_now} highlighted')
				
			# if charted_dp.ID == 214: Logger.info(f'{charted_dp.name}-- barchart updated')
				
			# -----add data to barchart, Voeg nu dit datapoint met zijn values toe aan de chart......
			self.chart.add	(
							charted_dp.name + " (" + str(charted_dp.unit) + ")", 
							values,
							secondary = (dp_info['axis'] == AxeSelection.secondary)
							)
		self.chart.value_formatter = lambda x: '%.1f' % x 
		self.set_content(self.chart)
		# back to normal cursor
		Common_Data.MAIN_CONTAINER.style["cursor"]="default"


	def refresh(self, *args, **kwargs):
		try:
			# A call to the refresh of the upper class is not necessary, there is NO value that needs updating
			# super().refresh(*args, **kwargs)
			self.update()

		except Exception as err:
			Logger.exception(str(err))
		
	def chart_selected(self, *args, **kwargs):
		if not self.config['allow_dragdrop']: return
		
		# print('chart selected')
		Common_Data.SELECTED_CHART = self
		Common_Data.SELECTED_DATAPOINTS = self.charted_datapoints

	def chart_dropped(self, *args, **kwargs):
		if not self.config['allow_dragdrop']: return
		
		# anything to drop? dropped in self????
		if not Common_Data.SELECTED_CHART or Common_Data.SELECTED_CHART is self: return

		# check of er dp's zijn die al in de chart staan, zo niet dan toevoegen
		for dpname in Common_Data.SELECTED_DATAPOINTS:
			if dpname in self.charted_datapoints: continue		# oeps it is....dont add twice
			else:
				# add datapoint info to this chart
				self.charted_datapoints[dpname] = Common_Data.SELECTED_DATAPOINTS[dpname]
				# assign the next available color
				nwcolor = self.colors[len(self.charted_datapoints) - 1] if len(self.colors) >= len(self.charted_datapoints) else 'black'
				self.charted_datapoints[dpname]['color'] = nwcolor
				# and add datapoint to the parent ChartCont, if there is one
				if self.parent_chartcont: self.parent_chartcont.datapoints.append(Common_Data.SELECTED_DATAPOINTS[dpname]['datapoint'])

		for dpname in self.charted_datapoints:
			dp = self.charted_datapoints[dpname]["datapoint"]
			# remove old subscriptions for the old chart
			if Common_Data.SELECTED_CHART in dp.subscribed_widgets:
				dp.subscribed_widgets.remove(Common_Data.SELECTED_CHART)
			# (re)subscribe deze line_chart bij de datapoints die op de kaart staan.
			if self not in dp.subscribed_widgets:
				dp.subscribed_widgets.append(self)
			# print('datapoint %s now has color %s' % (dpname, self.charted_datapoints[dpname]['color']))
				
		# ruim nu de oude chart op, 
		charts_parent = Common_Data.CHARTS_PARENT_CONTAINER
		this_chartcontainer = Common_Data.SELECTED_CHART.get_parent()
		charts_parent.remove_child(this_chartcontainer)

		Common_Data.SELECTED_CHART=None
		Common_Data.SELECTED_DATAPOINTS=None
		# re-generate the legendbox of the parent  chartcont
		if self.parent_chartcont: self.parent_chartcont.fill_legendbox()
		# re-present the chart
		self.update()







class JSEM_Stacked_Bar(gui.Svg):
	def __init__(self, parent=None, datapoints=[], *args, **kwargs):
		try:
			super().__init__(*args, **kwargs)
			self.css_position = "relative"
			self.datapoints = datapoints
			self.title = kwargs["title"] if "title" in kwargs else ""
			# Check optional parameters in kwargs
			if "tooltip" in kwargs: self.attributes["title"]=kwargs["tooltip"]
			
			self.bgcolor = kwargs.get("bgcolor", "transparent")
			
			self.parent = parent
			if self.parent is not None:
				self.key = self.parent.append(self)
			else:
				self.key=None
				
			# get font, top, left, width and height for the SVG container
			set_css_sizes(widget=self, *args, **kwargs)
			self.css_background_color = kwargs.get("bgcolor","transparent")
			self.css_color = kwargs.get("color","black")

			# definieer nu de config class voor de algemene chart setup en de Style voor de weergave
			self.custom_config = Config	(
										width = kwargs.get('chart_width', 500),
										height = kwargs.get('chart_height', 700),
										title = kwargs.get('chart_title',None),
										show_legend = kwargs.get('show_legend',True),
										legend_at_bottom=True,
										legend_at_bottom_columns=1,
										x_labels = ["Power"]
										)
			# # eventueel nog aan custom_config toevoegen: (explicit_size=True)
			# pygal.config.Config(explicit_size=True)
			
			self.custom_style = Style	(
										background=kwargs.get("bgcolor","transparent"),
										plot_background=kwargs.get("bgcolor","transparent"),
										colors = kwargs.get('chart_colors', ['red','green','yellow','blue','purple','black']),
										legend_font_size=20,
										label_font_size=20,
										major_label_font_size=20, 
										title_font_size=30
										)

									
			self.bar_chart = pygal.StackedBar(config=self.custom_config, style=self.custom_style)
					
			for dp in self.datapoints:
				dpname = (dp.name[:12] + '..') if len(dp.name) > 12 else dp.name
				self.bar_chart.add(str(dpname), [dp.value])					
				dp.subscribed_widgets.append(self)
				
			self.set_content(self.bar_chart)
			
		except Exception as err:
			Logger.exception(str(err))


	def set_content(self, chart):
		self.data = chart.render()
		self.add_child("chart", self.data)

	def refresh(self, *args, **kwargs):
		self.bar_chart = pygal.StackedBar(config=self.custom_config, style=self.custom_style)

		for dp in self.datapoints:
			dpname = (dp.name[:12] + '..') if len(dp.name) > 12 else dp.name
			self.bar_chart.add(str(dpname), [dp.value])
		
		self.set_content(self.bar_chart)


class JSEM_ChartCont(JSEM_GUI, VBox):
	def __init__(self, parent=None, datapoints=[], **kwargs):
		# define the default style and config
		default_config = dict(dp_signal_prop='', adopt_dp_signals=False, load_extra_datapoints=True, 
								show_title=True, show_controlbox=True, show_legendbox=True, show_value=False)
									
		chart_cont_style =  '''position:absolute;margin:0px;background-color:lightgrey;width:100%;border-style:none;align-items:center;'
							height:100%;width:100%;font-size:100%'''
							
				
		default_style = {
				'position':'absolute', 'margin':'0px', 'background-color':'lightgrey', 'width':'100%', 'border-style':'none', 'align-items':'center',
				'height':'100%', 'font-size':'100%'}

				# # 'title-font-size':"12px", 'title-color':"black", 'title-width':"100%", 'title-text-align':"left", 'title-position':"absolute",
				# # 'value-font-size':"12px", 'value-color':"black", 'value-width':"100%", 'value-text-align':"left", 'value-position':"absolute",
				#
				# 'ctrlbox-background-color':"transparent", 'ctrlbox-width':"100%", 'ctrlbox-height':"20px",
				# 'ctrlbox-align-items':"center", 'ctrlbox-justify-content':"space-between",
				#
				# 'ctrlbox-closebtn-background-color':"red", 'ctrlbox-closebtn-width':"auto",
				# 'ctrlbox-closebtn-height':"100%",
				#
				# 'ctrlbox-chsel-background-color':"white", 'ctrlbox-chsel-width':"auto",
				# 'ctrlbox-chsel-height':"100%",
				#
				# 'ctrlbox-aggsel-background-color':"white", 'ctrlbox-aggsel-width':"auto",
				# 'ctrlbox-aggsel-height':"100%",
				#
				# 'ctrlbox-datasel-background-color':"white", 'ctrlbox-datasel-width':"auto",
				# 'ctrlbox-datasel-height':"100%", 'ctrlbox-datasel-visibility':"visible",
				#
				# 'ctrlbox-datesel-background-color':"white", 'ctrlbox-datesel-width':"auto",
				# 'ctrlbox-datesel-height':"100%", 'ctrlbox-datesel-visibility':"visible",
				#
				#
				# 'lgndbox-background-color':"transparent", 'lgndbox-width':"100%", 'lgndbox-height':"20px",
				# 'lgndbox-align-items':"center", 'lgndbox-justify-content':"space-around", 'lgndbox-font-size':"80%",
				#
				# 'lgndbox-ckblabel-color':"black", 'lgndbox-ckblabel-background-color':"transparent",
				# 'lgndbox-ckblabel-width':"180px", 'lgndbox-ckblabel-height':"95%", 'lgndbox-ckblabel-accent-color':'blue'
				#
				# 		}

		if not datapoints: 
			Logger.error('No datapoint passed..Cant build a chart')
			return

		# A chartcontainer does NOT link to a single datapoint via the JSEM GUI inheritance
		super().__init__(parent, None, default_config, default_style, **kwargs)
		
		self.legendbox = None
		self.controlbox = None
		self.value_lbl = None
		self.title_lbl = None
		self.chart = None
		
		# Now go through all datapoints passed as argument and see if they import extra datapoints...
		if self.config['load_extra_datapoints']:
			extended_datapoints = []
			for dp in datapoints:
				extended_datapoints.append(dp)
				chinfo = dp.chartsinfo[0]
				# In the chart definitions EXTRA datapoints can be added
				for dpname in chinfo["joinwith"]: 
					if dpname.isdecimal() and int(dpname) in Common_Data.DATAPOINTS_ID:
						xtra_dp = Common_Data.DATAPOINTS_ID[int(dpname)]
					elif dpname in DATAPOINTS_NAME:
						xtra_dp = DATAPOINTS_NAME[dpname]
					else:
						Logger.error('No joinwith datapoint found for %s' % dpname)
						continue
					
					if xtra_dp not in extended_datapoints: 
						extended_datapoints.append(xtra_dp)
						
			self.datapoints = extended_datapoints
		else:
			self.datapoints = datapoints
			
		# start with the FIRST chartdefinition for the first datapoint
		self.chartinfo = self.datapoints[0].chartsinfo[0]
		# and build the chartcontainer based on the charttype of the passed datapoint
		self.chart_selection_changed(ctype=self.chartinfo['ctype'])
			
		


	def fill_legendbox(self):
		'''
		Fills a HBox container with the legends of all presented datapoints
		By checking or un-checking the legend that datapoint will be added or removed from the chart
		'''
		if self.legendbox is None:
			# Generate a HBox container for the legends of all presented datapoints, it will be filled later by the JSEM chart objects
			self.legendbox = HBox(style='background-color:transparent; width:100%; height:20px; align-items:center; '
										'justify-content:space-around; font-size:80%')
			self.append(self.legendbox)

		# always start with an empty legendbox
		self.legendbox.empty()
		
		# het meest zuivere is om de legends ook daadwerkelijk direct af te leiden uit de charted_datapoints van de chart
		for dp_info in self.chart.charted_datapoints.values():
			dp = dp_info['datapoint']
			dp_ck_label = CheckBoxLabel(label="%s (%s)" % (dp.name, dp.unit), checked=dp_info['visible'],
										style='color:black; background-color:transparent; width:180px; height:95%; accent-color:blue')
			# set the datapoint specific color for the legend
			dp_ck_label.css_color = dp_info['color']
			dp_ck_label._checkbox.style['accent-color'] = dp_info['color']		# alleen de _checkbox accent color lijkt te werken!!
			dp_ck_label.onchange.connect(self.legend_clicked, datapoint=dp)
			self.legendbox.append(dp_ck_label)

	def legend_clicked(self, *args, **kwargs):
		# The datapoint is passed as an kwargs argument
		dp = kwargs.get("datapoint", None)
		dp_info = self.chart.charted_datapoints[dp.name]
		dp_info["visible"] = bool(args[1])
		# force an update en breng de chart alive....
		self.chart.update()

	def fill_controlbox(self):
		'''
		Fills a HBox container with the controls for the chart
		'''

		# Generate a HBox container for the controls of the chart, dataselection, chartselection, dateselection and exit btn
		self.controlbox = HBox(style=   'background-color:transparent; width:100%; height:20px; align-items:center; '
										'justify-content:space-between')
		
		self.close_btn = Button(text="close", style='background-color:red; width:auto; height:100%')
		self.close_btn.onclick.connect(self.close)
		self.controlbox.append(self.close_btn)

		# chart selector.... if needed
		if len(self.datapoints[0].chartsinfo) > 1:
			# only the first datapoint gets to decide which charts are possible....
			# the user can change the chart_type, default we use the first chart defined for self.datapoint
			self.ch_sel = DropDown(style='background-color:white; width:auto; height:100%')
			# vul de dropdown met alle charttypes van het eerste connected datapoint
			self.ch_sel.append([x["ctype"] for x in self.datapoints[0].chartsinfo])
			# for x in self.datapoints[0].chartsinfo: self.ch_sel.append(x["ctype"])
			# selecteer de current chartmode in de dropdown
			self.ch_sel.select_by_value(self.chartinfo["ctype"])
			self.ch_sel.onchange.connect(self.chart_selection_changed)
			self.controlbox.append(self.ch_sel)
		

		if self.chartinfo['ctype'] in ['bar']:
			# aggregation is only possible in bar charts, it enables grouping data per timeslot and then aggregate the data
			# on multiple different aggregations... for instance: Mean, Median, Count, etc.
			self.agg_sel = DropDown(style='background-color:white; width:auto; height:100%')
			# populate the dropdown
			# for x in Aggregation: self.agg_sel.append(x.name)
			self.agg_sel.append([x.name for x in Aggregation])
			
			# select the current aggregation of the master datapoint in the dropdown
			self.agg_sel.select_by_value(self.chartinfo["aggr"])
			self.agg_sel.onchange.connect(self.aggr_selection_changed)
			self.controlbox.append(self.agg_sel)
		
		
		
		if self.chartinfo['ctype'] in ['line', 'bar', 'map']:
			# dropdown (dd) en datepicker (dp) en timepicker (tp) zijn widgets waarmee de gebruiker de chart begin en eind timestamp kan kiezen
			# if ctype in ['line', 'bar']:
			self.datasel = DropDown(style='background-color:white; width:auto; height:100%')
			# vul de dropdown met alle members van de allowed_dataselections
			# for x in self.chart.allowed_dataselections: self.datasel.append(x.name)
			self.datasel.append([x.name for x in self.chart.allowed_dataselections])
			# selecteer de default chartmode in de dropdown
			self.datasel.select_by_value(self.chart.dataselection.name)
			self.datasel.onchange.connect(self.dataselection_changed, chart=self)
			self.controlbox.append(self.datasel)
			
			self.datetime_box = Container(style='background-color:transparent; width:20%; height:100%')
			# self.datetime_box.style['position'] = 'relative'
			
			self.prev = Button('<', style='background-color:grey; position:absolute; left:0%; top:0%; width:10%; height:100%')
			self.prev.onclick.connect(self.prv_nxt_hndlr, increment=-1)
			
			self.datesel = Date(style='background-color:white; position:absolute; left:10%; top:0%; width:50%; height:100%')
			self.datesel.set_value(self.chart.selecteddate.strftime("%Y-%m-%d"))
			self.datesel.onchange.connect(self.date_changed)

			self.dpd_date_format = "%Y-%B"
			self.datedpd = DropDown(style='background-color:white; position:absolute; left:10%; top:0%; width:50%; height:100%; visibility:hidden')
			self.datedpd.onchange.connect(self.date_changed)
			
			self.next = Button('>', style='background-color:grey; position:absolute; left:60%; top:0%; width:10%; height:100%')
			self.next.onclick.connect(self.prv_nxt_hndlr, increment=1)
			
			self.timesel = DropDown(style='background-color:white; position:absolute; left:70%; top:0%; width:30%; height:100%')
			self.timesel.append('now')
			self.timesel.append([f'{i:02d}:{j:02d}' for i in range(24) for j in range(0, 60, 10)])
			self.timesel.set_value(self.chart.selecteddate.strftime("now"))
			self.timesel.onchange.connect(self.time_changed)
			
			self.datetime_box.append([self.prev, self.datesel, self.datedpd, self.next, self.timesel])
			self.controlbox.append(self.datetime_box)
			# In order to use position:absolute in the children of the datetime_box its position needs to be defined as relative or absolute
			# however, adding it to a Hbox or Vbox overwrites the position to static....so set the position AFTER adding it to a VBox or HBox
			self.datetime_box.style['position'] = 'relative'

			self.dataselection_changed(self.datasel, self.datasel.get_value())


	def close(self, *args, **kwargs):
		for dp in self.datapoints:
			# remove the datapoint subscriptions for this chart
			if self.chart in dp.subscribed_widgets:
				dp.subscribed_widgets.remove(self.chart)
		# and remove myself from the parent widget
		self.parent.remove_child(self)
		
		if len(self.parent.children.keys()) == 0:
			# this was the last chart...collapse the chart area
			expandcollapse(Common_Data.DATA_PARENT_CONTAINER, Common_Data.CHARTS_PARENT_CONTAINER)


	def chart_selection_changed(self, calling_widget=None, ctype=None, *args, **kwargs):
		
		if calling_widget:
			# we zijn hier terecht gekomen via een chart_selection dropdown list... er is dus nu al een chart
			# maar die wil de gebruiker wijzigen in een ander chart type... behoud dan de dataselection en de selected date
			dataselection = self.chart.dataselection
			selecteddate = self.chart.selecteddate
			# switch chart type, and load the correct chartinfo for the new type
			for cinfo in self.datapoints[0].chartsinfo:
				if cinfo["ctype"]==ctype:
					self.chartinfo = cinfo
					break
		else:
			# Nog Geen chart, gebruik de defaults
			dataselection = Default_ChartMode
			selecteddate = datetime.now()
		
		# Er kan nog een oude chart zijn, die moeten we eerst weghalen
		for dp in self.datapoints:
			# remove the datapoint subscriptions for this chart
			if self.chart and self.chart in dp.subscribed_widgets:
				dp.subscribed_widgets.remove(self.chart)
		# now remove everything from this chart container
		self.empty()
		self.legendbox = None
		self.controlbox = None
		self.value_lbl = None
		self.title_lbl = None
		self.chart = None
		
		# Generate the chart object, first create the style dict for the chart
		chart_style = {}
		# iterate over all entries in the style dict that startwith 'ctrlbox-'
		for prop in [x for x in self.style.keys() if x.startswith('chart-')]: 
			chart_style[prop[len('chart-'):]] = self.style[prop]
			
		

		if self.chartinfo['ctype'] == 'line': 
			self.chart = JSEM_Line_Chart(parent=self, datapoints=self.datapoints, chartinfo=self.chartinfo, height="92%",
											dataselection=dataselection, selecteddate=selecteddate)
		elif self.chartinfo['ctype'] == 'bar': 
			self.chart = JSEM_Bar_Chart(parent=self, datapoints=self.datapoints, chartinfo=self.chartinfo, height="92%",
											dataselection=dataselection, selecteddate=selecteddate)
		elif self.chartinfo['ctype'] == 'map': 
			self.chart = JSEM_Map_Chart(parent=self, datapoints=self.datapoints, chartinfo=self.chartinfo, height="80%",
											dataselection=dataselection, selecteddate=selecteddate)
		else:
			Logger.error("%s-- Can not create chart, illegal type: %s" % (self.refdp.name, self.chartinfo))
		# Because of the VBox add widgets in the correct order chart_cont VBox (or use the css-order property)
		self.append(self.chart)
		if self.config['show_legendbox']:
			self.fill_legendbox()
			self.append(self.legendbox)
		if self.config['show_controlbox']:
			self.fill_controlbox()
			self.append(self.controlbox)

	def aggr_selection_changed(self,widget, nwselection, **kwargs):
		if self.chart:
			# print ('nwselection %s ' % nwselection)
			self.chart.chartinfo['aggr'] = nwselection
			self.chart.update()

	def dataselection_changed(self, widget, nwselection, **kwargs):
		if self.chart: 
			self.chart.dataselection = DataSelection[nwselection]
			self.chart.update()
			
			if nwselection in [DataSelection.All.name, DataSelection._Last50.name]:
				self.datesel.style['visibility']='hidden'
				self.datedpd.style['visibility']='hidden'
				self.timesel.style['visibility']='hidden'
				self.prev.style['visibility'] = 'hidden'
				self.next.style['visibility'] = 'hidden'

			elif nwselection in [DataSelection.Day.name, DataSelection.Week.name]:
				self.datesel.style['visibility']=''
				self.datedpd.style['visibility']='hidden'
				self.timesel.style['visibility']='hidden'
				self.prev.style['visibility'] = ''
				self.next.style['visibility'] = ''
			
			elif nwselection == DataSelection.Month.name:
				self.dpd_date_format = "%Y-%B"
				self.set_dpd(self.chart.selecteddate)
				self.datesel.style['visibility']='hidden'
				self.datedpd.style['visibility']=''
				self.timesel.style['visibility']='hidden'
				self.prev.style['visibility'] = ''
				self.next.style['visibility'] = ''

			elif nwselection == DataSelection.Year.name:
				self.dpd_date_format = "%Y"
				self.set_dpd(self.chart.selecteddate)
				self.datesel.style['visibility']='hidden'
				self.datedpd.style['visibility']=''
				self.timesel.style['visibility']='hidden'
				self.prev.style['visibility'] = ''
				self.next.style['visibility'] = ''


			else:
				self.datesel.style['visibility']=''
				self.datedpd.style['visibility']='hidden'
				self.timesel.style['visibility']=''
				self.prev.style['visibility'] = ''
				self.next.style['visibility'] = ''

	
			
	
	def date_changed(self, widget, selection, **kwargs):
		if self.chart:
			nw_date = self.chart.selecteddate
			if type(widget) is Date:
				nw_date = datetime.strptime(selection, "%Y-%m-%d")
				# self.chart.selecteddate = self.chart.selecteddate.replace(year=nw_date.year, month=nw_date.month, day=nw_date.day)
			if type(widget) is DropDown:
				if self.chart.dataselection == DataSelection.Month:
					nw_date = datetime.strptime(f'{selection}-{self.chart.selecteddate.day}',
												"%Y-%B-%d")
				elif self.chart.dataselection == DataSelection.Year:
					nw_date = datetime.strptime(f'{selection}-{self.chart.selecteddate.month}-{self.chart.selecteddate.day}',
												"%Y-%m-%d")

			self.chart.selecteddate = nw_date
			self.set_dpd(self.chart.selecteddate)
			self.chart.update()
	
	def prv_nxt_hndlr(self, widget, increment=0, **kwargs):
		if self.chart:
			delta_arg = {'days':0}
			if self.chart.dataselection == DataSelection._Last50: return
			elif self.chart.dataselection == DataSelection.Day: delta_arg = {'days':increment}
			elif self.chart.dataselection == DataSelection.Week: delta_arg = {'weeks':increment}
			elif self.chart.dataselection == DataSelection.Month: delta_arg = {'months':increment}
			elif self.chart.dataselection == DataSelection.Year: delta_arg = {'years':increment}
			elif self.chart.dataselection.name.startswith('_'): delta_arg = {'seconds':increment * (self.chart.dataselection.value / 4)}
			nw_date = (self.chart.selecteddate + relativedelta(**delta_arg))
			nw_date = datetime(nw_date.year, nw_date.month, nw_date.day, nw_date.hour,
							   nw_date.minute - (nw_date.minute % 10))				# round down to 10 minutes
			
			self.chart.selecteddate = nw_date
			self.datesel.set_value(nw_date.strftime("%Y-%m-%d"))
			self.set_dpd(self.chart.selecteddate)
			self.timesel.set_value(nw_date.strftime('%H:%M'))
			self.chart.update()

	
	def time_changed(self, widget, nwtime, **kwargs):
		if self.chart: 
			if nwtime == 'now':
				nw_hour = datetime.now().hour
				nw_minute = datetime.now().minute
				nw_second = datetime.now().second
			else:
				nw_hour = int(nwtime.split(':')[0])
				nw_minute = int(nwtime.split(':')[1])
				nw_second = 0
			self.chart.selecteddate = self.chart.selecteddate.replace(hour=nw_hour, minute=nw_minute, second=nw_second, microsecond=0)
			self.chart.update()
	
	def set_dpd(self, nw_date):
		# rebuilds the dropdown lists and selects the active value
		self.datedpd.empty()
		dd_list = []
		if self.chart.dataselection == DataSelection.Month:
			for teller in range(-6, 7, 1):
				dd_date = self.chart.selecteddate + relativedelta(months=teller)
				dd_list += [f'{dd_date.strftime(self.dpd_date_format)}']
		elif self.chart.dataselection == DataSelection.Year:
			for teller in range(-2, 3, 1):
				dd_date = self.chart.selecteddate + relativedelta(years=teller)
				dd_list += [f'{dd_date.strftime(self.dpd_date_format)}']
		self.datedpd.append(dd_list)
		self.datedpd.set_value(nw_date.strftime(self.dpd_date_format))


class JSEM_Label(JSEM_GUI, HBox):
	'''
	JSEM label is a specific JSEM widget. It connects to a datapoint and can be updated by that datapoint via a subscription
	it has a number of sub-labels placed into a HBox (Remi), the format of these sublabels can be controlled via the style argument wich updates
	the default style definition of the JSEM label. Also named arguments (kwargs) can be used to control specific style parameters 
	of the HBox and all sublabels
	Upon initialization it connects to a datapoint by subscribing itself to the datapoint and it copies its conditional 
	formatting (if config[adopt_dp_signals] is set). Apart from the conditional formatting dictated by a datapoint, several conditional formatting
	rules can be specified in the cond_format argument.
	The (mandatory) refresh method is implemented thru the inheritance from the JSEM_GUI parent
	When doubleclicking the NAME sublabel the linked datapoint will be relaoded from the database by calling the reload method of the datapoint 
	(only in config[reload_ondblclick] is set)
	When clicking on the VALUE sublabel the chart will be launched (only if the connected datapoint has a chart_def field with the chart info)
	'''
	def __init__(self, parent=None, datapoint=None, **kwargs):
		
		# define the default style and config
		default_config = dict(dp_signal_prop='value-background-color', adopt_dp_signals=True, reload_ondblclick=True,
								show_name=True, show_subcat=True, show_value=True, show_unit=True, enable_RW=True,
								show_tooltip=True, unit='')
									
		default_style = {
			'position':'absolute', 'margin':'0px', 'background-color':'transparent', 'border-style':'none', 'font-size':'14px',
			'width':'100px', 'height':'auto', 'justify-content':'flex-start',
			
			'name-white-space':'nowrap', 'name-overflow':'clip', 'name-font-size':'1.0em', 'name-color':"black", 'name-height':"auto", 'name-width':"40%", 'name-text-align':"left", 'name-background-color':'transparent', 'name-cursor':'default', 
			'subcat-white-space':'nowrap', 'subcat-overflow':'clip', 'subcat-font-size':'0.75em', 'subcat-color':"black", 'subcat-height':"auto", 'subcat-width':'22%', 'subcat-text-align':"left", 'subcat-background-color':'transparent', 'subcat-cursor':'default',
			'txt-white-space':'nowrap', 'txt-overflow':'clip', 'txt-font-size':'1.0em', 'txt-color':"black", 'txt-height':"auto", 'txt-width':'auto', 'txt-text-align':"left", 'txt-background-color':'transparent', 'txt-cursor':'default',
			'value-white-space':'nowrap', 'value-overflow':'clip', 'value-font-size':'1.0em', 'value-color':"black", 'value-height':"auto", 'value-width':'18%', 'value-text-align':"left", 'value-background-color':'transparent', 'value-cursor':'default',
			'unit-white-space':'nowrap', 'unit-overflow':'clip', 'unit-font-size':'0.75em', 'unit-color':"black", 'unit-height':"auto", 'unit-width':'8%', 'unit-text-align':"left", 'unit-background-color':'transparent', 'unit-cursor':'default',
			'ckbox-transform':'scale(0.8)', 'ckbox-cursor':'pointer', 'ckbox-accent-color':'blue', 'ckbox-height':"2cqh", 'ckbox-width':"2cqh", 
			'input-border-style':'solid', 'input-border-width':'1px', 'input-border-color':'grey', 'input-font-size':'1.0em', 'input-color':"black", 'input-height':"1.15em", 'input-width':'12%', 'input-text-align':"left",'input-background-color':'white', 'input-cursor':'text'
						}





						
		super().__init__(parent, datapoint, default_config, default_style, **kwargs)
		
		# with container-type this container is set as the resizing parent for the resizing of fonts that use container queries (cqw or cqh)
		self.style['container-type'] = 'inline-size'
		# For whatever reason 'size' causes Firefox browser to stop working
		# self.style['container-type'] = 'size'

		self.chart_cont = None
		
		self.name_lbl = None
		self.sc_lbl = None
		self.txt_lbl = None
		self.value_lbl = None
		self.unit_lbl = None
		self.ckbox_lbl = None
		self.input_lbl = None
		
		if self.datapoint:
			dp = self.datapoint
			
			if self.config['show_name']:
				self.name_lbl = Label(dp.name)
				# iterate over all entries in the style dict that startwith 'name-'
				for prop in [x for x in self.style.keys() if x.startswith('name-')]: 
					self.name_lbl.style[prop[len('name-'):]] = self.style[prop]
				# When double clicking the name label should the datapoint be reloaded from the database?
				if self.config['reload_ondblclick']: self.name_lbl.ondblclick.connect(dp.reload)
				if self.config['show_tooltip']: self.name_lbl.attributes["title"]=f'{dp.ID}--{dp.descr}'
				self.append(self.name_lbl)
			
			if self.config['show_subcat']:
				self.sc_lbl = Label(dp.sub_cat)
				# iterate over all entries in the style dict that startwith 'subcat-'
				for prop in [x for x in self.style.keys() if x.startswith('subcat-')]: 
					self.sc_lbl.style[prop[len('subcat-'):]] = self.style[prop]
				self.append(self.sc_lbl)
	
			if kwargs.get('text', None):
				# Text was passed as argument, and a datapoinit was linked....this can be used to replace the name and sub_cat for more friendly display
				self.txt_lbl = Label(kwargs['text'])
				# iterate over all entries in the style dict that startwith 'txt-'
				for prop in [x for x in self.style.keys() if x.startswith('txt-')]: 
					self.txt_lbl.style[prop[len('txt-'):]] = self.style[prop]
				self.append(self.txt_lbl)

			if self.config['show_value']:
				self.value_lbl = Label(str(self.value))
				# iterate over all entries in the style dict that startwith 'value-'
				for prop in [x for x in self.style.keys() if x.startswith('value-')]: 
					self.value_lbl.style[prop[len('value-'):]] = self.style[prop]
				# connect the handler for starting the charts via click
				if dp.enabled and dp.chart_type: 
					self.value_lbl.onclick.connect(self.on_datapoint_clicked)
					self.value_lbl.style['cursor']='pointer'
				self.append(self.value_lbl)
				
				if self.config['show_unit']:
					self.unit_lbl = Label(dp.unit)
					# iterate over all entries in the style dict that startwith 'unit-'
					for prop in [x for x in self.style.keys() if x.startswith('unit-')]: 
						self.unit_lbl.style[prop[len('unit-'):]] = self.style[prop]
					self.append(self.unit_lbl)
	
			if self.config['enable_RW'] and dp.enabled and dp.read_write.upper() == "RW":
				if dp.unit.lower()=='onoff':
					# Checkbox needed, los van een input widget is een checkbox ook een GUI widget
					self.ckbox_lbl = CheckBox(checked=(dp.value==1))
					# iterate over all entries in the style dict that startwith 'ckbox-'
					for prop in [x for x in self.style.keys() if x.startswith('ckbox-')]: 
						self.ckbox_lbl.style[prop[len('ckbox-'):]] = self.style[prop]
					self.ckbox_lbl.onchange.connect(dp.write_GUI_value)
					# self.ckbox_lbl.set_value(dp.value==1)
					self.append(self.ckbox_lbl)
				else:
					self.input_lbl = TextInput(single_line=True)
					# self.input_lbl.set_text(' ')
					# iterate over all entries in the style dict that startwith 'input-'
					for prop in [x for x in self.style.keys() if x.startswith('input-')]: 
						self.input_lbl.style[prop[len('input-'):]] = self.style[prop]
					self.input_lbl.onchange.connect(dp.write_GUI_value)
					self.append(self.input_lbl)

		else:
			# Geen datapoint meegegeven, gewoon een text label
			if kwargs.get('text', None):
				# Text was passed as argument, and no datapoinit was linked....so just a text label
				self.txt_lbl = Label(kwargs['text'])
				# iterate over all entries in the style dict that startwith 'txt-'
				for prop in [x for x in self.style.keys() if x.startswith('txt-')]: 
					self.txt_lbl.style[prop[len('txt-'):]] = self.style[prop]
				self.append(self.txt_lbl)
		
		self.update()
		
	def refresh (self, *args, **kwargs):
		super().refresh(*args, **kwargs)
		self.update()

	def update(self):
		# First check if there is a conditional format instruction for this widget
		# an example of a conditional format instruction is: dict(cond="gt", check_value=0.0, prop="color", true="green", false="darkgrey")
		if self.cond_format:
			# now walk through all defined conditional formats, and adjust the widget attributes and style accordingly
			for cf in self.cond_format:
				prop = cf.get('prop', self.config['dp_signal_prop'])
				prop_nwvalue = None
				cond_check, prop_nwvalue = super().check_condition(cf)
				# do we have a new value for the property?
				if prop_nwvalue:
					if prop.startswith('name-') and self.name_lbl: self.name_lbl.style[prop[len('name-'):]] = prop_nwvalue
					if prop.startswith('subcat-') and self.subcat_lbl: self.subcat_lbl.style[prop[len('subcat-'):]] = prop_nwvalue
					if prop.startswith('txt-') and self.txt_lbl: self.txt_lbl.style[prop[len('txt-'):]] = prop_nwvalue
					if prop.startswith('value-') and self.value_lbl: self.value_lbl.style[prop[len('value-'):]] = prop_nwvalue
					if prop.startswith('unit-') and self.unit_lbl: self.unit_lbl.style[prop[len('unit-'):]] = prop_nwvalue
					if prop.startswith('ckbox-') and self.ckbox_lbl: self.ckbox_lbl.style[prop[len('ckbox-'):]] = prop_nwvalue
					if prop.startswith('input-') and self.input_lbl: self.input_lbl.style[prop[len('input-'):]] = prop_nwvalue
					else: self.style[prop] = prop_nwvalue
						
				# now check if we need to continue with the next conditional format
				if 'qit' in cf:
					if cf['qit'] and cond_check: break
		
		# Widget specific update logic.....
		if self.value_lbl:
			# print(f'Label text updated with {self.value}') 
			self.value_lbl.set_text(str(self.value)) 


		
	def on_datapoint_clicked(self, *args, **kwargs):
		# print('JSEM_Label.on_datapoint_clicked')
		# check if a chart can be displayed for this datapoint, during loading of the datapoint
		# all chartinfo is loaded into the chartsinfo property, which is al list of chartinfo's
		if not self.datapoint.chartsinfo: return

		Common_Data.MAIN_CONTAINER.style["cursor"]="wait"

		charts_parent = Common_Data.CHARTS_PARENT_CONTAINER
		data_parent = Common_Data.DATA_PARENT_CONTAINER
		main_cont = Common_Data.MAIN_CONTAINER
		# check if this JSEM label already has an chart running, if so...close it
		if self.chart_cont:
			self.chart_cont.close()
			
		self.chart_cont = JSEM_ChartCont(charts_parent, [self.datapoint], show_controlbox=True, show_legendbox=True, width='100%')

		Common_Data.MAIN_CONTAINER.style["cursor"]="default"
		return

def perc_to_px(widget, perc, direction='width'):
	try:
		parent = widget.get_parent()
		# print(parent)
		# print(parent.style)
		if not parent: raise Exception ('Reached the top of the heap without finding any dimension definition')
		if '%' in parent.style[direction]:
			# print('one more up')
			perc = perc * (float(parent.style[direction].replace('%', ''))/100.0)
			return perc_to_px(parent, perc)
		else:
			# print('hebbes')
			return int(perc * float(parent.style[direction].replace('px','')))
	except Exception as err:
		print(f'Error: {err}')

class JSEM_MultiArrow(JSEM_GUI, Svg):
	def __init__(self, parent=None, datapoint=None, **kwargs):
		import re
	
		# # define the default style and config
		default_config = dict(dp_signal_prop='line-stroke', adopt_dp_signals=False, orientation="horizontal", arrow="end")
		default_style = 	{
							'position':'absolute', 'margin':'0px', 
							'border-style':'solid', 'border-width':'0px', 'border-color':'transparent', 'border-radius':'0px',
							'background-color':'transparent', 'line-stroke':"black", 'line-stroke-width':'1', 'line-fill':'green'
							}

		arrow1 = kwargs.pop('arrow1', {})
		ap1 = arrow1.get('ap',0)
		sw1 = arrow1.get('sw',50)
		aw1 = arrow1.get('aw',100)
		al1 = arrow1.get('al',35)
		sl1 = arrow1.get('sl',65)
		# check valid args
		sw1 = max(sw1,0)
		sl1 = max(sl1,0)
		aw1 = max(aw1, sw1)
		al1 = max(al1,0)
		ap1 = max(sw1/2, aw1/2, ap1)
		# calc extra dimensions
		tl1 = sl1+al1			# total length arrow 1
		tw1 = aw1				# total width arrow 1
		as1 = (aw1-sw1)/2		# arrow-stick overhang arrow1

		drw_width = tl1
		drw_height = ap1 + int(tw1/2)
		
		arrow2 = kwargs.pop('arrow2', None)
		if arrow2:
			ap2=arrow2.get('ap', 0)				# x coord arrow point 2
			sw2=arrow2.get('sw', 20)				# stick width arrow 2
			aw2=arrow2.get('aw', 40)				# arrow width arrow 2
			al2=arrow2.get('al', 35)				# arrow length arrow 2
			sl2=arrow2.get('sl', 50)				# stick length arrow 2
			# check valid args
			sw2 = max(sw2,0)
			sl2 = max(sl2,0)
			aw2 = max(aw2, sw2)
			al2 = max(al2,0)
			ap2 = min(ap2, sl1-0.5*sw2)
			ap2 = max(ap2, 0.5*aw2)
			# calc extra dimensions
			tl2=sl2+al2								# total length arrow 2
			tw2=aw2									# total width arrow 2
			as2=(aw2-sw2)/2							# arrow-stick overhang arrow2
		
			drw_width = max(drw_width, ap2 + 0.5*tw2)
			drw_height = max(drw_height, drw_height-as1+tl2)
	
		super().__init__(parent, datapoint, default_config, default_style, **kwargs)

		# print (self.style)


		self.svgpolyline = SvgPolygon()
		
		
		if self.style.get('rotate', None): 	rotate = int(self.style.pop('rotate').replace('degr', ''))
		else:								rotate=0
			
		if self.style.get('flip', None): 	flips = self.style.pop('flip')
		else:								flips = 'none'

		# Regex pattern splits on substrings ";" and "," and " "
		flips = re.split(';|,| ', flips)
		transform = ''
		for flip in flips:
			if flip.strip().lower()=='vertical':
				transform += f'translate({0} {drw_height}), scale(1 -1) '
			elif flip.strip().lower()=='horizontal':
				transform += f'translate({drw_width} {0}), scale(-1 1) '
		
		# print(f'Transform after flips: {transform}')
			
		if rotate==90:
			transform += f'translate({drw_height} {0}), rotate(90) '
			view_width = drw_height
			view_height = drw_width
		elif rotate==180:
			transform += f'translate({drw_width} {drw_height}), rotate(180) '
			view_width = drw_width
			view_height = drw_height
		elif rotate==270:
			transform += f'translate({0} {drw_width}), rotate(270) '
			view_width = drw_height
			view_height = drw_width
		else:
			view_width = drw_width
			view_height = drw_height
			
		# print(f'Transform after rotate: {transform}')
			
		self.style['line-transform'] = transform
		
		
		# The following code is to translate the line_stroke_width to actual pixels, we need this to correct the viewbox later on
		svgsize_px = perc_to_px(self, float(self.style['width'].replace('%', ''))/100.0, 'width')
		# print(f'svgsize_px = {svgsize_px}')
		
		lw = int(self.style["line-stroke-width"].replace('px','').replace('%',''))
		# print(f'line-stroke-width was = {lw} percent')
		
		lw_px = int(float(lw/100.0) * svgsize_px)
		# print(f'This translates to {lw_px} pixels')
		self.style['line-stroke-width'] = f'{lw_px}px'
		
		# coord = [	(0, as1), (sl1, as1), (sl1, 0), (tl1, tw1/2),
					# (sl1, tw1), (sl1, tw1-as1), (0, tw1-as1)]

		coord = [	(0, ap1-0.5*sw1), (sl1, ap1-0.5*sw1), (sl1, ap1-0.5*aw1), (tl1,ap1),
					(sl1, ap1+0.5*aw1), (sl1, ap1+0.5*sw1), (0, ap1+0.5*sw1)]

		if arrow2:
			coord = coord[:-1] + \
					[(ap2+0.5*sw2, ap1+0.5*sw1), (ap2+0.5*sw2, ap1+0.5*sw1+sl2), (ap2+0.5*aw2, ap1+0.5*sw1+sl2), (ap2, ap1+0.5*sw1+tl2), (ap2-0.5*aw2, ap1+0.5*sw1+sl2),
					(ap2-0.5*sw2, ap1+0.5*sw1+sl2), (ap2-0.5*sw2, ap1+0.5*sw1), (0, ap1+0.5*sw1)]
					
		# correct for the line_stroke_width, make sure all is in sight...
		transform = f'translate ({lw} {lw}) ' + transform
		# print(f'Transform after line_stroke_width correction: {transform}')
		
		self.style['line-transform'] = transform

		# een viewbox is a sort of window that looks at a part of the svg container. By defining a viewbox window of 100 x 100
		# and specifying all svglines and svgpolylines in 0-100 coordinates within that window 
		# the viewbox will automatically scale the content with the svgwidget......
		self.attributes['viewBox'] = f"{0} {0} {view_width+2*lw} {view_height+2*lw}"
		# self.attributes['preserveAspectRatio'] = "xMidYMid meet"
		self.attributes['preserveAspectRatio'] = "none"

		# iterate over all entries in the xtra_style dict that startwith 'line_' and copy them to the svgpolyline attributes
		for prop in [x for x in self.style.keys() if x.startswith('line-')]: 
			self.svgpolyline.attributes[prop[len('line-'):]] = self.style[prop]
		
		# draw the arrow
		# print(self.svgpolyline.attributes['stroke-width'])
		
		for x,y in coord:
			self.svgpolyline.add_coord(x,y)
		self.append(self.svgpolyline)
		
		self.update()
		

	def refresh (self, *args, **kwargs):
		super().refresh(*args, **kwargs)
		self.update()

	def update(self, **kwargs):
		# First check if there is a conditional format instruction for this widget
		# an example of a conditional format instruction is: dict(cond="gt", check_value=0.0, prop="color", true="green", false="darkgrey")
		if self.cond_format:
			# now walk through all defined conditional formats, and adjust the widget attributes and style accordingly
			for cf in self.cond_format:
				prop = cf.get('prop', self.config['dp_signal_prop'])
				if not prop: continue
				prop_nwvalue = None
				cond_check, prop_nwvalue = super().check_condition(cf)
				# do we have a new value for the property?
				if prop_nwvalue:
					# there is a difference between a change in the style of the mother container (css) or a change in the xtra_style
					if prop.startswith('line-') and self.svgpolyline: 
						self.svgpolyline.attributes[prop[len('line-'):]] = prop_nwvalue
					else: self.style[prop] = prop_nwvalue
					
				# now check if we need to continue with the next conditional format
				if 'qit' in cf:
					if cf['qit'] and cond_check: break

		# Widget specific update logic.....
		# None for this widget


class JSEM_WeatherIcon(JSEM_GUI, Container):
	def __init__(self, parent=None, datapoint=None, **kwargs):
		
		# # define the default style and config
		default_config = dict(adopt_dp_signals=False, lookahead=10, interval=1, svg_images=False, image_source='')
		default_style = 	{
							'background-color':'transparent', 'position':'absolute', 'margin':'0px', 
							'border-style':'solid', 'border-width':'0px', 'border-color':'transparent', 'border-radius':'0px',
							}
		
		super().__init__(parent, datapoint, default_config, default_style, **kwargs)

		self.start_dt = datetime.now().replace(minute=0, second=0, microsecond=0)
		self.end_dt = self.start_dt + relativedelta(hours=(self.config['lookahead'] * self.config['interval']))

		icon_width= int(100/self.config['lookahead'])
		self.lbl_list=[]
		self.img_list=[]
		self.tmp_list=[]
		
		self.legend = Label(style=f'top:0%; left:0%; width:100%; height:20%; font-size:0.7em; position:absolute')
		self.append(self.legend)
		for img_nr in range(self.config['lookahead']):
			if self.config['svg_images']:
				img = Svg(style=f'top:20%; left:{icon_width * img_nr}%; width:{icon_width}%; height:50%; position:absolute')
			else:
				img = Image(style=f'top:20%; left:{icon_width * img_nr}%; width:{icon_width}%; height:50%; position:absolute')
				
			lbl = Label(style=f'top:75%; left:{icon_width * img_nr}%; width:{icon_width}%; height:25%; font-size:0.7em; '
								'position:absolute')
			tmp = Label(style=f'top:35%; left:{icon_width * img_nr}%; width:{icon_width}%; height:25%; font-size:0.7em; '
								'position:absolute; text-align:center')
			self.append([img,lbl,tmp])
			self.lbl_list.append(lbl)
			self.img_list.append(img)
			self.tmp_list.append(tmp)
			
		self.update()
		

	def refresh (self, *args, **kwargs):
		super().refresh(*args, **kwargs)
		self.update()

	def update(self, **kwargs):
		# First check if there is a conditional format instruction for this widget
		# an example of a conditional format instruction is: dict(cond="gt", check_value=0.0, prop="color", true="green", false="darkgrey")
		if self.cond_format:
			# now walk through all defined conditional formats, and adjust the widget attributes and style accordingly
			for cf in self.cond_format:
				prop = cf.get('prop', self.config['dp_signal_prop'])
				if not prop: continue
				prop_nwvalue = None
				cond_check, prop_nwvalue = super().check_condition(cf)
				# do we have a new value for the property?
				if prop_nwvalue:
					# there is a difference between a change in the style of the mother container (css) or a change in the xtra_style
					if prop.startswith('line-') and self.svgpolyline: 
						self.svgpolyline.attributes[prop[len('line-'):]] = prop_nwvalue
					else: self.style[prop] = prop_nwvalue
					
				# now check if we need to continue with the next conditional format
				if 'qit' in cf:
					if cf['qit'] and cond_check: break

		# Widget specific update logic.....load the image the corresponds to the datapoint value

		
		frcst = get_df_from_database(dpIDs=[frcst_temp, frcst_icoon], 
									datagrouping=DatabaseGrouping.Hour, 
									aggregation=Aggregation.Not,
									selected_startdate=self.start_dt, 
									selected_enddate=self.end_dt)
									
		# now only keep every 'interval'th row...
		# print(frcst)

		frcst = frcst.iloc[::self.config['interval'], :]
		
		# print(frcst)
		self.legend.set_text(f'{self.start_dt.strftime("%A %d %B")}')
		if not self.config['svg_images']:
			for teller, img in enumerate(self.img_list):
				value = frcst.iloc[teller]['frcst_icoon']
				dt = datetime.fromtimestamp(frcst.iloc[teller]['timestamp'])
				self.lbl_list[teller].set_text(dt.strftime('%H:%M'))
				deg = u'\N{DEGREE SIGN}'
				self.tmp_list[teller].set_text(f'{frcst.iloc[teller]["frcst_temp"]}{deg}')
				img.attr_src = Load_Images(f'{self.config["image_source"]}/{value}')
				
		else:
			# TODO: load svg file....
			pass
		
		# Logger.info(f'Updated WeatherIcon, datapoint value = {self.datapoint.value}, timestamp={datetime.fromtimestamp(self.datapoint._value_timestamp)}')



class JSEM_Arrow(JSEM_GUI, Svg):
	def __init__(self, parent=None, datapoint=None, **kwargs):

		# # define the default style and config
		default_config = dict(dp_signal_prop='line-stroke', adopt_dp_signals=False, orientation="horizontal", arrow="end")
		default_style = 	{
							'position':'absolute', 'margin':'0px', 
							'border-style':'solid', 'border-width':'0px', 'border-color':'transparent', 'border-radius':'0px',
							'background-color':'transparent', 'line-stroke':"black", 'line-stroke-width':'40%', 
							'arrow-ratio':'50%'
							}
			
		# # Om top, left height en width gewoon als getal op te kunnen geven worden deze als args binnengehaald en geconverteerd
		# for attr_name in ['height', 'width', 'top', 'left']:
			# attr = kwargs.get(attr_name,'50%')
			# if type(attr) == str:	kwargs[attr_name] = attr
			# else:					kwargs[attr_name] = "%spx" % attr
		# # print('nw kwargs %s' % kwargs)

		super().__init__(parent, datapoint, default_config, default_style, **kwargs)
		# For whatever reason the normal top, left etc kwargs are not send to the super SVG widget...
		# self.style.update({'top':kwargs.get('top', '0%'), 'left':kwargs.get('left', '0%'), 'height':kwargs.get('height', '0%'), 'width':kwargs.get('width', '0%')})
		self.css_top = kwargs.get('top', '0%')
		self.css_left = kwargs.get('left', '0%')
		self.css_height = kwargs.get('height', '0%')
		self.css_width = kwargs.get('width', '0%')
		self.css_position = 'absolute'
		# self.css_background_color = 'yellow'
		# print(self.style)

		# een viewbox is a sort of window that looks at a part of the svg container. By defining a viewbox window of 100 x 100
		# and specifying all svglines and svgpolylines in 0-100 coordinates within that window 
		# the viewbox will automatically scale the content with the svgwidget......
		self.attributes['viewBox'] = "%s %s %s %s" % (0,0, 100, 100)
		self.attributes['preserveAspectRatio'] = 'none'

		self.svgline = None
		self.svgpolyline = None
		
		# Completely draw the arrow within the container
		if self.config['arrow']=="none":
			arrwidth = 0
		else:
			arrwidth = int(self.style['arrow-ratio'].replace('px','').replace('%',''))
			
		stroke_width = int(self.style['line-stroke-width'].replace('px','').replace('%',''))
		color = self.style['line-stroke']
		arrow = self.config['arrow']
		orientation = self.config['orientation']
		
		if orientation == 'horizontal':
			if arrow=="end":
				self.svgline = SvgLine(0, 50, 100-arrwidth, 50)
				arrow_coord = [(100 - arrwidth, 0), (100, 50), (100 - arrwidth, 100)]
				
			else:	# arrow=="begin"
				self.svgline = SvgLine(arrwidth, 50, 100, 50)
				arrow_coord = [(arrwidth,0), (0,50), (arrwidth, 100)]

		else:	# orientation == 'vertical':
			if arrow=="end":
				self.svgline = SvgLine(50, 0, 50, 100-arrwidth)
				arrow_coord = [(0,100-arrwidth), (50,100), (100,100-arrwidth)]
			else:	# arrow=="begin"
				self.svgline = SvgLine(50, arrwidth, 50, 100)
				arrow_coord = [(0,arrwidth), (50,0), (100, arrwidth)]
		
		# iterate over all entries in the xtra_style dict that startwith 'line_' and copy them to the svgline attributes
		for prop in [x for x in self.style.keys() if x.startswith('line-')]: 
			self.svgline.attributes[prop[len('line-'):]] = self.style[prop]
		
		self.append(self.svgline)
		
		if arrwidth != 0: 
			# draw the arrowhead
			self.svgpolyline = SvgPolyline()
			self.svgpolyline.attributes['stroke-width'] = '1px'
			self.svgpolyline.attributes['stroke'] = self.svgline.attributes['stroke']
			self.svgpolyline.attributes['fill'] = self.svgline.attributes['stroke']
			for x,y in arrow_coord:
				self.svgpolyline.add_coord(x,y)
			self.append(self.svgpolyline)
		
		self.update()
		

	def refresh (self, *args, **kwargs):
		super().refresh(*args, **kwargs)
		self.update()

	def update(self, **kwargs):
		# First check if there is a conditional format instruction for this widget
		# an example of a conditional format instruction is: dict(cond="gt", check_value=0.0, prop="color", true="green", false="darkgrey")
		if self.cond_format:
			# now walk through all defined conditional formats, and adjust the widget attributes and style accordingly
			for cf in self.cond_format:
				prop = cf.get('prop', self.config['dp_signal_prop'])
				if not prop: continue
				prop_nwvalue = None
				cond_check, prop_nwvalue = super().check_condition(cf)
				# do we have a new value for the property?
				if prop_nwvalue:
					# there is a difference between a change in the style of the mother container (css) or a change in the xtra_style
					if prop.startswith('line-') and self.svgline: 
						self.svgline.attributes[prop[len('line-'):]] = prop_nwvalue
						if self.svgpolyline:
							self.svgpolyline.attributes['stroke'] = self.svgline.attributes['stroke']
							self.svgpolyline.attributes['fill'] = self.svgline.attributes['stroke']
					else: self.style[prop] = prop_nwvalue
					
				# now check if we need to continue with the next conditional format
				if 'qit' in cf:
					if cf['qit'] and cond_check: break

		# Widget specific update logic.....
		# None for this widget


		
class JSEM_Buffer(JSEM_GUI, Container):
	
	def __init__(self, parent=None, datapoint=None, value=0.0, **kwargs):
	# def __init__(self, parent=None, datapoint=None, top=100, left=100, width=70, height=300, value=None, text='', **kwargs):
		# define the default style and config
		default_config = dict(dp_signal_prop='fill-background-color', adopt_dp_signals=False, 
								max_value=100, min_value=0, show_minmax=False, show_value=True, show_unit=True, unit='')
									
		default_style = {
				'position':'absolute', 'margin':'0px', 'background-color':'white', 
				'border-style':'solid', 'border-width':'2px', 'border-color':'black', 'border-radius':'0px',
				'fill-background-color':"grey", 'fill-position':"absolute", 'fill-width':"100%",
				'value-font-size':"8cqh", 'value-color':"black", 'value-width':"100%", 'value-text-align':"left", 'value-position':"absolute",
				'minlbl-font-size':"3cqh", 'minlbl-color':"black", 'minlbl-width':"100%", 'minlbl-text-align':"right", 'minlbl-position':"absolute",
				'maxlbl-font-size':"3cqh", 'maxlbl-color':"black", 'maxlbl-width':"100%", 'maxlbl-text-align':"right", 'maxlbl-position':"absolute",
				# 'text-font-size':"30px", 'text-color':"black", 'text-rotate':"0deg", 'text-text-align':"center", 'text-overflow':"clip", 'text-top':"50%"
				'text-position':'absolute', 'text-top':'10%', 'text-left':'30%', 'text-font-size':"10cqh", 'text-color':"black", 'text-rotate':"0deg"
						}
							
		# # Om top, left height en width gewoon als getal op te kunnen geven worden deze als args binnengehaald en geconverteerd
		for attr_name in ['height', 'width', 'top', 'left']:
			attr = kwargs.get(attr_name,'50%')
			if type(attr) == str:	kwargs[attr_name] = attr
			else:					kwargs[attr_name] = "%spx" % attr
		# print('nw kwargs %s' % kwargs)

		super().__init__(parent, datapoint, default_config, default_style, **kwargs)
		
		# If the init of the parent class has not initialized the value, then use the value passed as argument
		if self.value is None: self.value = value
		
		# For whatever reason the normal top, left etc kwargs are not send to the super SVG widget...
		# self.style.update({'top':kwargs.get('top', '0%'), 'left':kwargs.get('left', '0%'), 'height':kwargs.get('height', '0%'), 'width':kwargs.get('width', '0%')})
		self.css_top = kwargs.get('top', '0%')
		self.css_left = kwargs.get('left', '0%')
		self.css_height = kwargs.get('height', '0%')
		self.css_width = kwargs.get('width', '0%')
		self.css_position = 'absolute'
		# with container-type this container is set as the resizing parent for the resizing of fonts that use container queries (cqw or cqh)
		self.style['container-type'] = 'inline-size'
		# For whatever reason 'size' causes Firefox browser to stop working
		# self.style['container-type'] = 'size'
		
		# print('config', type(self.config), self.config)
		# print('style', type(self.style), self.style)
		# input('any key')
		
		# Nu definieren we ook een VBox voor het huizen van alle labels, text etc. Maar niet de meelopende Value label
		self.lbl_cont = None
		self.lbl_cont = VBox()
		self.lbl_cont.css_height = '100%'
		self.lbl_cont.css_width = '100%'
		self.lbl_cont.css_position = "absolute"
		self.lbl_cont.css_background_color = "transparent"
		self.lbl_cont.css_justify_content = "space-between"

		self.fillcont = None
		self.fillcont = Container()
		# iterate over all entries in the xtra_style dict that startwith 'text_'
		for prop in [x for x in self.style.keys() if x.startswith('fill-')]: 
			self.fillcont.style[prop[len('fill-'):]] = self.style[prop]
		
		self.text = kwargs.get('text', '')
		self.text_lbl = None
		# See if we need do define a text label 
		if self.text:
			self.text_lbl = Label(self.text)
			# iterate over all entries in the xtra_style dict that startwith 'text_'
			for prop in [x for x in self.style.keys() if x.startswith('text-')]: 
				self.text_lbl.style[prop[len('text-'):]] = self.style[prop]
				
			self.text_lbl.style['height'] = "auto"
			self.text_lbl.style['width'] = "auto"
			
			# print('Style:  ', self.text_lbl.style)

		
		self.max_lbl = None
		self.min_lbl = None
		# Any min and max labels needed?
		if self.config["show_minmax"]:
			self.max_lbl = Label(str(self.config.get('max_value','')))
			# iterate over all entries in the xtra_style dict that startwith 'max-'
			for prop in [x for x in self.style.keys() if x.startswith('maxlbl-')]: 
				self.max_lbl.style[prop[len('maxlbl-'):]] = self.style[prop]
				
			self.min_lbl = Label(str(self.config.get('min_value','')))
			# iterate over all entries in the xtra_style dict that startwith 'min-'
			for prop in [x for x in self.style.keys() if x.startswith('minlbl-')]: 
				self.min_lbl.style[prop[len('minlbl-'):]] = self.style[prop]
			
			
		self.val_lbl = None
		# DO we need to display the value?
		if self.config["show_value"]:
			self.val_lbl = Label()
			# iterate over all entries in the xtra_style dict that startwith 'value_'
			for prop in [x for x in self.style.keys() if x.startswith('value-')]: 
				self.val_lbl.style[prop[len('value-'):]] = self.style[prop]
			
		self.append(self.fillcont)
		self.append(self.lbl_cont)
		if self.max_lbl: self.lbl_cont.append(self.max_lbl)
		# put the text label in the mother container...
		if self.text_lbl: self.append(self.text_lbl)
		if self.min_lbl: self.lbl_cont.append(self.min_lbl)
		if self.val_lbl: self.append(self.val_lbl)
		
		# self.text_lbl.style['z-index']='10'
		
		self.update()
		
	def refresh (self, *args, **kwargs):
		super().refresh(*args, **kwargs)
		# Logger.info(f'intermediate check: {self.value}')
		self.update()

		
	def update(self, **kwargs):
		try:
			# First check if there is a conditional format instruction for this widget
			# an example of a conditional format instruction is: dict(cond="gt", check_value=0.0, prop="color", true="green", false="darkgrey")
			if self.cond_format:
				# now walk through all defined conditional formats, and adjust the widget attributes and style accordingly
				for cf in self.cond_format:
					prop = cf.get('prop', self.config['dp_signal_prop'])
					if not prop: continue
					prop_nwvalue = None
					cond_check, prop_nwvalue = super().check_condition(cf)
					# do we have a new value for the property?
					if prop_nwvalue:
						if prop.startswith('fill-') and self.fillcont: self.fillcont.style[prop[len('fill-'):]] = prop_nwvalue
						if prop.startswith('text-') and self.text_lbl: self.text_lbl.style[prop[len('text-'):]] = prop_nwvalue
						if prop.startswith('minlbl-') and self.min_lbl: self.min_lbl.style[prop[len('minlbl-'):]] = prop_nwvalue
						if prop.startswith('maxlbl-') and self.max_lbl: self.max_lbl.style[prop[len('maxlbl-'):]] = prop_nwvalue
						if prop.startswith('value-') and self.val_lbl: self.val_lbl.style[prop[len('value-'):]] = prop_nwvalue
						else: self.style[prop] = prop_nwvalue
							
					# now check if we need to continue with the next conditional format
					if 'qit' in cf:
						if cf['qit'] and cond_check: break
			
			# Widget specific update logic.....
			# clip the value between max and min and calculate the percentage filled
			# Logger.info(f'determining max between {self.config["min_value"]} and {self.value}')
			nwvalue = max(self.config['min_value'], self.value)
			# Logger.info(f'determining min between {self.config["max_value"]} and {nwvalue}')
			nwvalue = min(self.config['max_value'], nwvalue)
			# Logger.info(f'Using a new buffer value 0f {nwvalue}')
			
			self.perc_fill = (nwvalue - self.config["min_value"]) * 100 / (self.config["max_value"] - self.config["min_value"])
			# Logger.info(f'Fill percentage {self.perc_fill}')
			
			self.fillcont.css_height = "%s%%" % (int(self.perc_fill))
			self.fillcont.css_top = "%s%%" % (100 - int(self.perc_fill))
	
			if self.val_lbl and self.value:
				value_str = '%s' % self.value
				if self.config['show_unit']: value_str += ' %s' % self.config['unit']
				value_str = value_str.strip()
				self.val_lbl.set_text(value_str)
				top = min(90, (100 - int(self.perc_fill)))
				self.val_lbl.style["top"] = "%s%%" % top
		except Exception as err:
			Logger.exception(f'{err}')

class JSEM_Rect(JSEM_GUI, Container):
	def __init__(self, parent=None, datapoint=None, **kwargs):

		# define the default style and config
		default_config = dict(dp_signal_prop='background-color', adopt_dp_signals=False)
		default_style = 	{
							'position':'absolute', 'margin':'0px', 
							'border-style':'solid', 'border-width':'2px', 'border-color':'black', 'border-radius':'0px',
							'background-color':'transparent',
							'text-font-size':"3cqh", 'text-color':"black", 'text-background-color':"transparent", 
							'text-text-align':"center", 'text-rotate':"0deg", 'text-overflow':"clip"
							}
							
		# # Om top, left height en width gewoon als getal op te kunnen geven worden deze als args binnengehaald en geconverteerd
		for attr_name in ['height', 'width', 'top', 'left']:
			attr = kwargs.get(attr_name,'50%')
			if type(attr) == str:	kwargs[attr_name] = attr
			else:					kwargs[attr_name] = "%spx" % attr
		# print('nw kwargs %s' % kwargs)

		super().__init__(parent, datapoint, default_config, default_style, **kwargs)

		# For whatever reason the normal top, left etc kwargs are not send to the super SVG widget...
		# self.style.update({'top':kwargs.get('top', '0%'), 'left':kwargs.get('left', '0%'), 'height':kwargs.get('height', '0%'), 'width':kwargs.get('width', '0%')})
		self.css_top = kwargs.get('top', '0%')
		self.css_left = kwargs.get('left', '0%')
		self.css_height = kwargs.get('height', '0%')
		self.css_width = kwargs.get('width', '0%')
		self.css_position = 'absolute'
		# with container-type this container is set as the resizing parent for the resizing of fonts that use container queries (cqw or cqh)
		self.style['container-type'] = 'inline-size'
		# For whatever reason 'size' causes Firefox browser to stop working
		# self.style['container-type'] = 'size'

		# print('config', type(self.config), self.config)
		# print('style', type(self.style), self.style)
		# input('any key')
		
		# Nu definieren we ook een VBox voor het huizen van alle labels, text etc.
		self.lbl_cont = VBox()
		self.lbl_cont.css_height = '100%'
		self.lbl_cont.css_width = '100%'
		# self.lbl_cont.css_position = "absolute"
		self.lbl_cont.css_background_color = "transparent"
		self.lbl_cont.css_justify_content = "center"

		self.text = kwargs.get('text', '')
		self.text_lbl = None
		# See if we need do define a text label 
		if self.text:
			self.text_lbl = Label(self.text)
			# iterate over all entries in the xtra_style dict that startwith 'text_'
			for prop in [x for x in self.style.keys() if x.startswith('text-')]: 
				self.text_lbl.style[prop[len('text-'):]] = self.style[prop]
			self.text_lbl.style['height'] = "auto"
			self.text_lbl.style['width'] = "auto"
			
		if self.text_lbl: self.lbl_cont.append(self.text_lbl)
		self.append(self.lbl_cont)

		self.update()
		
	def refresh (self, *args, **kwargs):
		super().refresh(*args, **kwargs)
		self.update()

	def update(self, **kwargs):
		# First check if there is a conditional format instruction for this widget
		# an example of a conditional format instruction is: dict(cond="gt", check_value=0.0, prop="color", true="green", false="darkgrey")
		if self.cond_format:
			# now walk through all defined conditional formats, and adjust the widget attributes and style accordingly
			for cf in self.cond_format:
				prop = cf.get('prop', self.config['dp_signal_prop'])
				if not prop: continue
				prop_nwvalue = None
				cond_check, prop_nwvalue = super().check_condition(cf)
				# do we have a new value for the property?
				if prop_nwvalue:
					if prop.startswith('text-') and self.text_lbl: self.text_lbl.style[prop[len('text-'):]] = prop_nwvalue
					else: 
						# print(f'prop {prop} set to {prop_nwvalue}')
						self.style[prop] = prop_nwvalue
						
				# now check if we need to continue with the next conditional format
				if 'qit' in cf:
					if cf['qit'] and cond_check: break

		# self.redraw()
		
		# Widget specific update logic.....
		# Nothing for this widget



def main(args):
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
