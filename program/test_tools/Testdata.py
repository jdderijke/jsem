import json
import pathlib
import random
from datetime import datetime

import pandas as pd
from textwrap import dedent


def load_from_json(filepath=None):
	"""
	Loads this holdings datapoints from a JSON file specified in the filepath argument, but only if that file contains
	data that is less than mfda old

	Args:
		filepath: (Path) The JSON file to load this holdings datapoints from. defaults to isin_dp.json in the cache directory
						of the mother portfolio
		cdrh: (int) The maximum age of the data in the JSON file that will be accepted

	Raises:
		FileNotFoundError: if the cache json file does not exist
		TimeoutError: if the data is too old and exceeded mfda
	"""
	datapoints = {}
	try:
		with open(filepath) as json_file:
			tmp = json.load(json_file)
	except Exception as err:
		raise FileNotFoundError(f'{filepath}-- Problems...')
	
	datapoints = tmp
	
	# All data is now in datapoints... but...
	# Some of the datapoints are now a dict because of the JSON restrictions, we want them in a dataframe
	try:
		for dp in datapoints:
			if type(datapoints[dp]) is dict:
				dp_df = pd.DataFrame(datapoints[dp])
				try:
					dp_df = dp_df.astype(float, errors='ignore')
				except Exception as err:
					print(str(err))
				datapoints[dp] = dp_df
	except Exception as err:
		print(str(err))
	
	# assume a portfolio total value of 1.000.000,-
	prtf_value = 1000000
	assets_df = datapoints['assets']
	if 'weighting' in assets_df:
		sum_of_weightings = assets_df['weighting'].sum()
		if sum_of_weightings != 100.0:
			# We have seen that the sum of all weightings of all assets does NOT equal 100.0 at all times
			# for now we rescale the weighting back to a total of 100.0
			assets_df['weighting'] = assets_df['weighting'] * (100.0 / sum_of_weightings)
			assets_df['weighting'] = assets_df['weighting'].round(4)
		assets_df['prtf_value'] = assets_df['weighting'] * prtf_value / 100.0
		assets_df['prtf_value'] = assets_df['prtf_value'].round(2)
		assets_df['prtf_weighting'] = assets_df['weighting']
		assets_df['prtf_weighting'] = assets_df['prtf_weighting'].round(2)

	else:
		print('Could not calculate the prtf_value for the assets')
		print('No weighting column in assets_df, defaulting prtf_value to 0.0')
		assets_df['prtf_value'] = 0.0
		assets_df['prtf_weighting'] = 0.0
	
	datapoints['assets'] = assets_df
	
	return datapoints



testdata = [('ID', 'Enabled', 'First Name', 'Last Name'),
			('101', True, 'Danny zag lange loesje lopen langs de lange lindelaan', 'Young'),
			('102', False, 'Christine', 'Holland'),
			('103', True, 'Lars', 'Gordon'),
			('104', False, 'Roberto', 'Robitaille'),
			('105', True, 'Maria', 'Papadopoulos'),
			('101', True, 'Danny zag lange loesje lopen langs de lange lindelaan', 'Young'),
			('102', False, 'Christine', 'Holland'),
			('103', True, 'Lars', 'Gordon'),
			('104', False, 'Roberto', 'Robitaille'),
			('105', True, 'Maria', 'Papadopoulos'),
			('101', True, 'Danny zag lange loesje lopen langs de lange lindelaan', 'Young'),
			('102', False, 'Christine', 'Holland'),
			('103', True, 'Lars', 'Gordon'),
			('104', False, 'Roberto', 'Robitaille'),
			('105', True, 'Maria', 'Papadopoulos'),
			('101', True, 'Danny zag lange loesje lopen langs de lange lindelaan', 'Young'),
			('102', False, 'Christine', 'Holland'),
			('103', True, 'Lars', 'Gordon'),
			('104', False, 'Roberto', 'Robitaille'),
			('105', True, 'Maria', 'Papadopoulos'),
			('101', True, 'Danny zag lange loesje lopen langs de lange lindelaan', 'Young'),
			('102', False, 'Christine', 'Holland'),
			('103', True, 'Lars', 'Gordon'),
			('104', False, 'Roberto', 'Robitaille'),
			('105', True, 'Maria', 'Papadopoulos')
			]

tooltips = [[None],
			['Rare achternaam<br/>Tweede regel<br/>Derde regel'],
			['Dit is dus 102'],
			['Dit is dus 103 <br/>Tweede regel'],
			['en dit 104 <br/>Extra regel <br/>En nog een..'],
			['en dit 105 <br/>En nog een..'],
			]
tt_df = pd.DataFrame(tooltips)

test_df = pd.DataFrame(testdata[1:], columns=testdata[0])

test_msg = """
Dit is een test
"""
intro_msg = """
## **Enter portfolio setup information.**
* Choose a portfolio name, no spaces and no characters that are incompatible with the naming conventions of the file system...
* The Portfolio currency is the currency all positions will be translated into. The current Exchange Rate is used from the Yahoo Finance website...
#### Different Header
* Economy mode uses cached data whenever possible. Using cached data significantly reduces the data traffic on the Morningstar endpoint.
* Cached data retention is the number of hours the cached data can be used after it has been downloaded from Morningstar
#### <b><u>And another one</u></b>
* dit is een test line
* en dit is ook een testline <u>**Once a fund is removed it can not be undone**</u>
"""

countries = {
	"unitedStates": 72.94327,
	"japan": 5.502,
	"unitedKingdom": 3.16509,
	"canada": 3.14909,
	"switzerland": 2.572,
	"france": 2.32579,
	"germany": 2.27603,
	"australia": 1.66727,
	"netherlands": 1.33353,
	"spain": 0.88685,
	"sweden": 0.81443,
	"italy": 0.68029,
	"singapore": 0.50874,
	"denmark": 0.4802,
	"hongKong": 0.43888,
	"belgium": 0.21067,
	"finland": 0.20668,
	"israel": 0.18843,
	"ireland": 0.14319,
	"brazil": 0.13999,
	"norway": 0.13621,
	"austria": 0.05486,
	"portugal": 0.05012,
	"newZealand": 0.04861,
	"china": 0.03543,
	"malaysia": 0.01853,
	"mexico": 0.00857,
	"poland": 0.0037
}
countries_df = pd.DataFrame(
	{'countries': [k for k in countries.keys()], 'exposure': [v for v in countries.values()]}).set_index(['countries'])

line_test_df = pd.DataFrame(
	{'date':[f'2025-{m}-1' for m in range(1,13)],
	 'serie1':[random.randint(0,1000) for x in range(1,13)],
	 'serie2':[random.randint(0,1000) for x in range(1,13)],
	 'serie3':[random.randint(0,1000) for x in range(1,13)]}
							)
line_test_df = line_test_df.set_index(['date'])



