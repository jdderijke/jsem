
import threading
import time
from Datapoint_IDs import *
from Common_Enums import *
import Common_Data
from LogRoutines import Logger
from Common_Data import DATAPOINTS_ID, DATAPOINTS_NAME
from datetime import datetime

from Epex_Leba_data_download import get_epex_leba_data, HEADERS, PROVIDERS
from HP_Optimizer import make_hp_plan, predict_heatingpower
from MeteoServer_Forecast import get_meteoserver_forecast


# from dateutil.relativedelta import relativedelta

class JSEM_Rule(object):
	def __init__(self, *args, **kwargs):
		self.name = kwargs.get("name", "Unnamed....")
		self.rule = kwargs.get("rule", None)
		if self.rule is None: 
			Logger.info("%s-- No strategy routine specified for this rule object, rule ignored" % self.name)
			return
		self.interval = kwargs.get("interval", 60)
		self.startup_delay = kwargs.get("startup_delay", 120)
		
		
		if kwargs.get("start", False): self.start_rule()
		
	def start_rule(self):
		self.rule_timer = threading.Timer(self.startup_delay, self.rule_timer_callback)
		# have the timer run as daemon thread....
		self.rule_timer.daemon = True
		self.rule_timer.start()
		self.__rule_timer_running = True
		Logger.info (self.name + "-- Strategy starts in " + str(self.startup_delay) + "s, with interval: "+ str(self.interval) + "s.")
		
	def restart_rule(self):
		self.rule_timer = threading.Timer(self.interval, self.rule_timer_callback)
		# have the timer run as daemon thread....
		self.rule_timer.daemon = True
		self.rule_timer.start()
		self.__rule_timer_running = True
		
	def rule_timer_callback(self):
		self.__rule_timer_running = False
		self.rule_timer = None
		self.rule()
		Logger.debug("%s-- Strategy routine called...." % self.name)
		self.restart_rule()
		
	def stop_rule(self):
		if self.rule_timer is not None: 
			self.rule_timer.cancel()
			# wait until the timer thread has stopped
			self.rule_timer.join()
			self.__rule_timer_running = False
			self.rule_timer = None
		Logger.info ("%s-- Strategy stopped." % self.name)


def get_weather_frcst(*args, **kwargs):
	Logger.info("Running get_meteoserver_forecast....")
	result = get_meteoserver_forecast(running_standalone=False,
									  location='8141PR',
									  make_csv=True,
									  store_in_db=True)


def get_epex_data(*args, **kwargs):
	Logger.info("Running get_epex_leba_data.... for electricity")
	for provider in PROVIDERS:
		header = HEADERS['electricity']
		if get_epex_leba_data(header=header, provider=provider, start_date=datetime.now(),
							  end_date=datetime(2099,12,31,0,0,0),
							  make_csv=True, store_in_db=True, incl_vat=False):
			break

def get_leba_data(*args, **kwargs):
	Logger.info("Running get_epex_leba_data.... for gas")
	for provider in PROVIDERS:
		header = HEADERS['gas']
		if get_epex_leba_data(header=header, provider=provider, start_date=datetime.now(),
							  end_date=datetime(2099,12,31,0,0,0),
							  make_csv=True, store_in_db=True, incl_vat=False):
			break


def optimizer(*args, **kwargs):
	"""
	Runs a predictor on the heating power needed based on the model and weather forecast
	Then runs an algorithm to find the best way to provide in this power based on EPEX prices and costs
	"""
	Logger.info("predict_heatingpower started by JSEM_rules.optimizer....")
	power_forecast = predict_heatingpower(store_in_db=True)
	Logger.info("make_hp_plan started by JSEM_rules.optimizer....")
	make_hp_plan(power_forecast=power_forecast, store_in_db=True)




def warmtepomp_strat_1(*args, **kwargs):
	'''
	Door de HP_optimizer wordt een draaiplan gemaakt voor de warmtepomp.
	Deze rule kijkt in dat plan en start de warmtepomp wanneer hij volgens het plan moet lopen en stopt hem wanneer hij volgens het plan
	moet stoppen
	'''
	from DB_Routines import get_value_from_database
	Logger.debug("Running warmtepomp_strat_1....")
	
	use_strategy = DATAPOINTS_ID[use_hp_strategy].value
	
	buftemp_setp = DATAPOINTS_ID[buf_temp_setp].value
	hpboost_setp = DATAPOINTS_ID[hp_boost_setp].value
	hpnorm_setp = DATAPOINTS_ID[hp_normal_setp].value
	
	vloerflowtemp_setp = DATAPOINTS_ID[vloer_flow_temp_setp].value
	vloerboost_incr = DATAPOINTS_ID[vloer_boost_incr].value
	
	# Logger.info(f'buf_temp_setp:{buftemp_setp}, hp_boost_setp:{hpboost_setp}, hp_normal_setp:{hpnorm_setp}')

	overrule_hp = DATAPOINTS_ID[use_hp_overrule].value
	
	# Get the plan for this hour!
	run_hp = DATAPOINTS_ID[hp_plan].value
	
	ALB_limit = DATAPOINTS_ID[hp_ALB_limit]
	# print('ALB_limit.value', type(ALB_limit.value))
	# print('ALB_limit.initial_value', type(ALB_limit.initial_value))
	# print('ALB_limit.last_value', type(ALB_limit.last_value))

	cur_ALB_limit = ALB_limit.value
	# initial_ALB_limit = ALB_limit.datatype(ALB_limit.initial_value)
	initial_ALB_limit = ALB_limit.initial_value
	
	
	if cur_ALB_limit <  initial_ALB_limit:
		# we voorkomen altijd dat de hp kan starten in boostbedrijf (kan nog steeds starten in normaal bedrijf)
		run_hp = False
		overrule_hp = False

	if (use_strategy and run_hp) or overrule_hp:
		if buftemp_setp != hpboost_setp:
			Logger.info (f"BOOST ON--buf_temp_setp naar {hpboost_setp}, vloer_flow_temp_setp naar {vloerflowtemp_setp+vloerboost_incr}")
			# write new boost setpoints to system
			DATAPOINTS_ID[buf_temp_setp].write_value(nwvalue=hpboost_setp)
			DATAPOINTS_ID[sl_temp_corr].write_value(nwvalue=vloerboost_incr)
			# During loading keep the circulationpump running to achieve maximal mixing in the buffer
			DATAPOINTS_ID[circ_pomp_hp_buf].write_value(nwvalue=True)
	else:
		if abs(buftemp_setp - hpnorm_setp) > 0.2:
			# Om jutteren te voorkomen een kleine hysteresis gebruiken
			Logger.info (f"BOOST OFF--buf_temp_setp aangepast naar {hpnorm_setp}, vloer_sl_temp_corr reset to 0.0")
			DATAPOINTS_ID[sl_temp_corr].write_value(nwvalue=0.0)
			DATAPOINTS_ID[buf_temp_setp].write_value(nwvalue=hpnorm_setp)
			# Normally we don't want mixing in the buffer when it unloads
			DATAPOINTS_ID[circ_pomp_hp_buf].write_value(nwvalue=False)


	
	

def laadpaal_rule_1(*args, **kwargs):
	'''
	Deze rule kijkt of de startegy gebruikt moet worden, en zo ja of er volgens het ev_plan OP of AFgeschakeld moet worden
	Deze rule kijkt verder naar de actuele epex prijs en vergelijkt die met de laadpaal grenswaarde.
	Wanneer de actuele prijs onder de grenswaarde is, wordt de laadpaal OP geschakeld (max amps)
	Wanneer de actuele prijs boven de grenswaarde komt, wordt de laadpaal AFgeschakeld (min amps).
	'''
	dp = DATAPOINTS_ID
	Logger.debug("Running laadpaal_rule_1....")
	use_strategy = bool(DATAPOINTS_ID[ev_use_strategy].value)
	use_overrule = bool(DATAPOINTS_ID[ev_use_overrule].value)

	ev_curr_limits = (DATAPOINTS_ID[ev_ALB_limit_L1].value, DATAPOINTS_ID[ev_ALB_limit_L2].value, DATAPOINTS_ID[ev_ALB_limit_L3].value)
	ev_init_limits = (DATAPOINTS_ID[ev_ALB_limit_L1].initial_value, DATAPOINTS_ID[ev_ALB_limit_L2].initial_value, DATAPOINTS_ID[ev_ALB_limit_L3].initial_value)
	ev_curr_use = (DATAPOINTS_ID[ev_current_L1].value, DATAPOINTS_ID[ev_current_L2].value, DATAPOINTS_ID[ev_current_L3].value)

	# Als we alb limieten kunnen zetten per fase in de laadpaal, dan moet hier nog e.e.a. aangepast worden
	ALB_limit = min(ev_curr_limits)

	# De alb limit beperkt de maximale setpoint voor de laadpaal
	max_allowed_setpoint = min(dp[EV_max_stroom].value, ALB_limit)
	
	# Logger.info('use_strategy: %s, evplan: %s, epex_prijs: %s, epex_grens: %s' % (use_strategy,evplan.value,epex_prijs.value,epex_grens.value))
	# allereerst wordt aan de strategy gevraagd of de laadpaal AAN of UIT moet
	if (use_strategy and dp[ev_plan].value):
		if dp[ev_curr_setpoint].value != max_allowed_setpoint:
			Logger.info("ev_plan: Laadpaal schakelt naar maximale toegestane laadstroom...")
			dp[ev_curr_setpoint].write_value(nwvalue=max_allowed_setpoint)
			return
	elif dp[epex_data].value is not None and (dp[epex_data].value <= dp[ev_epex_grensprijs].value):
		if dp[ev_curr_setpoint].value != max_allowed_setpoint:
			Logger.info("Epex grenswaarde onderschreden: Laadpaal schakelt naar maximale toegestane laadstroom...")
			dp[ev_curr_setpoint].write_value(nwvalue=max_allowed_setpoint)
			return
	elif use_overrule:
		if dp[ev_curr_setpoint].value != max_allowed_setpoint:
			Logger.info("EV_overrule: Laadpaal schakelt naar maximale toegestane laadstroom...")
			dp[ev_curr_setpoint].write_value(nwvalue=max_allowed_setpoint)
			return
	else:
		if dp[ev_curr_setpoint].value != dp[EV_min_stroom].value:
			Logger.info("Laadpaal schakelt af...")
			dp[ev_curr_setpoint].write_value(nwvalue=dp[EV_min_stroom].value)
		
	


def zwembad_rule_1(*args, **kwargs):
	'''
	Deze rule kijkt allereerst naar de ALB (Active Load Balancing), indien nodig schakelt hij UIT en indien mogelijk (en gewenst
	door de poolplanning of timerplanning of epex prijs) schakelt hij AAN
	
	Deze rule kijkt of de strategies (2) gebruikt moet worden, en zo ja of er volgens het pool_plan of pool_timerplan AAN geschakeld moet worden
	Deze rule kijkt verder naar de actuele epex prijs en vergelijkt die met de zwembad grenswaarde.
	Wanneer de actuele prijs onder de grenswaarde is, wordt de pomp AANgeschakeld
	Wanneer de actuele prijs boven de grenswaarde komt, wordt de pomp UITgeschakeld
	'''
	from DB_Routines import get_value_from_database
	from JSEM_Commons import this10min_timestamp
	
	Logger.debug("Running zwembad_rule_1....")
	use_strategy = bool(DATAPOINTS_ID[pool_use_strategy].value)
	use_timer = bool(DATAPOINTS_ID[pool_use_timer].value)
	use_overrule = bool(DATAPOINTS_ID[pool_overrule].value)

	epex_prijs = DATAPOINTS_ID[epex_data]
	epex_grens = DATAPOINTS_ID[pool_epex_grens]
	poolplan = DATAPOINTS_ID[pool_plan]
	timerplan = DATAPOINTS_ID[pool_timerplan]
	filterpump = DATAPOINTS_ID[pool_filter_pump]
	
	pool_curr_limits = (DATAPOINTS_ID[pool_ALB_limit_L1].value, DATAPOINTS_ID[pool_ALB_limit_L2].value, DATAPOINTS_ID[pool_ALB_limit_L3].value)
	pool_init_limits = (DATAPOINTS_ID[pool_ALB_limit_L1].initial_value, DATAPOINTS_ID[pool_ALB_limit_L2].initial_value, DATAPOINTS_ID[pool_ALB_limit_L3].initial_value) 
	pool_curr_use = (DATAPOINTS_ID[pool_current_L1].value, DATAPOINTS_ID[pool_current_L2].value, DATAPOINTS_ID[pool_current_L3].value)
	
	if all([a==b for a,b in zip(pool_curr_limits, pool_init_limits)])==False:
		# Kijk eerst of de actuele ALB_limits afwijken van de initiele ALB limits, voor elke fase
		# Als dat zo is schakel dan de pool UIT (er kan geen stroom/vermogen worden geregeld, alleen AAN/UIT)
		if filterpump.value: 
			Logger.info("Pool_ALB: Switching filterpump OFF for ALB reasons...")
			filterpump.write_value(nwvalue=False)
	# Als ALB geen issue is wordt daarna aan alle strategies en rules gevraagd of de pool AAN moet, zo nee dan gaat ie UIT
	elif (use_strategy and poolplan.value):
		# De eerste strategy is de pool_strategy die in een poolplan wordt opgeslagen door de Pool_Optimizer die via crontab regelmatig loopt
		if not filterpump.value: 
			Logger.info("Pool_strategy: Switching filterpump from OFF to ON...")
			filterpump.write_value(nwvalue=True)
	elif (use_timer and timerplan.value):
		# De tweede strategy is een simpele pool_timer die eveneens door de Pool_Optimizer wordt gemaakt
		if not filterpump.value: 
			Logger.info("Pool_timer: Switching filterpump from OFF to ON...")
			filterpump.write_value(nwvalue=True)
	elif epex_prijs.value is not None and (epex_prijs.value <= epex_grens.value):
		# De derde, een rule, kijkt of de epex_prijs onder een instelbare grenswaarde is, zo ja dan gaat de pool AAN
		if not filterpump.value: 
			Logger.info("Pool_epex_grens: Switching filterpump from OFF to ON...")
			filterpump.write_value(nwvalue=True)
	elif use_overrule:
		# En als bovenstaande allemaal niet aan de orde is dan kan middels een overrule (rule) de pool AAN worden gedwongen
		if not filterpump.value: 
			Logger.info("Pool_overrule: Switching filterpump from OFF to ON...")
			filterpump.write_value(nwvalue=True)
	else:
		if filterpump.value: 
			Logger.info("Pool: Switching filterpump from ON to OFF...")
			filterpump.write_value(nwvalue=False)
		
		
		

def solar_rule_1(*args, **kwargs):
	'''
	Deze rule kijkt naar de actuele epex prijs.
	Wanneer de epex prijs onder de ingestelde solar_epex_grens zakt wordt de solar omvormer teruggeregeld naar 0%
	Wanneer de epex prijs boven de ingestelde solar_epex_grens stijgt wordt de solar Act_Powerlimit weer op de Normal_Powerlimit gezet
	'''
	use_strategy = DATAPOINTS_ID[solar_use_strategy].value
	use_overrule = DATAPOINTS_ID[solar_overrule].value
	
	Logger.debug("Running solar_rule_1....")
	epex_prijs = DATAPOINTS_ID[epex_data]
	epex_grens = DATAPOINTS_ID[solar_epex_grens]
	powerlimit = DATAPOINTS_ID[solar_powerlimit]
	normal_powerlimit = DATAPOINTS_ID[solar_normal_powerlimit]
	cutoff_powerlimit = DATAPOINTS_ID[solar_cutoff_powerlimit]
	
	# allereerst wordt aan de strategy gevraagd of de panelen AAN of UIT moeten
	# -----er is (nog) geen strategy voor Solar... alleen standaard epex_grens bewaking
	if epex_prijs.value is not None and (epex_prijs.value <= epex_grens.value):
		if powerlimit.value != cutoff_powerlimit.value:
			Logger.info("Epex grenswaarde onderschreden: Zonnepanelen schakelen naar cutoff powerlimit...")
			powerlimit.write_value(nwvalue=cutoff_powerlimit.value)
			return
	elif use_overrule:
		if powerlimit.value != cutoff_powerlimit.value:
			Logger.info("Solar_overrule: Zonnepanelen schakelen naar cutoff powerlimit...")
			powerlimit.write_value(nwvalue=cutoff_powerlimit.value)
			return
	else:
		# De powerlimit wordt niet gepolled..... dus de omvormer zal na een restart weer op 100% gaan staan...
		# TODO: We moeten een manier vinden om de powerlimit gewoon te pollen van de omvormer... dan weten we tenminste
		# wat de stand van de omvormer nu is....
		powerlimit.write_value(nwvalue=normal_powerlimit.value)
		
		# Onderstaande gaat dus niet werken, na een restart (iedere morgen) staat de omvormer weer op 100%, maar omdat wij 
		# niet pollen, weten we dat niet en gaan wij ervan uit dat hij nog op de door ond ingestelde waarde staat...
		# if powerlimit.value != normal_powerlimit.value:
			# Logger.info("Zonnepanelen schakelen op naar normal powerlimit ...")
			# powerlimit.write_value(nwvalue=normal_powerlimit.value)
	



# Counter die iedere keer wanneer de Load Balancing Rule loopt wordt opgehoogd, tot een grens is bereikt
# wordt gebruikt om de verhouding tussen reduction en release van capaciteit te regelen
ALB_run_counter = 0


def load_balance_rule(*args, **kwargs):
	global ALB_run_counter
	'''
	Deze rule kijkt naar de actuele load op de netaansluiting. (grid_netto)
	Wanneer de load hoger wordt dan de maximaal toegestane load (grid_max_load), wordt er gekeken in de tabel
	met loadbalance priorities wie er afgeschakeld mag worden, sommigen kunnen alleen AAN of UIT geschakeld
	worden (zwembad, warmtepomp), en sommigen kunnen ook geregeld worden tussen een minimum en 100% (zonnepanelen en laadpaal)
	deze rule set alleen een load balance limiet.... en de andere rules moeten die dan implementeren....
	
	Wanneer de load onder de maximaal toegestane load is wordt gekeken of er iets bijgeschakeld kan worden
	
	'''
	
	ev_prio = DATAPOINTS_ID[ev_loadbal_prio].value
	ev_curr_limits = (DATAPOINTS_ID[ev_ALB_limit_L1].value, DATAPOINTS_ID[ev_ALB_limit_L2].value, DATAPOINTS_ID[ev_ALB_limit_L3].value)
	ev_init_limits = (DATAPOINTS_ID[ev_ALB_limit_L1_init].value, DATAPOINTS_ID[ev_ALB_limit_L2_init].value, DATAPOINTS_ID[ev_ALB_limit_L3_init].value)
	ev_min_limits = (DATAPOINTS_ID[ev_ALB_limit_L1_min].value, DATAPOINTS_ID[ev_ALB_limit_L2_min].value, DATAPOINTS_ID[ev_ALB_limit_L3_min].value)
	ev_curr_use = (DATAPOINTS_ID[ev_current_L1].value, DATAPOINTS_ID[ev_current_L2].value, DATAPOINTS_ID[ev_current_L3].value)
	ev_alb_dps = (DATAPOINTS_ID[ev_ALB_limit_L1], DATAPOINTS_ID[ev_ALB_limit_L2], DATAPOINTS_ID[ev_ALB_limit_L3])
	
	pool_prio = DATAPOINTS_ID[pool_loadbal_prio].value
	pool_curr_limits = (DATAPOINTS_ID[pool_ALB_limit_L1].value, DATAPOINTS_ID[pool_ALB_limit_L2].value, DATAPOINTS_ID[pool_ALB_limit_L3].value)
	pool_init_limits = (DATAPOINTS_ID[pool_ALB_limit_L1_init].value, DATAPOINTS_ID[pool_ALB_limit_L2_init].value, DATAPOINTS_ID[pool_ALB_limit_L3_init].value) 
	pool_min_limits = (DATAPOINTS_ID[pool_ALB_limit_L1_min].value, DATAPOINTS_ID[pool_ALB_limit_L2_min].value, DATAPOINTS_ID[pool_ALB_limit_L3_min].value)
	pool_curr_use = (DATAPOINTS_ID[pool_current_L1].value, DATAPOINTS_ID[pool_current_L2].value, DATAPOINTS_ID[pool_current_L3].value)
	pool_alb_dps = (DATAPOINTS_ID[pool_ALB_limit_L1], DATAPOINTS_ID[pool_ALB_limit_L2], DATAPOINTS_ID[pool_ALB_limit_L3])
	
	curr_use = (DATAPOINTS_ID[L1_amps].value, DATAPOINTS_ID[L2_amps].value, DATAPOINTS_ID[L3_amps].value)
	max_use = (DATAPOINTS_ID[L1_max_current].value, DATAPOINTS_ID[L2_max_current].value, DATAPOINTS_ID[L3_max_current].value)
	unbalance = [b-a for a,b in zip(max_use, curr_use)]
	
	
	treshold = DATAPOINTS_ID[ALB_treshold].value
	
	use_strategy = DATAPOINTS_ID[use_load_balancing].value
	
	Logger.debug("Running load_balance_rule....")
	
	# Build the load_balance table... every time again in order to take into account changes in ALB settings
	load_balance_info = 	{
						ev_prio:{'name':'laadpaal', 
								'current_use':ev_curr_use, 
								'current_limit':ev_curr_limits, 
								'initial_limit':ev_init_limits, 
								'min_limit':ev_min_limits, 
								'dps': ev_alb_dps, 
								'action': laadpaal_rule_1},
						pool_prio:{'name':'zwembad', 
								'current_use':pool_curr_use,
								'current_limit':pool_curr_limits, 
								'initial_limit':pool_init_limits, 
								'min_limit':pool_min_limits, 
								'dps': pool_alb_dps, 
								'action': zwembad_rule_1}
						# hp_prio:{'name':'warmtepomp', 
								# 'current_use':hp_current_use, 
								# 'current_limit':hp_current_limit,
								# 'initial_limit':hp_initial_limit, 
								# 'dp': hp_limit, 
								# 'action': warmtepomp_strat_1}
							}


	# build a list of the active ALB systems and put them in a string to display on screen
	alb_status = []
	for system in load_balance_info.values():
		# a systems alb is active if the initial limits are no longer used as the current limits...
		if sum([a-b for a,b in zip(system['initial_limit'], system['current_limit'])]) != 0.0:
			if system['name'] not in alb_status: 			alb_status.append(system['name'])
	nw_status = ', '.join(alb_status)
	DATAPOINTS_ID[ALB_status].write_value(nwvalue=nw_status)

	execute_actions = {}
	
	# Releasing capacity on phases must happen much SLOWER then reducing capacity.... some systems take some time to start up
	# te snel capaciteit vrijgeven kan leiden tot jutter gedrag omdat het systeem zo snel niet opstart en bij de volgende ronde nog
	# niet volledig loopt. En dus wordt er dan weer meer capaciteit vrijgegeven etc. etc.
	ALB_run_counter += 1
	handle_availability = False
	# Logger.info(f'ALB_run_counter = {ALB_run_counter}')
	if int(DATAPOINTS_ID[ALB_reduce_release_ratio].value) != 0 and ALB_run_counter % int(DATAPOINTS_ID[ALB_reduce_release_ratio].value) == 0:
		handle_availability = True
		ALB_run_counter = 0
	# Logger.info(f'handle_availability = {handle_availability}')
	
	if use_strategy:
		# now sort the dict based on loadbal_prio ascending (from low to high) load balancing happens from low to high
		reduction_alb_info = dict(sorted(load_balance_info.items()))
		# now sort the dict based on loadbal_prio descending (from high to low)
		release_alb_info = dict(sorted(load_balance_info.items(), reverse=True))
		
		Logger.debug(f'unbalance for phase 1,2,3: {unbalance} A')
		
		for fase in range(3):
			if unbalance[fase] > abs(treshold):
				reduction = unbalance[fase]
				# We moeten reduceren voor deze fase
				Logger.debug(f'Reduction needed for phase {fase}: reduce {reduction} A')
				for system in reduction_alb_info.values():
					# STOP als de benodigde reductie is gehaald
					if reduction <= 0.0: break					
					'''
					Als we nu een reductie moeten doen en er is nog een lagere prio systeem wat niet actief is, zet daarvan de ALB op 0.0
					Voor reductie geldt verder: We lopen de system lijst af in oplopende prioriteit, dus eerst de laagste prioriteit
					indien een systeem GEEN bijdrage levert op deze fase aan het gebruik, maar dit wel zou kunnen, dan zetten we
					de ALB limiet op 0 zodat dit systeem niet plotseling kan gaan draaien. 
					'''
					
					if system['current_use'][fase] == 0.0 and system['initial_limit'][fase] != 0.0:
						# Dit systeem draait nu niet, maar als hij gaat draaien gebruikt hij wel op deze fase, we willen niet dat dat gebeurt
						system['dps'][fase].write_value(nwvalue=0.0)
						execute_actions[system['name']] = system['action']
						continue
						
					elif system['current_use'][fase] >= reduction:
						# Dit systeem draait nu wel op deze fase en zelfs meer dan de onbalans op deze fase, we verminderen de load met de onbalans
						nwvalue=(system['current_use'][fase] - reduction)
						if nwvalue < system['min_limit'][fase]: nwvalue = 0.0
						system['dps'][fase].write_value(nwvalue=nwvalue)
						execute_actions[system['name']] = system['action']
						reduction = 0.0
						continue
						
					elif system['current_use'][fase] != 0.0:
						# Dit systeem draait nu wel op deze fase, maar minder dan de onbalans op deze fase, we schakelen dit systeem op deze fase af
						reduction = reduction - system['current_use'][fase]
						system['dps'][fase].write_value(nwvalue=0.0)
						execute_actions[system['name']] = system['action']
						continue
						

					
			elif unbalance[fase] < -abs(treshold) and handle_availability:
				available = -unbalance[fase]
				# Er is ruimte over op deze fasen en meer dan de treshold
				Logger.debug(f'Extra room available for phase {fase}: available {available} A')
				for system in release_alb_info.values():
					# STOP als alle available ruimte is weggegeven
					if available <= 0.0: break
					'''
					Voor vrijgave geldt: We lopen de system list af in aflopende prioriteit, dus de hoogste prioriteit eerst....
					We hoeven niet te kijken of een systeem actief is of in alb staat...Door de limieten stukje bij beetje vrij te geven 
					zal in deze of een volgende iteratie vanzelf een actief/alb systeem worden vrijgegeven, immers bij een volgende run zal blijken 
					dat de vrijgave in deze run nog steeds tot een boel available ruimte leidt op de fase.... 
					'''
					if system['current_limit'][fase] == system['initial_limit'][fase]:
						# Andere aanpak: als er geen alb actief is....-> skip dit systeem
						continue
						
					if system['current_limit'][fase] == 0.0 and available >= system['min_limit'][fase]:
						# Als er wel alb actief is en we hebben genoeg ruimte om in ieder geval de minimum limit te halen....doen!
						nwvalue = min(available, system['initial_limit'][fase])
						available = available - nwvalue
						system['dps'][fase].write_value(nwvalue=nwvalue)
						execute_actions[system['name']] = system['action']
						continue
					
					if system['current_limit'][fase] != 0.0 and available >= (system['initial_limit'][fase] - system['current_limit'][fase]):
						# Er is genoeg ruimte beschikbaar om alb UIT te zetten voor deze fase
						system['dps'][fase].write_value(nwvalue=system['initial_limit'][fase])
						execute_actions[system['name']] = system['action']
						available = available - (system['initial_limit'][fase] - system['current_limit'][fase])
						continue
						
					if system['current_limit'][fase] != 0.0 and available < (system['initial_limit'][fase] - system['current_limit'][fase]):
						# In dit geval zouden we dus een beetje alb kunnen vrijgeven.... maar dat leidt tot jutteren
						nwvalue = system['current_limit'][fase] + available
						available = 0.0
						system['dps'][fase].write_value(nwvalue=nwvalue)
						execute_actions[system['name']] = system['action']
						continue
						
						
			
			else:
				# Unbalance for this phase is between - and + treshold... no action needed
				Logger.debug(f'Unbalance for phase {fase} = {unbalance[fase]} A, no action needed!!!')
			
	else:
		for system in load_balance_info.values():
			for fase in range(3):
				# Reset all limits to their initial values
				system['dps'][fase].write_value(nwvalue=system['initial_limit'][fase])
			execute_actions[system['name']] = system['action']

	for action in execute_actions.values():
		# run the necessary rules to activate the load balancing
		action()
	
	
	
def main(args):
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
