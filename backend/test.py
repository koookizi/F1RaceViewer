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

# def test(year, country, session_name):    
#     # FastF1
#     session = fastf1.get_session(year, country, session_name)
#     session.load()


    

# test(2025, "United Kingdom", "Race")

s = fastf1.get_session(2023, 1, "R")
s.load()
print(s.results["TeamName"].unique())