#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Pygal_LineBar.py
#  
#  Copyright 2023  <pi@raspberrypi>
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
from remi import start, App
import remi.server
import os
import time
import pygal 
from pygal.style import Style
from datetime import datetime


 
class PyGal(gui.Svg):
	def set_content(self, chart):
		self.data = chart.render()
		self.add_child("chart", self.data)

class LineBar(pygal.Line, pygal.Bar):
	def __init__(self, config=None, **kwargs):
		super(LineBar, self).__init__(config=config, **kwargs)
		self.y_title_secondary = kwargs.get('y_title_secondary')
		self.plotas = kwargs.get('plotas', 'line')

	def _make_y_title(self):
		super(LineBar, self)._make_y_title()
		
		# Add secondary title
		if self.y_title_secondary:
			yc = self.margin_box.top + self.view.height / 2
			xc = self.width - 10
			text2 = self.svg.node(
				self.nodes['title'], 'text', class_='title',
				x=xc,
				y=yc
			)
			text2.attrib['transform'] = "rotate(%d %f %f)" % (
				-90, xc, yc)
			text2.text = self.y_title_secondary

	def _plot(self):
		for i, serie in enumerate(self.series, 1):
			plottype = self.plotas

			raw_series_params = self.svg.graph.raw_series[serie.index][1]
			if 'plotas' in raw_series_params:
				plottype = raw_series_params['plotas']
				
			if plottype == 'bar':
				self.bar(serie)
			elif plottype == 'line':
				self.line(serie)
			else:
				raise ValueError('Unknown plottype for %s: %s'%(serie.title, plottype))

		for i, serie in enumerate(self.secondary_series, 1):
			plottype = self.plotas

			raw_series_params = self.svg.graph.raw_series[serie.index][1]
			if 'plotas' in raw_series_params:
				plottype = raw_series_params['plotas']

			if plottype == 'bar':
				self.bar(serie, True)
			elif plottype == 'line':
				self.line(serie, True)
			else:
				raise ValueError('Unknown plottype for %s: %s'%(serie.title, plottype))


class MyApp(App):
	def main(self):
		# plot a dashboard for month time intervals:
		# 1) number of open (backlog) tickets at that time
		# 2) number of new tickets in interval
		# 3) number of tickets closed in interval
		# 4) in seperate graph look at turnaround time for tickets resolved
		#    between X and X+T
		# 5) in seperate graph look at first contact time for tickets resolved
		#    between X and X+T
		
		data = [('Apr 10', 20, 30,  5, 20, 3.2),
				('May 10', 45, 33,  5, 20, 1.7),
				('Jun 10', 73, 30, 20, 10, 2.5),
				('Jul 10', 83, 12, 37, 28, 3.7),
				('Aug 10', 58, 27, 23, 18, 1.9),
				('Sep 10', 62, 10, 23, 11, 3.8),
				('Oct 10', 49, 17, 29, 31, 3.6),
				('Nov 10', 31, 27, 23, 13, 1.7),
				('Dec 10', 35, 17, 32, 44, 0.9),
				('Jan 11', 20, 30,  5, 24, 1.7),
				('Feb 11', 45, 33,  5, 20, 8.6),
				('Mar 11', 73, 30, 20, 10, 3.7),
				('Apr 11', 83, 12, 37, 28, 2.1),]
		
		config = pygal.Config()
		
		# Customize CSS
		# Almost all font-* here needs to be !important. Base styles include
		#  the #custom-chart-anchor which gives the base setting higher
		#  specificy/priority.  I don't know how to get that value so I can
		#  add it to the rules. I suspect with code reading I could set some
		#  of these using pygal.style....
		
		# make axis titles size smaller
		config.css.append('''inline:
		  g.titles text.title {
			font-size: 12px !important;
		  }''')
		# Make plot_title larger and bold
		# (override size by placing this later with !important)
		config.css.append('''inline:
		  g.titles text.title.plot_title {
			font-size: 18px !important;
			font-weight: bold;
		  }''')
		# shrink legend label text
		config.css.append('''inline:
		  g.legend text {
			font-size: 10px !important;
		  }''')
		# move line and points for turnround time plot to middle of the
		# three related bars.
		# Don't use just g.serie-3 as that gets the value labels as well.
		# 12.88 is a magic number. Given the bar width(w) and number of bars (n=3),
		#    calculate as: (w*n/2)+(w/2)
		config.css.append('''inline:
		  g.plot.overlay g.serie-3, g.graph g.serie-3 {
			transform: translate(12.88px,0);
		  }''')
		# Turn off printed values, I only want it for turnaround time
		config.css.append('''inline:
		  g.text-overlay text.value {
			display: none;
		  }''')
		# turn on and style printed values for turnaround time and move it above
		# points. Translate values are all magic, no formula.
		config.css.append('''inline:
		  g.text-overlay g.serie-3 text.value {
			display: block;
			text-anchor: end;
			transform: translate(-3pt,-11pt);
		  }''')
		# make guide lines lighter, clashes with printed values.
		config.css.append('''inline:
		  g.guides path.guide.line{
			stroke: rgb(0,0,0,0.25) !important;
		  }''')
		# If we hover over the label or the line, make line full black.
		config.css.append('''inline:
		  g.guides:hover path.guide.line {
			stroke: rgb(0,0,0,1) !important;
		  }''')
		
		# Would prefer legend_at_bottom = False. So legend is next to correct
		# axis for plot. However this pushes the y_title_secondary away from
		# the axis.  To compensate, set legend_at_bottom_columns to 3 so first
		# row is left axis and second row is right axis. With second axis plot
		# showing printed values, this should reduce confusion.
		
		# Make range and secondary range integer mutiples so I end up with
		# integer values on both axes.
		
		style=pygal.style.DefaultStyle(value_font_size=8)
		
		chart = LineBar(config,
						width=600,
						height=300,
						title="Tracker Dashboard",
						x_title="Month",
						y_title='Count',
						y_title_secondary='Days',
						legend_at_bottom=True,
						legend_at_bottom_columns=3,
						legend_box_size=10,
						range = (0,90), # Without this the bars start below the bottom axis
						secondary_range=(0,45),
						x_label_rotation=45,
						print_values=False,
						print_values_position='top',
						style=style,
						)
		
		chart.x_labels = [ x[0] for x in data ]
		chart.x_labels.append("") # without this the final bars overlap the secondary axis
		
		chart.add("backlog",[ x[1] for x in data] , plotas='bar')
		chart.add("new",[ x[2] for x in data] , plotas='bar')
		chart.add("resolved", [ x[3] for x in data] , plotas='bar')
		chart.add("turnaround time", [ x[4] for x in data] , plotas='line', secondary=True)
		
		# chart.render_to_file("plotdash_pygal.svg", pretty_print=True)


		#creating a container VBox type, vertical (you can use also HBox or Widget)
		self.main_container = gui.VBox(width=500, height=500)
		self.pygal_container = PyGal(width=500, height=500)
		self.pygal_container.set_content(chart)

		self.main_container.append(self.pygal_container)
		
		# returning the root widget
		return self.main_container


if __name__ == "__main__":
	# starts the webserver
	start(MyApp, address='127.0.0.1', port=8081, start_browser=True)


