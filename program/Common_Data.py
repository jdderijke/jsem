
import os
import __main__
import sys
from pathlib import Path


INTERFACE_ID = {}
INTERFACE_NAME = {}

CATEGORY_ID = {}
CATEGORY_NAME = {}

DATAPOINTS_ID = {}
DATAPOINTS_NAME = {}

SELECTED_CHART = None
SELECTED_DATAPOINTS = []

CHARTS_AND_DATA_PARENT_CONTAINER = None
CHARTS_PARENT_CONTAINER = None
DATA_PARENT_CONTAINER = None

MAIN_CONTAINER = None
MAIN_INSTANCE = None

# REMI_SHOULD_RUN = True
# REMI_IS_RUNNING = False

# JSEM_RULES is a list containing all the active JSEM rule objects
JSEM_RULES = []

# DBSTORE is the DBstore_engine responsible for all writing actions to the DB
DB_STORE = None


def main(args):
	return 0

if __name__ == '__main__':
	import sys
	sys.exit(main(sys.argv))
