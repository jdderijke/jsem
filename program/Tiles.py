import datetime
import pathlib

from pandas.core.strings.accessor import cat_core

from common_utils import get_logger, pg_style, get_attr_from_stylestr

Logger = get_logger()

import math

import remi.gui as gui
from remi import start, App
from remi.gui import decorate_event, decorate_set_on_listener

from remi_addons import MultilineLabel, EditableTable
from remi_common import remove_child_from_widget

import pandas as pd
from common_utils import update_css_stylestr
from common_utils import get_extra_css, Waitkey

from lxml.etree import _Element
import pygal as pg
from pygal.style import Style
from test_tools.Testdata import *
# from porxpy.texts_en import *


DEFAULT_LINE_CHART_COLORS = ('blue,red,black,magenta,green,purple,maroon,coral,darkslategrey,burlywood,'
							 'aquamarine,brown,blueviolet,chartreuse,chocolate,crimson,dodgerblue,indigo')
							
DEFAULT_BAR_CHART_COLORS = Style().colors

DEFAULT_PIE_CHART_COLORS = Style().colors

DEFAULT_MAP_CHART_COLORS = Style().colors

class Tile(gui.Container):
	def __init__(self, title='', ok_cancel_buttons=False, layout='horizontal', close_button=False, allow_maximize=False, help_text:str='',
				 style='', title_style='', **kwargs):
		style = update_css_stylestr(f'position:static;background:Gainsboro;border-radius:10px;'
								 	     f'height:100%;width:100%;'
								 	     # f'min-height:300px;min-width:300px;margin:0.25%;'
										 f'overflow:hidden;align-items:center',
								style
								)
		super(Tile, self).__init__(style=style, **kwargs)
		
		self.main_cont = gui.Container(style='position:relative;display:flex;flex-direction:column;'
											 'width:100%;height:100%;background:transparent')
		self.append(self.main_cont)
		
		self.stored_width = self.css_width
		self.stored_height = self.css_height
		self.inputs = {}
		self.layout = layout
		self.ok_btn = None
		self.cn_btn = None
	
		# self.top_area = gui.HBox(style='width:100%')
		if allow_maximize or help_text or close_button:
			self.cntrl_cont = gui.HBox(style='position:absolute;top:2px;right:2px;width:auto;height:30px;padding:2px'
											 'justify-content:space-between; background-color:transparent;color:black;'
											 'z-index:100')
			btn_style = ('width:30px;height:100%;background-color:red;color:white;font-size:15px;text-align:center'
						 'border-radius:5px;border:solid black')
			if close_button:
				self.close_btn = gui.Button('X', style=btn_style)
				self.close_btn.onclick.connect(self.on_close)
				self.cntrl_cont.append(self.close_btn)
				
			if allow_maximize:
				self.size_state = 'normal'
				self.size_btn = gui.Button('[]', style=btn_style)
				self.size_btn.onclick.connect(self.size_btn_clicked)
				self.cntrl_cont.append(self.size_btn)
				
			if help_text:
				self.help_btn = gui.Button('?', style=btn_style)
				self.help_btn.onclick.connect(self.help_btn_clicked, help_text)
				self.cntrl_cont.append(self.help_btn)
				
			self.main_cont.append(self.cntrl_cont)

			
		if title:
			self.title_cont = gui.HBox(style='width:100%;height:auto;background:transparent')
			title_style = update_css_stylestr('font-size:1.8em;width:auto;height:100%;text-align:center;'
											  'background:transparent', title_style)
			self.title_widg = gui.Label(title, style=title_style)
			self.title_cont.append(self.title_widg)
			self.main_cont.append(self.title_cont)
			
		self.pres_cont = gui.Container(
			style=f'position:relative;display:flex;flex-direction:{"row" if layout=="horizontal" else "column"};'
				  f'flex-wrap:nowrap;justify-content:space-around;padding:1%;'
				  'height:100%;width:100%;background:transparent;overflow:auto')
		
		self.main_cont.append(self.pres_cont)
		
		if ok_cancel_buttons:
			cont = gui.HBox(style='position:relative;width:20%;min-width:100px;height:8%;min-height:25px;'
								  'justify-content:space-between;background:transparent;margin:2%;align-self:end')
			self.ok_btn = gui.Button('Ok', style='width:40%;height:100%')
			self.cn_btn = gui.Button('Cancel', style='width:40%;height:100%')
			cont.append([self.cn_btn, self.ok_btn])
			self.main_cont.append(cont)
			
			self.ok_btn.onclick.connect(self.on_confirm_dialog)
			self.cn_btn.onclick.connect(self.on_cancel_dialog)

	@decorate_event
	def on_close(self, *args, **kwargs):
		"""To close a widget in Remi, remove it as a child from its parent"""
		parent:gui.Tag
		parent = self.get_parent()
		parent.remove_child(self)
		return args
	
	@decorate_event
	def on_confirm_dialog(self, *args, **kwargs):
		return args
	
	@decorate_event
	def on_cancel_dialog(self, *args, **kwargs):
		return args
	
	def help_btn_clicked(self, btn, help_text, *args, **kwargs):
		help_tile = TextTile(help_text, close_button=True, style='position:absolute;left:10%;top:20%;'
																 'width:auto;height:60%;'
																 'border-style:solid;border-color:grey')
		
		self.main_cont.append(help_tile, key="__help_tile")
		
		
	def size_btn_clicked(self, btn, *args, **kwargs):
		if self.size_state == 'normal':
			# print(self.css_width)
			# print(self.css_height)
			# print(self.style['width'])
			# print(self.style['height'])
			if '%' in self.css_width:
				width = float(self.css_width.replace('%',''))
				if not '%' in self.css_height: raise ValueError('width and height must both be as percentage')
				height = float(self.css_height.replace('%',''))
				aspect_ratio = width / height
				if width > height:
					nw_width = '80%'
					nw_height = f'{int(80 / aspect_ratio)}%'
				else:
					nw_height = '80%'
					nw_width = f'{int(80 * aspect_ratio)}%'
			else:
				nw_height = '80%'
				nw_width = '80%'
			
			self.stored_width = self.css_width
			self.stored_height = self.css_height
			self.set_style(f'position:absolute;left:10%;top:10%;width:{nw_width};height:{nw_height};'
						   f'z-index:999;border-style:solid;border-color:grey')
			self.size_btn.set_text('-')
			self.size_state = 'maximized'
		else:
			self.set_style(f'position:static;width:{self.stored_width};height:{self.stored_height};'
						   f'z-index:auto;border-style:none')
			self.size_btn.set_text('[ ]')
			self.size_state = 'normal'


	def add_field_with_label(self, key, label_description, field):
		"""
		Adds a field to the Tile together with a descriptive label and a unique identifier.
	
		Note: You can access to the fields content calling the function Tile.get_field(key).
	
		Args:
			key (str): The unique identifier for the field.
			label_description (str): The string content of the description label.
			field (Widget): The instance of the field Widget. It can be for example a TextInput or maybe
			a custom widget.
		"""
		self.inputs[key] = field
		field.set_style('font-size:inherit')
		label = gui.Label(label_description, style='margin:0px 5px;min-width:20%;font-size:inherit')
		container = gui.HBox(style='justify-content:space-between;overflow:auto;margin:1%;background:transparent')
		container.append(label, key='lbl' + key)
		container.append(self.inputs[key], key=key)
		self.pres_cont.append(container, key=key)
	
	def add_field(self, key, field):
		"""
		Adds a field to the dialog with a unique identifier.

		Note: You can access to the fields content calling the function Tile.get_field(key).

		Args:
			key (str): The unique identifier for the field.
			field (Widget): The widget to be added to the dialog, TextInput or any Widget for example.
		"""
		# self.inputs[key] = field
		# container = gui.HBox(style='justify-content:space-between;overflow:auto;background:transparent')
		# container.append(self.inputs[key], key=key)
		# self.pres_cont.append(container, key=key)
		
		self.inputs[key] = field
		self.pres_cont.append(self.inputs[key], key=key)

	
	def get_field(self, key):
		"""
		Args:
			key (str): The unique string identifier of the required field.
	
		Returns:
			Widget field instance added previously with methods Tile.add_field or
			Tile.add_field_with_label.
		"""
		return self.inputs[key]
	
	
	


class GraphTile(Tile):
	def __init__(self, data:pd.DataFrame, add_table:bool=False, **kwargs):
		screen_ratio = 1920 / 1080
		
		self.default_colors = Style().colors
		
		self.add_table = add_table
		self.add_tbl_totals = kwargs.pop('add_tbl_totals', False)

		self.precision = kwargs.pop('precision', 2)
		self.use_log_values = kwargs.pop('use_log_values', False)
		asp_ratio = kwargs.pop('aspect_ratio', '1/1')
		self.aspect_ratio = int(asp_ratio.split('/')[0]) / int(asp_ratio.split('/')[1])
		self.is_percentage = kwargs.pop('is_percentage', False)
		self.show_values_in_legend = kwargs.pop('show_values_in_legend', False)
		self.limit_results_to = kwargs.pop('limit_results_to', 15)
		
		# calc viewbox settings
		self.x_offset = kwargs.pop('x_offset', 0)
		self.y_offset = kwargs.pop('x_offset', 0)
		self.graph_size_x = kwargs.pop('graph_size_x', 600)
		self.graph_size_y = kwargs.pop('graph_size_y', 600)
		self.vb_width = self.graph_size_x
		self.vb_height = int((self.graph_size_y * self.aspect_ratio) / screen_ratio)
		
		# We dont want to impact the original data argument, we will work with a copy...
		self.work_df: pd.DataFrame = data.copy(deep=True)
		# self.work_df = self.work_df.reset_index()
		
		super().__init__(title=kwargs.pop('title', ''), style=kwargs.pop('style', ''),
									  title_style=kwargs.pop('title_style', ''), **kwargs)
		
		self.svg_cont = gui.Svg(style='height:100%;width:100%;background:transparent;overflow:auto')
		self.svg_cont.set_viewbox(self.x_offset, self.y_offset, self.vb_width, self.vb_height)
		self.pres_cont.append(self.svg_cont)
		self.svg_data = None
		if self.add_table: self._make_table(**kwargs)
		# any pygal specific kwargs (like style and config items) are stored first
		self.pg_kwargs = kwargs
	
	def _make_table(self, **kwargs):
		self.table_cont = gui.Container(style=update_css_stylestr(
			'position:absolute;top:2%;left:2%;width:auto;'
			'height:auto;max-height:50%;overflow:auto;font-size:1.0em',
			kwargs.pop('tbl_style', '')))
		self.table = EditableTable(sort_on_title_click=False, style='white-space:nowrap; width:auto; height:auto')
		
		self.table.set_data(self.work_df.reset_index())
		self.table_cont.append(self.table)
		self.pres_cont.append(self.table_cont)
	
	def _make_graph(self, graph_df:pd.DataFrame, **kwargs) -> _Element:
		raise NotImplementedError("The _make_graph method must be overridden in the child class!!")
	
	def update(self, calling_widget=None, *args, **kwargs):
		# Switch to a new work_df?
		nw_data_df = kwargs.pop('new_data', None)
		if nw_data_df is not None:
			self.work_df = nw_data_df

		# # apply a filter on the work_df from the info in the table..
		# if calling_widget:
		# 	pass
		
		# put the active colors in a pg_style string and update any existing user-defined pg_style with it, store in kwargs.
		color_style_str = f'colors:{",".join(self.default_colors)}'
		user_defined_pg_style = self.pg_kwargs.pop('pg_style', '')
		self.pg_kwargs['pg_style'] = update_css_stylestr(color_style_str, user_defined_pg_style)
		
		# First remove any old chart that may be there before we build a new one
		remove_child_from_widget(self.svg_data, self.svg_cont)
		if not self.work_df.empty:
			self.svg_data = self._make_graph(self.work_df.reset_index(), width=self.graph_size_x, height=self.graph_size_y,
										   **self.pg_kwargs)
		else:
			self.svg_data = gui.SvgText(x=int(self.graph_size_x/2) - 40,y=int(self.graph_size_y/2) - 20,
										text='NO DATA', style='font-size:2em')
		self.svg_cont.add_child(str(id(self.svg_data)), self.svg_data)
		
		if self.add_table:
			# optionally add a totals row, only in the table.... not in the graph
			if self.add_tbl_totals:
				sums = [self.work_df[col].sum() for col in self.work_df.columns]
				if sums: self.work_df.loc['Totals'] = sums
			# round to precision
			for col in self.work_df.columns:
				self.work_df[col] = self.work_df[col].astype(float)
				self.work_df[col] = self.work_df[col].round(self.precision)
			
			self.table.set_data(self.work_df.reset_index())


# class MapTile(GraphTile):
#
# 	pg_style = ('background:transparent;plot_background:transparent;major_label_font_size:18;tooltip_font_size:8;'
# 				 'title_font_family:Arial;title_font_size:14;stroke_width:2;'
# 				 'colors:red,blue,green,black,yellow,orange,purple,darkgrey')
#
#
# 	pg_addon_css = '''
# 	  {{ id }}.tooltip .value{
# 	    font-weight: bold;
# 	    fill: blue;
# 	   /* for whatever reason svg elements do not listen to the color css style setting, use fill instead */
# 	   /* color: blue; */
# 	  }
# 	  {{ id }}.title {
# 	    font-weight: bold;
# 	    fill: black;
# 	  }
# 	'''
#
# 	def __init__(self, data:pd.DataFrame, add_table:bool=False, **kwargs):
# 		"""
#
# 		:param data:
# 		:param add_table: add a table next to the graph, style to be set with tbl_style string
# 		:keyword use_log_values: first calculates the log of a value before. Thus enabling smaller differences to become visible
# 		:keyword is_percentage: If data representations is in percentages, then we scale back to fractions (between 0 and 1)
# 		:keyword precision: number of decimal places to display in the graphs and/or tables
# 		:keyword title: title string to be added as a non scrollable header, style to be set with title_style string
# 		:keyword aspect_ratio: aspect ratio of the graph or map, a ratio of 1/1 corrects for a screen ratio of 1920/1080
# 		:keyword style: a style string in css format defining the style of the top container
# 		:keyword x_offset: how many pixels to shift the graph to the left
# 		:keyword y_offset: how many pixels to shift the graph to the top
# 		:keyword graph_size: square (width and height) size of the svg viewbox and of the Pygal viewbox
# 		:keyword title_style: a style string in css format
# 		:keyword tbl_style: a style string in css format
# 		:keyword pg_style: a style string in Pygal format
# 		"""
#
# 		use_log_values = kwargs.pop('use_log_values', True)
# 		add_tbl_totals = kwargs.pop('add_tbl_totals', True)
# 		is_percentage = kwargs.pop('is_percentage', True)
#
# 		super().__init__(data, add_table, use_log_values=use_log_values, add_tbl_totals=add_tbl_totals,
# 									  is_percentage=is_percentage, **kwargs)
#
# 		self.default_colors=DEFAULT_MAP_CHART_COLORS
# 		self.update()
#
#
# 	def _make_graph(self, map_df:pd.DataFrame, **kwargs) -> _Element:
# 		'''
# 		Generates a color coded world map with exposure data... by country or by region
# 		The data passed MUST be a dataframe with the exposure type (regions or countries) in the index and the exposure
# 		percentages in the column named 'exposure' of the dataframe
#
# 		:param data: Dataframe with regional or country exposure data, first columns must be exposure category,
# 		  second column must contain the exposure data
#
# 		:keyword precision: Number of decimal places that show up in the tooltips and legends
# 		:keyword use_log_values (False): (maps only) Use log values when assigning colors gradients to countries or regions
# 		:keyword is_percentage (True): Autoscale to percentages
# 		:return:
# 		'''
#
# 		config = pg.Config(
# 							# explicit_size=True,
# 							show_legend=False,
# 							height=600,
# 							width=600
# 							)
#
#
# 		# add xtra css style information
# 		path_to_file = pathlib.Path(pathlib.Path.cwd(), "css/porxpy_tmp_css_file").with_suffix(".css")
# 		with open(path_to_file, 'w') as f:
# 			f.write(self.pg_addon_css)
# 		config.css.append(f'file://{path_to_file}')
#
# 		# Construct a Style object for Pygal
# 		new_style_str = update_css_stylestr(self.pg_style, kwargs.pop('pg_style', ''))
#
# 		# cat_col is always the first column,
# 		cat_col = map_df.columns[0]
# 		val_col = 'exposure'
#
# 		if cat_col not in ['regions','countries']:
# 			raise ValueError('Index_name must be either regions or countries...')
#
# 		if cat_col == 'countries':
# 			# convert the countries from Morningstar country names to alpha-2 country codes
# 			work_data = pd.merge(map_df, COUNTRY_DF[['mstar_country', 'alpha-2']],
# 								 how='left', left_on=[cat_col], right_on=['mstar_country'])
# 			err_df = work_data[work_data.isnull().any(axis=1)]
# 			if len(err_df) > 0: Logger.warning(f'Missing mstar_country in country table. \n{err_df}')
# 			cat = work_data['alpha-2'].values.tolist()
# 		else:
# 			# No need to convert the Morningstar region names, they are added in the SupranationalWorld definitions at startup
# 			cat = map_df[cat_col].values.tolist()
#
# 		cat = cat[:self.limit_results_to]
# 		val = map_df[val_col].values.tolist()[:self.limit_results_to]
# 		# do some data conversions and rounding if needed
# 		if val:
# 			if self.is_percentage and max(val) > 1.0: val = [v/100.0 for v in val]
# 			if self.use_log_values: val = [math.log10(v) if v > 0.0 else v for v in val]
# 		# prepare the data to be loaded in the map
# 		map_data = {k:v for k,v in zip(cat,val)}
#
# 		if cat_col == 'regions':
# 			map_chart = pg.maps.world.SupranationalWorld(config=config, style=pg_style(new_style_str), **kwargs)
# 		elif cat_col == 'countries':
# 			map_chart = pg.maps.world.World(config=config, style=pg_style(new_style_str), **kwargs)
#
# 		map_chart.add(f'{cat_col.upper()}', map_data)
# 		return map_chart.render(is_unicode=True)
	


class BarTile(GraphTile):
	pg_style = ('background:transparent;plot_background:transparent;major_label_font_size:18;tooltip_font_size:24;'
				 'stroke_width:2;value_font_size:20;legend_font_size:20;'
				 'colors:blue,red,black,magenta,green,purple,maroon,coral,darkslategrey,burlywood,aquamarine,brown,'
				 'blueviolet,chartreuse,chocolate,crimson,dodgerblue,indigo')

	pg_addon_css = '''
  {{ id }}.tooltip rect{
    border-radius: 10;
    font-size: 30;
   /* for whatever reason svg elements do not listen to the color css style setting, use fill instead */
   /* color: blue; */
  }

  {{ id }}.tooltip text{
    font-size: 30;
    fill:green
   /* for whatever reason svg elements do not listen to the color css style setting, use fill instead */
   /* color: blue; */
  }


  {{ id }}.tooltip .value{
    font-weight: bold;
    font-size:30;
    fill: blue;
   /* for whatever reason svg elements do not listen to the color css style setting, use fill instead */
   /* color: blue; */
  }

  {{ id }}.tooltip .legend{
    font-weight: bold;
    fill: blue;
   /* for whatever reason svg elements do not listen to the color css style setting, use fill instead */
   /* color: blue; */
  }

  {{ id }}.title {
    font-weight: bold;
    fill: black;
  }
	'''
	
	def __init__(self, data: pd.DataFrame, add_table: bool = False, **kwargs):
		"""
		
		:param data:
		:param add_table: add a table next to the graph, style to be set with tbl_style string
		:keyword use_log_values: first calculates the log of a value before. Thus enabling smaller differences to become visible
		:keyword is_percentage: If data representations is in percentages, then we scale back to fractions (between 0 and 1)
		:keyword precision: number of decimal places to display in the graphs and/or tables
		:keyword title: title string to be added as a non scrollable header, style to be set with title_style string
		:keyword aspect_ratio: aspect ratio of the graph or map, a ratio of 1/1 corrects for a screen ratio of 1920/1080
		:keyword style: a style string in css format defining the style of the top container
		:keyword x_offset: how many pixels to shift the graph to the left
		:keyword y_offset: how many pixels to shift the graph to the top
		:keyword graph_size: square (width and height) size of the svg viewbox and of the Pygal viewbox
		:keyword title_style: a style string in css format
		:keyword tbl_style: a style string in css format
		:keyword pg_style: a style string in Pygal format
		"""
		add_tbl_totals = kwargs.pop('add_tbl_totals', True)
		is_percentage = kwargs.pop('is_percentage', True)
		tbl_style = update_css_stylestr('left:auto;right:2%', kwargs.pop('tbl_style', ''))
		super().__init__(data, add_table, add_tbl_totals=add_tbl_totals, is_percentage=is_percentage,
						 tbl_style = tbl_style, **kwargs)
		
		self.default_colors = DEFAULT_BAR_CHART_COLORS
		self.update()
	
	def _make_graph(self, bar_df: pd.DataFrame, **kwargs) -> _Element:
		'''
		Generates a bar chart with (specifically) exposure data...

		:return: filename ('bar_chart.svg|png'): The filename to store a file or png rendered result
		'''
		
		config = pg.Config(
			# explicit_size=True,
			height=600,
			width=600
		)
		
		# add xtra css style information
		path_to_file = pathlib.Path(pathlib.Path.cwd(), "css/porxpy_tmp_css_file").with_suffix(".css")
		with open(path_to_file, 'w') as f:
			f.write(self.pg_addon_css)
		config.css.append(f'file://{path_to_file}')
		
		# Construct a Style object for Pygal
		new_style_str = update_css_stylestr(self.pg_style, kwargs.pop('pg_style', ''))

		# cat_col is always the first column,
		cat_col = bar_df.columns[0]
		val_col = bar_df.columns[1]
		
		cat = bar_df[cat_col].values.tolist()[:self.limit_results_to]
		val = bar_df[val_col].values.tolist()[:self.limit_results_to]

		# optionally add the value to the category which will show up in de legend...
		if self.show_values_in_legend:
			unit = '%' if self.is_percentage else ''
			cat = [f'{round(v, self.precision)} {unit} -{c}' for c,v in zip(cat,val)]

		# do some data conversions and rounding if needed
		if val:
			if self.is_percentage and max(val) > 1.0: val = [v/100.0 for v in val]
			if self.use_log_values: val = [math.log10(v) if v != 0.0 else v for v in val]
		
		bar_chart = pg.Bar(config=config, style=pg_style(new_style_str), show_x_labels=True, print_values=True, **kwargs)
		
		for k, v in zip(cat, val):
			bar_chart.add(k, v)
		
		if self.is_percentage:
			bar_chart.value_formatter = lambda x: f'{x:.{self.precision}%}'
		
		return bar_chart.render(is_unicode=True)
	


class PieTile(GraphTile):
	pg_style = ('background:transparent;plot_background:transparent;major_label_font_size:18;tooltip_font_size:24;'
				'stroke_width:2;value_font_size:22;legend_font_size:22')
	
	pg_addon_css = '''
  {{ id }}.tooltip .value{
    border-radius:10;
    font-size:30;
    font-weight: bold;
    fill: blue;
   /* for whatever reason svg elements do not listen to the color css style setting, use fill instead */
   /* color: blue; */
  }

  {{ id }}.tooltip .legend{
    font-weight: bold;
    fill: blue;
   /* for whatever reason svg elements do not listen to the color css style setting, use fill instead */
   /* color: blue; */
  }

  {{ id }}.title {
    font-weight: bold;
    fill: black;
  }
	'''
	
	def __init__(self, data: pd.DataFrame, add_table: bool = False, **kwargs):
		"""

		:param data:
		:param add_table: add a table next to the graph, style to be set with tbl_style string
		:keyword add_tbl_totals: add a totals row at the end of the table, adding all columns except the index
		:keyword use_log_values: first calculates the log of a value before. Thus enabling smaller differences to become visible
		:keyword is_percentage: If data representations is in percentages, then we scale back to fractions (between 0 and 1)
		:keyword precision: number of decimal places to display in the graphs and/or tables
		:keyword title: title string to be added as a non scrollable header, style to be set with title_style string
		:keyword aspect_ratio: aspect ratio of the graph or map, a ratio of 1/1 corrects for a screen ratio of 1920/1080
		:keyword style: a style string in css format defining the style of the top container
		:keyword x_offset: how many pixels to shift the graph to the left
		:keyword y_offset: how many pixels to shift the graph to the top
		:keyword graph_size: square (width and height) size of the svg viewbox and of the Pygal viewbox
		:keyword title_style: a style string in css format
		:keyword tbl_style: a style string in css format
		:keyword pg_style: a style string in Pygal format
		"""
		add_tbl_totals = kwargs.pop('add_tbl_totals', True)
		is_percentage = kwargs.pop('is_percentage', True)
		
		super().__init__(data, add_table, add_tbl_totals=add_tbl_totals, is_percentage=is_percentage, **kwargs)
		
		self.default_colors = DEFAULT_BAR_CHART_COLORS
		self.update()
	
	def _make_graph(self, bar_df: pd.DataFrame, **kwargs) -> _Element:
		'''
		Generates a pie chart ...

		:return: _Element string to inject in HTML
		'''
		
		config = pg.Config(
			# explicit_size=True,
			show_x_labels=True,
			print_values=True,
			height=600,
			width=600
		)
		
		# add xtra css style information
		path_to_file = pathlib.Path(pathlib.Path.cwd(), "css/porxpy_tmp_css_file").with_suffix(".css")
		with open(path_to_file, 'w') as f:
			f.write(self.pg_addon_css)
		config.css.append(f'file://{path_to_file}')

		# Construct a Style object for Pygal
		new_style_str = update_css_stylestr(self.pg_style, kwargs.pop('pg_style', ''))
		
		# cat_col is always the first column,
		cat_col = bar_df.columns[0]
		val_col = bar_df.columns[1]
		
		# make lists and limit the results to avoid cluttered graphs
		cat = bar_df[cat_col].values.tolist()[:self.limit_results_to]
		val = bar_df[val_col].values.tolist()[:self.limit_results_to]
		
		# optionally add the value to the category which will show up in de legend...
		if self.show_values_in_legend:
			unit = '%' if self.is_percentage else ''
			cat = [f'{round(v, self.precision)} {unit} -{c}' for c,v in zip(cat,val)]
			
		# do some data conversions and rounding if needed
		if val:
			if self.is_percentage and max(val) > 1.0: val = [v / 100.0 for v in val]
			if self.use_log_values: val = [math.log10(v) if v != 0.0 else v for v in val]
		
		pie_chart = pg.Pie(config=config, style=pg_style(new_style_str), **kwargs)
		
		for k, v in zip(cat, val):
			pie_chart.add(k, [{'value': v, 'label': k}])
		
		if self.is_percentage:
			pie_chart.value_formatter = lambda x: f'{x:.{self.precision}%}'
			
		return pie_chart.render(is_unicode=True)



class LineTile(GraphTile):
	pg_style = ('background:transparent;plot_background:transparent;major_label_font_size:18;tooltip_font_size:24;'
				'stroke_width:2;value_font_size:22;legend_font_size:22')
	
	pg_addon_css = '''
  {{ id }}.tooltip .value{
    border-radius:10;
    font-size:30;
    font-weight: bold;
    fill: blue;
   /* for whatever reason svg elements do not listen to the color css style setting, use fill instead */
   /* color: blue; */
  }

  {{ id }}.tooltip .legend{
    font-weight: bold;
    fill: blue;
   /* for whatever reason svg elements do not listen to the color css style setting, use fill instead */
   /* color: blue; */
  }

  {{ id }}.title {
    font-weight: bold;
    fill: black;
  }
	'''
	
	def __init__(self, data: pd.DataFrame, add_table: bool = False, **kwargs):
		"""

		:param data:
		:param add_table: add a table next to the graph, style to be set with tbl_style string
		:keyword limit_results_to: limit the number of datapoints in the graph, for line the last n datapoints will be used
		:keyword add_tbl_totals: add a totals row at the end of the table, adding all columns except the index
		:keyword use_log_values: first calculates the log of a value before. Thus enabling smaller differences to become visible
		:keyword is_percentage: If data representations is in percentages, then we scale back to fractions (between 0 and 1)
		:keyword precision: number of decimal places to display in the graphs and/or tables
		:keyword title: title string to be added as a non scrollable header, style to be set with title_style string
		:keyword aspect_ratio: aspect ratio of the graph or map, a ratio of 1/1 corrects for a screen ratio of 1920/1080
		:keyword style: a style string in css format defining the style of the top container
		:keyword x_offset: how many pixels to shift the graph to the left
		:keyword y_offset: how many pixels to shift the graph to the top
		:keyword graph_size: square (width and height) size of the svg viewbox and of the Pygal viewbox
		:keyword title_style: a style string in css format
		:keyword tbl_style: a style string in css format
		:keyword pg_style: a style string in Pygal format
		"""
		graph_size_x = kwargs.pop('graph_size_x', 1200)
		graph_size_y = kwargs.pop('graph_size_y', 600)
		limit_results_to = kwargs.pop('limit_results_to', 1000)
		
		self.chart_colors = get_attr_from_stylestr(kwargs.pop('pg_style',''), 'colors', DEFAULT_LINE_CHART_COLORS)
		if self.chart_colors:
			self.chart_colors = [color for color in self.chart_colors.split(',')]
		else:
			self.chart_colors = DEFAULT_LINE_CHART_COLORS
		self.selected_colors = []

		super().__init__(data, add_table, graph_size_x=graph_size_x, graph_size_y=graph_size_y,
						 limit_results_to=limit_results_to, **kwargs)

		self.selection = self.work_df.columns

		if self.add_table:
			self.update(self.table)
		else:
			self.update()
		
	def _make_graph(self, line_df: pd.DataFrame, **kwargs) -> _Element:
		'''
		Generates a Dateline chart ...

		:return: _Element string to inject in HTML
		'''
		
		config = pg.Config(
			# explicit_size=True,
			show_legend=False,
			x_label_rotation=45,
			show_dots=False,
			show_x_labels=True,
			print_values=True,
			height=600,
			width=600
		)
		
		# add xtra css style information
		path_to_file = pathlib.Path(pathlib.Path.cwd(), "css/porxpy_tmp_css_file").with_suffix(".css")
		with open(path_to_file, 'w') as f:
			f.write(self.pg_addon_css)
		config.css.append(f'file://{path_to_file}')

		# Construct a Style object for Pygal
		new_style_str = update_css_stylestr(self.pg_style, kwargs.pop('pg_style', ''))
		
		# x_labels_major_every = 6, show_minor_x_labels = False,
		line_chart = pg.DateLine(config=config, style=pg_style(new_style_str), **kwargs)
		
		# line_chart.config.range = kwargs.pop('range', None)
		
		# date_col is always the first column,
		date_col = line_df.columns[0]
		# make lists and limit the results to avoid cluttered graphs
		dates = line_df[date_col].values.tolist()[-self.limit_results_to:]
		date_labels = [datetime.strptime(x, "%Y-%m-%d").date() for x in dates]
		
		for col in line_df.columns[1:]:
			val = line_df[col].values.tolist()[-self.limit_results_to:]
			# do some data conversions and rounding if needed
			if val:
				if self.is_percentage and max(val) > 1.0: val = [v / 100.0 for v in val]
				if self.use_log_values: val = [math.log10(v) if v != 0.0 else v for v in val]
			
			line_chart.add(col, list(zip(date_labels, val)))
		
		if self.is_percentage:
			line_chart.value_formatter = lambda x: f'{x:.{self.precision}%}'
		
		return line_chart.render(is_unicode=True)

	def _make_table(self, **kwargs):
		self.table_cont = gui.Container(style=update_css_stylestr(
			'position:absolute;top:2%;left:2%;width:auto;max-width:35%;'
			'height:98%;overflow:auto;font-size:1.0em;background:transparent',
			kwargs.pop('tbl_style', '')))
		self.table = EditableTable(sort_on_title_click=True,
								   style='white-space:nowrap;width:auto;height:auto;font-size:0.8em')
		self.table.on_toggle.connect(self.update, self.table)
		self.table.on_table_row_click.connect(self.set_item_colors_in_table)
		
		# make sure we have enough colors defined, at least as many as there are columns in the dataframe
		ln = len(self.work_df.columns)
		lc = len(self.chart_colors)
		# if needed duplicate/re-use the colors
		self.chart_colors = (self.chart_colors * (int(ln / lc) + 1))[:ln]
		legend_table_df = pd.DataFrame(
			{'show': [False for col in self.work_df.columns], 'name': [col for col in self.work_df.columns],
			 'color': self.chart_colors})
		self.table.set_data(legend_table_df, editable=['show'], toggle=['show'])
		
		self.selected_colors = legend_table_df[legend_table_df['show']==True]['color'].values.tolist()
		
		self.set_item_colors_in_table()
		
		self.table.on_item_changed.connect(self.update)
		self.table_cont.append(self.table)
		self.pres_cont.append(self.table_cont)
	
	def set_item_colors_in_table(self, *args, **kwargs):
		"""
		Sets the background colors in the 'color' column of the table to the value written in the
		corresponding table_item
		:return:
		"""
		_idx = self.table.column_nr('color')
		for row in range(1, self.table.row_count):
			# skip title row
			item = self.table.item_at(row, _idx)
			item.style['background-color'] = item.get_text()
	
		return args
	
	def update(self, calling_widget=None, *args, **kwargs):
		# Switch to a new work_df?
		nw_data_df = kwargs.pop('nw_data', None)
		if nw_data_df is not None:
			self.work_df = nw_data_df

		# apply a filter on the work_df from the info in the table..
		if type(calling_widget) is EditableTable:
			# table_item, new_value, row, column = args
			legend_table_df = self.table.get_data(as_dataframe=True)
			selection = legend_table_df[legend_table_df['show']==True]['name'].values.tolist()
			if selection:
				y_range = (self.work_df[selection].min(axis=None), self.work_df[selection].max(axis=None))
				self.pg_kwargs['yrange'] = y_range		# store the dynamic range calculation in kwargs to be picked up later
			self.selection = selection
			self.selected_colors = legend_table_df[legend_table_df['show']==True]['color'].values.tolist()
			
		# put the active colors in a pg_style string and inject in pg_style, store in pg_kwargs.
		color_style_str = f'colors:{",".join(self.selected_colors)}'
		pg_style = self.pg_kwargs.pop('pg_style','')
		self.pg_kwargs['pg_style'] = update_css_stylestr(pg_style, color_style_str)
		
		# First remove any old chart that may be there before we build a new one
		remove_child_from_widget(self.svg_data, self.svg_cont)
		self.svg_data = self._make_graph(self.work_df[self.selection].reset_index(), width=self.graph_size_x, height=self.graph_size_y, **self.pg_kwargs)
		self.svg_cont.add_child(str(id(self.svg_data)), self.svg_data)


class TableTile(Tile):
	# def __init__(self, data:pd.DataFrame, editable:list[str]=None, toggle:list[str]=None, tooltips:list[list[str]]=None, tip_type:str='item',
	# 			 rowdata_links=None, on_item_changed=None, on_table_row_click=None, **kwargs):
	def __init__(self, on_item_changed=None, on_table_row_click=None, **kwargs):
		
		"""
		Represents a tile with an optional title and a table (optionally editable)
		:param on_item_changed: 		reference to routine that should be called on item changed, args are: table,item,nw_value,row,column
		:param on_table_row_click: 		reference to routine that should be called on row clicked, args are: table,row,item
		:param kwargs:					For kwargs see the set_data method of the EditableTable class
		"""
		
		super(TableTile, self).__init__(title = kwargs.pop('title', ''), style = kwargs.pop('style', ''),
										title_style = kwargs.pop('title_style', ''),**kwargs)
	
		self.table_cont = gui.Container(style='width:100%;height:100%;overflow:auto;background:transparent')
		tbl_style = update_css_stylestr('white-space:nowrap;width:auto;height:auto;font-size:1.0em;margin:auto', kwargs.pop('tbl_style',''))
		tt_style = update_css_stylestr('text-align:left;color:black;height:auto;left:100%;top:-200%;width:auto', kwargs.pop('tt_style', ''))
		self.table = EditableTable(**kwargs, style=tbl_style)
		self.table.set_data(**kwargs, tt_style=tt_style)

		if on_item_changed:
			self.table.on_item_changed.connect(on_item_changed)

		if on_table_row_click:
			self.table.on_table_row_click.connect(on_table_row_click)
		
		self.table_cont.append(self.table)
		self.pres_cont.append(self.table_cont)


class TextTile(Tile):
	def __init__(self, text:str='', **kwargs):
		super(TextTile, self).__init__(title = kwargs.pop('title', ''), style = kwargs.pop('style', ''),
										title_style = kwargs.pop('title_style', ''),**kwargs)
		
		self.mll = MultilineLabel(text=text, style='width:fit-content;height:fit-content;padding:10px')
		self.pres_cont.append(self.mll)


class MyApp(App):
	def __init__(self, *args):
		super(MyApp, self).__init__(*args)
	
	def main(self):
		# insert an addition to the css stylesheet, specifically for the remi add-ons
		Logger.info("Looking for additional css files....")
		style_str = get_extra_css("css")
		head = self.page.get_child('head')
		head.add_child(str(id(style_str)), style_str)

		top_cont = gui.Container(style='position:absolute;display:flex;flex-direction:row;left:0%;top:0%;width:100%;height:100%;flex-wrap:wrap')
		
		# test = Tile(title='Test Title', ok_cancel_buttons=True, layout='vertical', style='height:30%;width:30%')
		# testinput = gui.TextInput()
		# testinput.set_value('Dit is een teststring om te kijken hoe width:auto werkt')
		# test.add_field_with_label("_testfield1", "Dit is een label:", gui.TextInput(style="background:orange"))
		# test.add_field_with_label("_testfield2", "Dit is ook een label:", gui.TextInput(style="background:yellow"))
		# test.add_field_with_label("_testfield3", "Dit is alweer een label:", gui.TextInput(style="background:red"))
		# test.add_field_with_label("_testfield4", "Dit is zowaar een label:", gui.TextInput(style="background:gray"))
		# test.add_field_with_label("_testfield5", "Dit is misschien ook wel alweer zowaar een label:", testinput)
		# test.ok_btn.onclick.connect(lambda *args: test.get_field("_testfield1").set_value("OK button clicked..."))
		# test.cn_btn.onclick.connect(lambda *args: test.get_field("_testfield1").set_value("Cancel button clicked..."))


		test1 = TableTile(table_data=test_df, editable=['Enabled','First Name'], title='Test', style='height:49.5%',
						  on_item_changed=lambda table, item, nw_value, row, col: print(nw_value))
		test1.table.ondblclick.connect(lambda *args: print('double click'))
		# test2 = TextTile(text='Dit is een test...', help_text=top_positions_msg, allow_maximize=True,
		# 				 title='Multiline Label', style='position:relative;height:49.5%;width:49.5%')

		# test3 = MapTile(countries_df, allow_maximize=True, style='position:relative;height:49.5%;width:49.5%', tbl_style='font-size:1.0em',
		# 				aspect_ratio='1/1', title='Hoofdmap')
		# test4 = MapTile(countries_df, add_table=False,
		# 				style='position:absolute;bottom:2%;right:2%;height:30%;width:30%;background:silver',
		# 				aspect_ratio='4/3', title='Eerste submap', pg_style='plot_background:yellow;colors:green,blue,red')
		# test6 = MapTile(countries_df, add_table=False, style='position:absolute;bottom:2%;left:2%;height:30%;width:20%;background:white',
		# 				aspect_ratio='4/3', title='Tweede submap', title_style='font-size:0.7em', pg_style='colors:blue,green,red')
		#
		# test5 = MapTile(countries_df, add_table=False, title='mooi he? Scrolt niet mee!!', title_style='color:white',
		# 				style='position:absolute;top:2%;right:2%;height:70%;width:30%;background:black',
		# 				aspect_ratio='16/9', pg_style='colors:white,yellow,silver')
		#
		# test7 = BarTile(countries_df, allow_maximize=True, add_table= True, title='BarChart', style='width:29.5%;height:49.5%', show_legend=False,
		# 				x_offset=0)
		#
		# test8 = PieTile(countries_df, allow_maximize=True, add_table=False, title="PieChart", style='width:34.5%;height:49.5%', aspect_ratio='1/1',
		# 				show_values_in_legend=True, truncate_legend=100, pg_style='legend_font_size:16', x_offset=60,
		# 				is_percentage=True)
		#
		# test9 = LineTile(line_test_df, allow_maximize=True, title='linechart', add_table=True, style='width:34.5%;height:49.5%')
		#
		# dial = gui.GenericDialog(title="Dit is een generic dialog", style="width:50%;height:50%")
		# dial.hide = lambda: top_cont.empty()
		# dial.show = lambda: top_cont.append(dial)
		# dial .add_field("_tile3", test3)
		# # dial.cancel_dialog.connect(cncl_cash_dialog)
		# # dial.confirm_dialog.connect(ok_cash_dialog)
		# dial.show()
		
		# test3.pres_cont.append([test4, test6])
		# test2.pres_cont.append(test5)
		# top_cont.append([test3])
		# # # top_cont.append([test4])
		# top_cont.append(([test]))
		top_cont.append(([test1]))
		# top_cont.append([test2])
		# top_cont.append([test7])
		# top_cont.append([test8])
		# top_cont.append([test9])
		return top_cont








if __name__ == '__main__':
	# starts the web server
	start(MyApp, port=8081)
	

