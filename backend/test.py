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

drivers =['HUL']

session = fastf1.get_session(2025, "United Kingdom", "Race")
session.load(laps=True, telemetry=False, weather=False)

laps = session.laps.copy()
laps = laps[laps["Driver"].isin(drivers)]
laps = laps[laps["LapTime"].notna()]
if pd.api.types.is_timedelta64_dtype(laps["LapTime"]):
    laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
else:
    laps["LapTimeSeconds"] = pd.to_numeric(laps["LapTime"], errors="coerce")
    laps = laps[laps["LapTimeSeconds"].notna()]

print(laps[["Driver","LapNumber","LapTimeSeconds"]])



