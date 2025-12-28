import signal
import sys
import os

import remi.gui as gui
from remi.gui import *
from Datapoint_IDs import *
from Config import *
# from LogRoutines import Logger
import Common_Data
from Common_Data import DATAPOINTS_NAME, DATAPOINTS_ID, CATEGORY_NAME, INTERFACE_ID, INTERFACE_NAME
from DB_Routines import get_displaysorted_datapoint_names
from JSEM_Commons import dump, IsNot_NOE, Is_NOE, Load_Images, expandcollapse
from Common_Enums import *
# from JSEM_GUI_classes import JSEM_ChartCont, JSEM_Label, JSEM_Stacked_Bar, JSEM_BalancedGauge, JSEM_Map_Chart, JSEM_Bar_Chart
# from JSEM_GUI_classes import JSEM_Line_Chart, JSEM_Rect, JSEM_Arrow, JSEM_Buffer, JSEM_WeatherIcon
from datetime import datetime
from dateutil.relativedelta import relativedelta

from JSEM_GUI_classes import JSEM_Label, JSEM_Line_Chart, JSEM_Map_Chart, JSEM_Bar_Chart
from LogRoutines import Logger
from remi_addons import ALB_widget
from DataPoint import Datapoint

def Overzicht(DataCont, ChartCont, my_app):
	from GUI_predef_widgets import Heat_widget, E_widget, Hp_widget, E_simple_widget, BarChart_widget
	dp = DATAPOINTS_ID
	screenname = "Overzicht"
	DataCont.empty()
	DataCont.append(Hp_widget(top=10, left=10, height=350, width=350))
	DataCont.append(E_simple_widget(top=10, left=380, height=350, width=350))
	DataCont.append(BarChart_widget(datapoints=[dp[epex_data]], title='Epex (APX) prijzen', top=120, left=630, height=100, width=100))

	# JSEM_WeatherIcon(DataCont, dp[frcst_icoon], top=300, left=10, height=60, width=350, lookahead=8, interval=3, svg_images=False, image_source='/Weathericons')



def Electra(DataCont, ChartCont, my_app):
	from GUI_predef_widgets import E_widget, BarChart_widget, LineChart_widget
	dp = DATAPOINTS_ID
	screenname = "Electra"
	DataCont.empty()
	
	ewidget = E_widget(top=10, left=10, height=450, width=600)

	ewidget.append(LineChart_widget(datapoints=[dp[solar_AC_Power]], title="Solar Power", 
										top='32%', left='3%', height='12%', width='15%', background_color='white'))
	ewidget.append(BarChart_widget(datapoints=[dp[epex_data]], title='Epex (APX) prijs', 
										top='32%', left='83%', height='12%', width='15%', background_color='white'))
	DataCont.append(ewidget)
	
	alb_cont = gui.Container(style='position:absolute;left:650px;top:10px;width:350;height:250px;background:transparent;border-style:none')
	alb_L1 = ALB_widget(name='L1 (Amp)', width=100, height=200, alb_value=dp[L1_max_current].value, alb_state=dp[use_load_balancing].value,
						style='position:absolute;left:0px;border-radius:10px;background-color:lavender')
	alb_L1._data_buffer[-100:] = dp[L1_amps].last100_values
	dp[L1_amps].subscribed_widgets.append(alb_L1)
	alb_L1.onALBvalue_change.connect(lambda *args, **kwargs: dp[L1_max_current].write_value(alb_L1.alb_value))
	
	alb_L2 = ALB_widget(name='L2 (Amp)', width=100, height=200, alb_value=dp[L2_max_current].value, alb_state=dp[use_load_balancing].value,
						style='position:absolute;left:125px;border-radius:10px;background-color:lavender')
	alb_L2._data_buffer[-100:] = dp[L2_amps].last100_values
	dp[L2_amps].subscribed_widgets.append(alb_L2)
	alb_L2.onALBvalue_change.connect(lambda *args, **kwargs: dp[L2_max_current].write_value(alb_L2.alb_value))
	
	alb_L3 = ALB_widget(name='L3 (Amp)', width=100, height=200, alb_value=dp[L3_max_current].value, alb_state=dp[use_load_balancing].value,
						style='position:absolute;left:250px;border-radius:10px;background-color:lavender')
	alb_L3._data_buffer[-100:] = dp[L3_amps].last100_values
	dp[L3_amps].subscribed_widgets.append(alb_L3)
	alb_L3.onALBvalue_change.connect(lambda *args, **kwargs: dp[L3_max_current].write_value(alb_L3.alb_value))
	
	alb_cont.append([alb_L1, alb_L2, alb_L3])
	alb_status = JSEM_Label(alb_cont, dp[ALB_status], left=0, top=210, style='width:350px;height:40px,background:orange',
							show_subcat=False, show_unit=False)
	DataCont.append(alb_cont)

def Warmte(DataCont, ChartCont, my_app):
	from GUI_predef_widgets import Heat_widget, BarChart_widget, LineChart_widget
	dp = DATAPOINTS_ID
	screenname = "Warmte"
	DataCont.empty()
	
	heatwidget = Heat_widget(top=10, left=10, height=450, width=600)
	heatwidget.append(LineChart_widget(datapoints=[dp[frcst_power], dp[Act_Power_01]], title='frcst(groen) vs Act(blauw) power', 
										top='39%', left='35%', height='10%', width='12%', background_color='white'))
	heatwidget.append(BarChart_widget(datapoints=[dp[hp_plan],dp[epex_data]], title='Planning(groen) en epex(blauw) prijs', 
										top='60%', left='72%', height='10%', width='12%', background_color='white'))
	DataCont.append(heatwidget)
	


def Zwembad (DataCont, ChartCont, my_app):
	dp = DATAPOINTS_ID
	try:
		DataCont.empty()

		refx=10
		refy=10
		background_img = Image()
		background_img.css_top = '%spx' % (refy+50)
		background_img.css_left = '%spx' % (refx+50)
		background_img.css_width = '600px'
		background_img.css_height = '500px'
		background_img.css_position = "absolute"
		background_img.attr_src = Load_Images('Pool')
		DataCont.append(background_img)

		lbl_style = {'font-size':'90%', 'txt-width':'100px', 'value-width':'45px'}
		lbl_config = dict(show_name=False, show_subcat=False)

		JSEM_Label(DataCont,dp[pool_overrule], text="NU AAN", left=refx,top=refy, config=lbl_config, style=lbl_style, 
								txt_font_size='1.5em', txt_width='auto', show_value=False, show_unit=False, adopt_dp_signals=False, 
								cond_format=dict(prop='txt-background-color', cond="!=", check_value=0, true="red", false="transparent"))
		JSEM_Label(DataCont,dp[frcst_zoninstraling],text="zon", left=refx+210,top=refy+250, config=lbl_config, style=lbl_style)
		JSEM_Label(DataCont,dp[pool_actual_filterhours],text="filter uren", left=refx+210,top=refy+290, config=lbl_config, style=lbl_style)
		JSEM_Label(DataCont,dp[pool_filter_pump],text="pomp", left=refx+305,top=refy+435, config=lbl_config, style=lbl_style, 
								show_value=False, show_unit=False, adopt_dp_signals=False,
								cond_format=dict(prop='txt-background-color', cond="!=", check_value=0, true="green", false="transparent"))
								
		JSEM_Label(DataCont,dp[pool_use_strategy], text="Optimaal filteren", left=refx+0,top=refy+500, config=lbl_config, style=lbl_style,
								txt_font_size='1.5em', txt_width='auto', show_value=False, show_unit=False, adopt_dp_signals=False,
								cond_format=dict(prop='txt-background-color', cond="!=", check_value=0, true="green", false="transparent"))
								
		
		chart_x = refx+170
		chart_y = refy
		chart_w = 400
		chart_h = 200
		chart = None

		# Laat OF de pool strategy OF de timerstrategy zien (als één van beide tenminste aanstaat)
		if dp[pool_use_strategy].value:
			chart = JSEM_Map_Chart(datapoints=[dp[pool_plan]], dataselection = DataSelection.Week, 
												selecteddate=datetime.now(), chart_title='deze week', 
												columnheaders=["{:02d}".format(x) for x in range(24)], fontsize=8)
		elif dp[pool_use_timer].value:
			chart = JSEM_Map_Chart(datapoints=[dp[pool_timerplan]], dataselection = DataSelection.Week, 
												selecteddate=datetime.now(), chart_title='deze week', 
												columnheaders=["{:02d}".format(x) for x in range(24)], fontsize=8)
		if chart is not None:
			chart.css_position = "absolute"
			chart.css_left = '%spx' % chart_x
			chart.css_top = '%spx' % chart_y
			chart.css_height = '%spx' % chart_h
			chart.css_width = '%spx' % chart_w
			DataCont.append(chart)
	
	except Exception as err:
		Logger.exception(str(err))




	
def Solar(DataCont, ChartCont, my_app):
	dp = DATAPOINTS_ID
	try:
		DataCont.empty()

		refx=10
		refy=10
		
		lbl_style = {
					'font-size':'1.0em', 'width':'150px',
					'txt-font-size':'1.0em', 'txt-width':'50%', 
					'value-font-size':'0.8em', 'value-width':'35%',
					'unit-font-size':'0.5em', 'unit-width':'15%'
					}
		lbl_config = dict(show_name=False, show_subcat=False, show_unit=True)
		
		background_img = Image()
		background_img.css_top = '%spx' % refy
		background_img.css_left = '%spx' % refx
		background_img.css_width = '720px'
		background_img.css_height = '500px'
		background_img.css_position = "absolute"
		background_img.attr_src = Load_Images('Solar')
		DataCont.append(background_img)

		JSEM_Label(DataCont,dp[solar_overrule], text="NU UIT", left=refx,top=refy, config=lbl_config, style=lbl_style, 
								txt_font_size='1.5em', txt_width='auto', show_value=False, show_unit=False, adopt_dp_signals=False, 
								cond_format=dict(prop='txt-background-color', cond="!=", check_value=0, true="red", false="transparent"))
								
		JSEM_Label(DataCont,dp[solar_AC_Power],text="Nu", left=refx+160,top=refy+260, config=lbl_config, style=lbl_style)
		JSEM_Label(DataCont,dp[solar_AC_Energy],text="Vandaag", left=refx+160,top=refy+280, config=lbl_config, style=lbl_style)
		JSEM_Label(DataCont,dp[solar_AC_energy_thismonth],text="Maand", left=refx+160,top=refy+300, config=lbl_config, style=lbl_style)
		JSEM_Label(DataCont,dp[solar_inverter_status],text="Status", left=refx+160,top=refy+320, config=lbl_config, style=lbl_style,
													show_value=False, dp_signal_prop='txt-background-color')
		
		chart_x = refx+160
		chart_y = refy
		chart_w = 300
		chart_h = 200
			
		chart = JSEM_Line_Chart(DataCont, datapoints=[dp[solar_AC_Power]], dataselection=DataSelection.Day, 
											left=chart_x, top=chart_y, height=chart_h, width=chart_w,
											selecteddate=datetime.now(), 
											chart_title='Opgewekt vermogen vandaag', 
											chart_style={'background': 'white', 'plot_background': 'white'})
	except Exception as err:
		Logger.exception(str(err))






def Laadpaal(DataCont, ChartCont, my_app):
	try:
		dp = DATAPOINTS_ID
		# print ('GUI routines, Laadpaal called....')
		DataCont.empty()

		refx=10
		refy=10
		
		lbl_style = {
					'font-size':'1.0em', 'width':'250px',
					'txt-font-size':'1.0em', 'txt-width':'45%', 
					'value-font-size':'0.8em', 'value-width':'20%',
					'unit-font-size':'0.5em', 'unit-width':'10%',
					'input-font-size':'0.8em', 'input-width':'20%'
					}
		lbl_config = dict(show_name=False, show_subcat=False)
		
		background_img = Image()
		background_img.css_top = '%spx' % refy
		background_img.css_left = '%spx' % refx
		background_img.css_width = '930px'
		background_img.css_height = '530px'
		background_img.css_position = "absolute"
		background_img.attr_src = Load_Images('Laadpaal')
		DataCont.append(background_img)
	
		JSEM_Label(DataCont,dp[ev_use_overrule], text="NU AAN", left=refx+0,top=refy, config=lbl_config, style=lbl_style, 
											txt_font_size='1.5em', txt_width='auto', show_value=False, show_unit=False, adopt_dp_signals=False, 
											cond_format=dict(prop='txt-background-color', cond="!=", check_value=0, true="red", false="transparent"))
											
		JSEM_Label(DataCont,dp[ev_ACpower], text='Power', left=refx+97, top=refy+120, config=lbl_config, style=lbl_style, txt_width='30%')
		
		JSEM_Label(DataCont,dp[act_session_energy], text='Sessie', left=refx+97, top=refy+235, config=lbl_config, style=lbl_style, txt_width='30%')
		
		JSEM_Label(DataCont,dp[ev_mode3_state], text='M3 Status', left=refx+600, top=refy+300, config=lbl_config, style=lbl_style, 
											show_unit=False, enable_RW=False,)
											
		JSEM_Label(DataCont,dp[ev_car_connected], text="conn", left=refx+600,top=refy+320,config=lbl_config, style=lbl_style, txt_width='60px', 
											adopt_dp_signals=False, show_value=False,
											cond_format = dict(prop='txt-background-color', cond="!=", check_value=0, true="red", false="grey"))
											
		JSEM_Label(DataCont,dp[ev_pwm_signal], text="comm", left=refx+600+60,top=refy+320,config=lbl_config, style=lbl_style, txt_width='60px',
											adopt_dp_signals=False, show_value=False, 
											cond_format = dict(prop='txt-background-color', cond="!=", check_value=0, true="red", false="grey"))
											
		JSEM_Label(DataCont,dp[ev_car_charging], text="charge", left=refx+600+2*60,top=refy+320,config=lbl_config, style=lbl_style, txt_width='60px',
											adopt_dp_signals=False, show_value=False,
											cond_format = dict(prop='txt-background-color', cond="!=", check_value=0, true="red", false="grey"))

		JSEM_Label(DataCont,dp[ev_use_strategy], text="Optimaal Laden", left=refx+0,top=refy+500, config=lbl_config, style=lbl_style, 
											txt_font_size='1.5em', txt_width='auto', show_value=False, show_unit=False, adopt_dp_signals=False, 
											cond_format=dict(prop='txt-background-color', cond="!=", check_value=0, true="green", false="transparent"))

		JSEM_Label(DataCont,dp[ev_act_kmrange], text="Actieradius", left=refx+320,top=refy+500, config=lbl_config, style=lbl_style)

											
		
		
		map_x = 220
		map_y = 10
		map_w = 260
		map_h = 160
		
		load_map1 = JSEM_Bar_Chart(datapoints=[dp[ev_plan]], dataselection = DataSelection.Day, 
											selecteddate=datetime.now(), chart_title='Vandaag', always_refresh=True)
		load_map1.css_position = "absolute"
		load_map1.css_left = '%spx' % map_x
		load_map1.css_top = '%spx' % map_y
		load_map1.css_height = '%spx' % map_h
		load_map1.css_width = '%spx' % map_w
		DataCont.append(load_map1) 
		

		load_map2 = JSEM_Bar_Chart(datapoints=[dp[ev_plan]], dataselection = DataSelection.Day, 
											selecteddate=datetime.now() + relativedelta(days=1), chart_title='Morgen', always_refresh=True)
		load_map2.css_position = "absolute"
		load_map2.css_left = '%spx' % (map_x + map_w - 60)
		load_map2.css_top = '%spx' % map_y
		load_map2.css_height = '%spx' % map_h
		load_map2.css_width = '%spx' % map_w
		DataCont.append(load_map2) 
		
		load_map3 = JSEM_Bar_Chart(datapoints=[dp[ev_plan]], dataselection = DataSelection.Day, 
											selecteddate=datetime.now() + relativedelta(days=2), chart_title='Overmorgen', always_refresh=True)
		load_map3.css_position = "absolute"
		load_map3.css_left = '%spx' % (map_x + map_w + map_w - 120)
		load_map3.css_top = '%spx' % map_y
		load_map3.css_height = '%spx' % map_h
		load_map3.css_width = '%spx' % map_w
		DataCont.append(load_map3) 

	except Exception as err:
		Logger.exception(str(err))
	

def E_meter(DataCont, ChartCont, my_app):
	dp = DATAPOINTS_ID
	DataCont.empty()

def Houtkachel(DataCont, ChartCont, my_app):
	dp = DATAPOINTS_ID
	DataCont.empty()

def Systeem(DataCont, ChartCont, my_app):
	dp = DATAPOINTS_ID
	DataCont.empty()

def Woning(DataCont, ChartCont, my_app):
	dp = DATAPOINTS_ID
	DataCont.empty()
	
	
	
def show_all(datacont, ChartCont, cat_name, my_app):
	try:
		datacont.empty()
		cat_id = Common_Data.CATEGORY_NAME[cat_name].ID
		# dimensioning variables
		height = 12
		# naam = 170
		# subcat = 100
		# value = 80
		# unit = 30
		# inp = 50
		total_width = 430
		row_sep = height + 8
		subcat_xtra_sep = 12
		col_sep = total_width + 50
		maxrows=30
		
		lbl_style = {'width':f'{total_width}px', 'height':f'{height}px'}
		lbl_config = {}
		
		x = 10
		y = 10 - row_sep
		rowteller=0
		# print ("show_all...cat_id=", cat_id)
		# dp_names=get_displaysorted_datapoint_names(cat_id)
		for sub_cat, names in get_displaysorted_datapoint_names(cat_id).items():
			rowteller += 1
			if rowteller + len(names) > maxrows:
				y = 10
				x = x + col_sep
				rowteller = 1
			else:
				y = y + subcat_xtra_sep

			for dp_name in names:
				dp=DATAPOINTS_NAME[dp_name]
				data_label=JSEM_Label(datacont,dp,left=x,top=y, config=lbl_config, style=lbl_style)
				rowteller += 1
				if rowteller > maxrows:
					y = 10
					x = x + col_sep
					rowteller = 1
				else:
					y = y + row_sep
				
	except Exception as err:
		Logger.exception(str(err))
		

def Instellingen(DataCont:Container, ChartCont:VBox, my_app):

	def rebootbutton_clicked(*args, **kwargs):
		def confirm_clicked(*args, **kwargs):
			Logger.info("Reboot requested")
			# only reboot on the raspberry Pi, not on the development system
			if ENVIRONMENT == Environment.Productie:
				os.kill(os.getpid(), signal.SIGUSR2)
			else:
				Logger.info("Reboot cancelled... this is not a production environment!..")

		def cancel_clicked(*args, **kwargs):
			Logger.info("Reboot cancelled")
			
		message = "Weet u ABSOLUUT zeker dat u de computer wilt restarten?"
		dialog = gui.GenericDialog("Waarschuwing!!!" + ": Druk op OK om aan tegeven dat u het risico begrijpt!", message=message, width='330px')
		dialog.css_font_size="16px"
		dialog.confirm_dialog.connect(confirm_clicked)
		dialog.cancel_dialog.connect(cancel_clicked)
		dialog.show(Common_Data.MAIN_INSTANCE)

		
	def stopappbutton_clicked(*args, **kwargs):
		def confirm_clicked(*args, **kwargs):
			Logger.info("Application stop requested")
			my_app.close()
			# print(my_app)
			# waitkey()
		
		# Common_Data.MAIN_INSTANCE.close()
			# os.kill(os.getpid(), signal.SIGUSR1)
			
		def cancel_clicked(*args, **kwargs):
			Logger.info("Application stop cancelled")
			
		message = "Weet u ABSOLUUT zeker dat u de applicatie wilt stoppen?"
		dialog = gui.GenericDialog("Waarschuwing!!!", message=message, width='330px')
		dialog.css_font_size="16px"
		dialog.confirm_dialog.connect(confirm_clicked)
		dialog.cancel_dialog.connect(cancel_clicked)
		dialog.show(Common_Data.MAIN_INSTANCE)

	def categorybutton_clicked(selected_button, **kwargs):
		show_all(DataCont, ChartCont, selected_button.text, my_app)
		
	def interf_pollbutton_clicked(poll_btn, interf):
		if interf.pollstate == PollState.Polling:
			interf.stop_polling()
		elif interf.pollstate == PollState.Not_Polling:
			interf.start_polling()

	def interf_connbutton_clicked(conn_button, interf):
		if interf.connstate == ConnState.Connected:
			interf.disconnect()
		elif interf.connstate == ConnState.DisConnected:
			interf.connect()
			
	def interf_poll_Q_button_clicked(pollQbutton, interf):
		if interf.POLLQ_widget is None:
			pollQ_widget = VBox(style='width:80%; height:95%; overflow:auto; '\
										'align-items:flex-start; justify-content:flex-start; flex-wrap:nowrap; '\
								  		'margin:5px; font-family:Courier New; font-size:15px')
			ChartCont.append(pollQ_widget, interf.name + "_pollQ")
			interf.POLLQ_widget = pollQ_widget
			interf.update_POLLQ_widget()
			pollQbutton.css_background_color = "red"
		else:
			interf.POLLQ_widget = None
			try:
				ChartCont.remove_child(ChartCont.get_child(interf.name + "_pollQ"))
			except:
				pass
			pollQbutton.css_background_color = "grey"
			
			
			
	def interf_monitorbutton_clicked(monitorbutton, pausebutton, interf):
		if interf.MON_widget is None:
			if interf.display_format.upper() in ['ASCII', 'TEXT']:
				mon_widget = VBox(style='width:80%; height:95%; overflow-x:hidden; overflow-y:auto; '\
										'align-items:flex-start; justify-content:flex-start; flex-wrap:nowrap; '\
								  		'margin:5px; font-family:Courier New; font-size:15px')
			elif interf.display_format.upper() in ['HEX']:
				mon_widget = Container(style=	'width:80%; height:95%; overflow:auto; '
												'margin:5px; font-family:Courier New; font-size:15px')
				
			ChartCont.append(mon_widget, interf.name + "_monitor")
			mon_widget.attributes["is_updating"]=True
			interf.MON_widget = mon_widget
			monitorbutton.css_background_color = "red"
		else:
			try:
				ChartCont.remove_child(ChartCont.get_child(interf.name + "_monitor"))
			except:
				pass
			interf.MON_widget = None
			monitorbutton.css_background_color = "grey"
			pausebutton.css_background_color="grey"
			pausebutton.text="pause"

	def interf_pausebutton_clicked(pausebutton, interf):
		try:
			mon_widget = ChartCont.get_child(interf.name + "_monitor")
			if mon_widget.attributes["is_updating"]:
				mon_widget.attributes["is_updating"]=False
				pausebutton.css_background_color="red"
				pausebutton.text="play"
			else:
				interf.flush_MON_buffer()
				mon_widget.attributes["is_updating"]=True
				pausebutton.css_background_color="grey"
				pausebutton.text="pause"
		except:
			pausebutton.css_background_color="grey"
			pausebutton.text="pause"
			
		
		
		
	try:
		DataCont.empty()
		
		topcont = Container(style='position:absolute; top:0px; left:0px; height:100%; width:84vw; font-size:0.8em; background-color:transparent')
		
		# Eerste een knop voor iedere categorie
		CatHbox = HBox(style='position:absolute; top:0%; left:0%; width:100%; height:20%; '\
							 'justify-content:flex-start; align-items:flex-start; flex-wrap:wrap; background-color:transparent')
		for catname in CATEGORY_NAME:
			btn1 = Button(catname, style='width:10%; height:25%; margin:10px')
			btn1.onclick.connect(categorybutton_clicked)
			CatHbox.append(btn1, btn1.text)
		topcont.append(CatHbox)
		
		# Dan een groep knoppen voor iedere interface, Connect/ Poll en PollQ /Monitor en Pause
		IntfVbox = VBox(style='position:absolute; top:20%; left:0%; width:100%; height:70%; '\
							  'justify-content:space-around; align-items:flex-start; background-color:transparent')
		# set_css_defaults(IntfVbox, width="100%", height="45%")
		
		if Common_Data.DB_STORE is not None:
			DB_Engine = Common_Data.DB_STORE
			DBSubHbox = HBox(style='width:90%; height:8%; background-color:transparent')
			btn_style = 'width:10%; height:100%'
			lbl = Label(DB_Engine.name, style=btn_style)
			DBSubHbox.append(lbl)
			DB_load_widget = Progress(value=0, max=100, style='width:50%; height:100%')
			Common_Data.DB_STORE.status_widget = DB_load_widget
			DBSubHbox.append(DB_load_widget)
			IntfVbox.append((DBSubHbox))
		
		for intfname in INTERFACE_NAME:
			intf = INTERFACE_NAME[intfname]
			IntfSubHbox = HBox(style='width:90%; height:8%; background-color:transparent')
			btn_style = 'width:10%; height:100%'
			
			lbl1 = Label(intf.name, style=btn_style)
			IntfSubHbox.append(lbl1)
			#------------------------Connect/DisConnect Button
			btn1 = Button(style=btn_style)
			intf.connwidget=btn1
			btn1.onclick.connect(interf_connbutton_clicked, intf)
			IntfSubHbox.append(btn1)
			
			#------------------------Polling/Poll_Q Buttons
			btn2A = Button(style=btn_style)
			intf.pollwidget=btn2A
			btn2A.onclick.connect(interf_pollbutton_clicked, intf)
			IntfSubHbox.append(btn2A)

			btn2B = Button("Poll_Q", style=f'{btn_style}; background-color:grey')
			btn2B.onclick.connect(interf_poll_Q_button_clicked, intf)
			IntfSubHbox.append(btn2B)
			
			#------------------------Monitor/Pause Buttons
			btn3A = Button("monitor", style=f'{btn_style}; background-color:grey')
			btn3B = Button("pause", style=f'{btn_style}; background-color:grey')
			btn3A.onclick.connect(interf_monitorbutton_clicked, btn3B, intf)
			btn3B.onclick.connect(interf_pausebutton_clicked, intf)
			IntfSubHbox.append([btn3A, btn3B])
			
			# kijk of er al een monitor container actief is voor deze interface en sync de knopkleuren daarmee
			if intf.MON_widget != None:
				btn3A.css_background_color = "red"
				if intf.MON_widget.attributes["is_updating"] == False:
					btn3B.css_background_color = "red"
					btn3B.text="play"

			#------------------------Receiver/Sender and Send_Q indicators
			recvlbl = Label("Receive", style=f'{btn_style}; background-color:grey')
			intf.recvwidget = recvlbl
			sendlbl = Label("Send", style=f'{btn_style}; background-color:grey')
			intf.sendwidget = sendlbl
			IntfSubHbox.append(recvlbl)
			IntfSubHbox.append(sendlbl)
		
			IntfVbox.append(IntfSubHbox)
			# # initialise the connection, poll, receive and send indicators and colors
			intf.upd_stats()
			intf.upd_indicators()


		topcont.append(IntfVbox)
		
		# Dan een groep knoppen voor de applicatie en het systeem: Stop (applicatie) en Reboot (het systeem)
		CntrlHbox = HBox(style = 'position:absolute; top:90%; left:0%; width:90%; height:10%; background-color:transparent; justify-content:flex-end')
		# Een button om te rebooten
		btn1 = Button("Reboot", style='width:10%; height:50%; margin:10px')
		btn1.onclick.connect(rebootbutton_clicked)
		CntrlHbox.append(btn1, "rebootbutton")

		# Een button om de app te stoppen, geen reboot
		btn2 = Button("Stop", style='width:10%; height:50%; margin:10px')
		btn2.onclick.connect(stopappbutton_clicked)
		CntrlHbox.append(btn2, "stopappbutton")
		
		topcont.append(CntrlHbox)
		DataCont.append(topcont)

	except Exception as err:
		Logger.exception(str(err))
	
	
def set_css_defaults(widget, *args, **kwargs):
	try:
		widget.css_position = "relative" if not "position" in kwargs else kwargs["position"]
		widget.css_width ="10%" if not "width" in kwargs else kwargs["width"]
		widget.css_height ="10%" if not "height" in kwargs else kwargs["height"]
		widget.css_align_items ="center" if not "align" in kwargs else kwargs["align"]
		widget.css_flex_wrap ="wrap" if not "wrap" in kwargs else kwargs["wrap"]
		widget.css_justify_content ="space-around" if not "spacing" in kwargs else kwargs["spacing"]
		# widget.css_margin = "5px" if not "margin" in kwargs else kwargs["margin"]
		
		if "fontsize" in kwargs: widget.css_font_size = kwargs["fontsize"]
		if "bgcolor" in kwargs: widget.css_background_color = kwargs["bgcolor"]
		if "color" in kwargs: widget.css_color = kwargs["color"]
	except Exception as err:
		Logger.exception(str(err))


	


def main(args):
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
