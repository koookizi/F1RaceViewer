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

def session_teamradio_view(year, country, session_name):    
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    fastf1_start = session.t0_date + session.session_start_time # gets the actual datetime of session start (first telemetry point)

    # ---

    print("FastF1: ",fastf1_start)
    print("OpenF1: ",session_df.loc[0, 'date_start'])
    

session_teamradio_view(2025, "United Kingdom", "Race")
