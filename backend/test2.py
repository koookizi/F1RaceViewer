from urllib.request import urlopen
import fastf1 
import pandas as pd
import numpy as np
import json
from datetime import datetime
import math
import openpyxl
from datetime import datetime, timedelta
from datetime import timezone

def fetch_car_data_chunk(session_key, start_iso, end_iso):
    response = urlopen(f'https://api.openf1.org/v1/car_data?session_key={session_key}&date>={start_iso}')
    return json.loads(response.read().decode('utf-8'))

def session_playback_view(year, country, session_name):    
    session = fastf1.get_session(year, country, session_name)
    session.load()

    # fastf1_start = session.t0_date + session.session_start_time

    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    openf1_start = pd.to_datetime(session_df.loc[0, "date_start"], utc=True)
    openf1_end = pd.to_datetime(session_df.loc[0, "date_end"], utc=True)

    response = urlopen(f'https://api.openf1.org/v1/car_data?driver_number=44&session_key={session_df.loc[0, "session_key"]}')
    data = json.loads(response.read().decode('utf-8'))
    print(json.dumps(data, indent=4))


session_playback_view(2025, "United Kingdom", "Race")
