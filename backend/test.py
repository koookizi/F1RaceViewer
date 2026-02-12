from urllib.request import urlopen
import fastf1 
import pandas as pd
import numpy as np
import json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen
from urllib.parse import urlencode
import math
import openpyxl

import fastf1
from fastf1.ergast import Ergast

# def test(year, country, session_name):    
#     # FastF1
#     session = fastf1.get_session(year, country, session_name)
#     session.load()


    

# test(2025, "United Kingdom", "Race")

ergast_driver_id = "hamilton"  # Ergast driverId
ergast = Ergast()

df = ergast.get_driver_info(driver=ergast_driver_id)  # pandas DataFrame
abbr = df.loc[0, "driverCode"]  # e.g. "HAM"

print(abbr)