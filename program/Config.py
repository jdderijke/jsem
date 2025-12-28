import os
import __main__
import sys
from pathlib import Path
from Common_Enums import Environment, DataSelection
import logging

'''
Met het loglevel wordt bepaald welke gebeurtenissen allemaal worden gelogd in de logfile. Normaal zou ik INFO als level kiezen
maar bij aanhoudende problemen kun je hem op DEBUG zetten.....maar dan krijg je wel hele grote logfiles.....
'''
# Logger settings
# Loglevel = logging.DEBUG
Loglevel = logging.INFO
# Loglevel = logging.ERROR

# System settings
ENVIRONMENT = Environment.Productie
# ENVIRONMENT = Environment.Test_full
# ENVIRONMENT = Environment.Test_data

BTW_PERC = 21


# Het systeem heeft de mogelijkheden om SQL te ontvangen van een externe computer, dit is voor
# toekomstige uitbreidingen met bijvoorbeeld een andere computer die DNN and AI functionaliteit heeft....
# Specify the MAXIMUM number of external connections accepted by the system, 0=No external connection allowed
MAX_EXTERNAL_CONN = 1
# Port for TCP commando server to listen on (non-privileged ports are > 1023), when 0 is used the system uses default 65432
TCPPORT = 65432
# IP address to use, if None or empty then system local IP address will be used, see log file at startup for used IP address.
# TCPHOST = "192.168.4.1"
TCPHOST = ""



# Current Working Directory... define the path to the directory of the running script... (which is not always pathlib.Path.cwd())
if hasattr(__main__, "__file__"):
	CWD = Path(os.path.dirname(os.path.abspath(__main__.__file__)))
else:
	CWD = Path(sys.path[0])

# File settings
LOGFILELOCATION = Path(CWD.parent, "resources/Logs")
# CSVFILELOCATION = "/Datapoints"
DBFILE = Path(CWD.parent, "resources/Database/JSEM.db")
# DBFILE = "Database/TEST.db"
IMAGES_LOCATION = Path(CWD.parent, "resources/Images")

DAYAHEAD_PRICES = Path(CWD.parent, "resources/DayAHeadPrices")
POWERSTATS = Path(CWD.parent, "resources/Powerstats")
PREDICTIONS = Path(CWD.parent, "resources/Predictions")
DB_CSV_FILES = Path(CWD.parent, "resources/DB_CSV_Files")
# CHROMEDRIVER_LOCATION = "/usr/lib/chromium-browser/chromedriver"
TFLITE_MODELS = Path(CWD.parent, "resources/tflite_models")
METEOSERVER_FORECASTS = Path(CWD.parent, "resources/MeteoServerForecasts")

# Meteoserver settings
METEOSERVER_KEY = "724ea43a99"		# PAS OP zie de website meteoserver.nl en log in. De key is goed voor max 500 datarequests/maand
METEOSERVER_DEFAULT_LOCATION = "Raalte"
METEOSERVER_DEFAULT_PC = "8141PR"
# Kies 1 van 2 modellen: uurverwachting - hoge resolutie 2 dagen of uurverwachting_gfs - 10 dagen medium resolutie
# METEOSERVER_URL = "https://data.meteoserver.nl/api/uurverwachting.php?%s&key=%s"
METEOSERVER_URL = "https://data.meteoserver.nl/api/uurverwachting_gfs.php?%s&key=%s"



# Heatpump planning settings
HP_POWER = 17.6		# Kw
HP_USAGE = 4.9		# Kw
# BUF_MIN = 3.0		# Kwh
# BUF_MAX = 38.0		# Kwh

# Pool optimer settings
DEFAULT_FILTERHOURS = 4
POOL_WIDTH = 5
POOL_LENGTH = 10
POOL_DEPTH = 1.7
POOL_TOPLAYER = 0.1

# Learning parameters for Powerstats
LOOK_BACK_DAYS = 365		# Number of days to look back in the DB for power usage statistics 
CONFIDENCE_LEVEL = 0.90 	# confidence level... 0.9 means that all powerreadings that are above 95% or below 5% will be dismissed
MINIMUM_VALID_SAMPLES = 20	# how many valid samples are minimally needed to learn from powerreadings at a certain outside temperature
HEATCURVE = 0.40			# What heatcurve should be used when looking for powerreadings
THERMOSTAT = 18.0			# what thermostat setting should be used when looking for powerreadings
TEMP_CORRECTION = 1.0		# correctie voor de forecast temperatuur (meteoserver) voor beter aansluiten bij de gemeten temperatuur door de warmtepomp
MAX_DEVIATION = 0.20		# max deviation for the ws52 watersetpoints (min-avg-max), above this the avg_poweruse measurement is invalid

frcst_timeshift = 0		# aantal uren dat de temp_frcst wordt vervroegd (-) of verlaat (+) voor het runnen van het predictie model van de Heating Power

# # de grenswaarden voor temp_frcst waarONDER de correcties worden toegepast van frcst_tempcorrvalues,
# # dus bij temp_frcst <= 2.0 gr Celcius: 2.5 graden erbij optellen
# frcst_tempcorrtresholds = 	[2.0, 7.0, 11.0]
# # aantal graden (Celcius) wat opgeteld moet worden bij de temp_frcst voor het predictiemodel Heating Power
# frcst_tempcorrvalues = 		[2.5, 1.5, 1.0, 0.0]

# Eem geheel andere benadering is om de frcst_temp en de echte BuitenTemperatuur1 over de afgelopen x uren te vergelijken en het 
# gemiddelde verschil te gebruiken als correctie op de frcst
frcst_tempcorr_backlook = 6

# Signal settings
# Kleuren van de ALARM, WARNING en SIGNAL indicaties van een datapoint
Signal_bg_color = "green"
Signal_fg_color = "black"

Warning_bg_color = "yellow"
Warning_fg_color = "black"

Alarm_bg_color = "red"
Alarm_fg_color = "white"

NoSignal_bg_color = "grey"
NoSignal_fg_color = "black"

# Database settings
DB_RETRIES = 3
DB_WAITBETWEENRETRIES = 0.2
# de looptime of the thread that does all the writes to the database, it empties the queue of queries and then sleeps for the DB_looptime
# before checking on the queue again

# DB_looptime = 0.2
DB_looptime = 2.0

# number of seconds before an alive signal is send to the Logger
DB_alivetime = 1800


# All interfaces have a send Queue, this is the maximum allowed number of entries in the send Queue after which a reconnect will be forced.
MsgQ_Alarm = 10

# Time in the day, month etc that the system must perform a save reboot, empty means NO reboot EVER.
Reboot_time = "04:00:00"

# Charts Settings


# Default Chart DataSelection
Default_ChartMode = DataSelection.Day
# Max number of points to be plotted in any single Chart
Max_Chart_Points = 5000
# Max number of datavalues to be rendered into a BAR chart, switch to LINE chart above this number
MaxValuesForBarChart = 150

Chart_Definitions=		{
						"line":	{
								"ctype": "line",
								"title": "LineChart",
								"aggr": "Not",
								"joinwith": [],
								"max_x_cols": Max_Chart_Points,
								"max_y_rows": None,
								"x_col_labels": [],
								"y_row_labels": []
								},
						"bar":  {
								"ctype": "bar",
								"title": "BarChart",
								"aggr": "Not",
								"joinwith": [],
								"max_x_cols": MaxValuesForBarChart,
								"max_y_rows": None,
								"x_col_labels": [],
								"y_row_labels": []
								},

						"map":  {
								"ctype": "map",
								"title": "Plan",
								"aggr": "Not",
								"joinwith": [],
								"max_x_cols": 6,
								"max_y_rows": 24,
								"x_col_labels": [],
								"y_row_labels": []
								}
						}

# Define the best strftime format for the x-axis of the charts
Best_dtFormat = {DataSelection._10min:'%H:%M:%S', 
				 DataSelection._30min:'%H:%M',
				 DataSelection._1hr:'%H:%M', 
				 DataSelection._2hr:'%H:%M',
				 DataSelection._6hr:'%H:%M',
				 DataSelection._12hr:'%H:%M',
				 DataSelection._24hr:'%H',
				 DataSelection._48hr:'%d-%m %H',
				 DataSelection.Day:'%H',
				 DataSelection.Week:'%d-%m %H',
				 DataSelection.Month:'%d-%m',
				 DataSelection.Year:'%m',
				}
