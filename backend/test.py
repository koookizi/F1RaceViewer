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

def test(year, country, session_name):    
    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    fastf1_start = session.t0_date + session.session_start_time # gets the actual datetime of session start (first telemetry point)

    # get car data
    grid_positions = {}
    results = session.results
    if results is not None and not results.empty:
        for drv in session.drivers:
            try:
                grid_positions[drv] = int(results.loc[drv]["GridPosition"])
            except Exception:
                grid_positions[drv] = None
    else:
        for drv in session.drivers:
            grid_positions[drv] = None

    drivers = ["63"]
    all_tel = []
    for drv in drivers:
        print("Getting data for:",drv)
        laps = session.laps.pick_drivers(drv)  # pick_driver (singular) is the usual one
        tel = laps.get_telemetry().copy()

        # Downsample early (HUGE speed win + smaller JSON)
        step=10
        if step and step > 1:
            tel = tel.iloc[::step].copy()

        tel["driver_number"] = drv
        tel["SessionTime"] = tel["Time"].dt.total_seconds()
        all_tel.append(tel)

        print(tel)


    car_data = pd.concat(all_tel, ignore_index=True)
    car_data = car_data[
    ["SessionTime"] + [c for c in car_data.columns if c != "SessionTime"]
    ]

    car_data = car_data.astype(object)
    car_data = car_data.where(pd.notna(car_data), None)
    car_data["driver_number"] = pd.to_numeric(car_data["driver_number"], errors="coerce").astype("Int64") # because FastF1 gives str

    car_data = car_data.drop(columns=['Time'])

    car_data["grid_position"] = car_data["driver_number"].astype(str).map(grid_positions)
    
    

test(2025, "United Kingdom", "Race")
