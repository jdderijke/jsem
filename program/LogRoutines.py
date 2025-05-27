
import __main__
import sys
import os.path
from datetime import datetime
from Config import LOGFILELOCATION, Loglevel, ENVIRONMENT
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler
from Common_Enums import *
from pathlib import Path


try:
	print("Logroutine script started with logfilename: ",__main__.logfilename)
	# wait = input("any_key")
	Path(LOGFILELOCATION).mkdir(parents=True, exist_ok=True)
	filepath = Path(LOGFILELOCATION, __main__.logfilename)
	Logger = logging.getLogger(__main__.logfilename.split('.')[0] + '_logger')
	handler = logging.handlers.RotatingFileHandler(filepath, mode="a", backupCount=__main__.backupcount)
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s')
	handler.setFormatter(formatter)
	# Om te voorkomen dat hij verder logt in de oude logfile doen we eerst een rollover om de logger te dwingen een nieuwe logfile aan te maken..
	handler.doRollover()
	Logger.addHandler(handler)
	Logger.setLevel(Loglevel)
	# Standaard worden log messages doorgegeven aan de root Logger, om dit te voorkomen (en dus te voorkomen dat er toch nog messages komen
	# op de stdOUT dient propagate op False te worden gezet!!
	if ENVIRONMENT == Environment.Productie:
		Logger.propagate = False
	else:
		Logger.propagate = False
		handler2 = logging.StreamHandler(sys.stdout)
		# handler2.setLevel(Loglevel)
		formatter2 = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s')
		handler2.setFormatter(formatter2)
		Logger.addHandler(handler2)
			
	Logger.info("Logfile created....")
	# print ("LogRoutines ran")
except Exception as err:
	print("openlog routine: " + str(err))
	# logging.shutdown()



def main(args):
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
