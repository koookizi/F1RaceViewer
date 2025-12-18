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

def session_leaderboard_view(year, country, session_name):    
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    openf1_start = pd.to_datetime(session_df.loc[0, "date_start"], utc=True)
    openf1_end = pd.to_datetime(session_df.loc[0, "date_end"], utc=True)

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    fastf1_start = session.t0_date + session.session_start_time # gets the actual datetime of session start (first telemetry point)

    # ---

    # get position data
    positions_data_req = urlopen(f"https://api.openf1.org/v1/position?meeting_key={session_df.loc[0, 'meeting_key']}&date>{session_df.loc[0, "date_start"]}")
    positions_data = pd.DataFrame(json.loads(positions_data_req.read().decode('utf-8')))
    positions_data["date"] = pd.to_datetime(
        positions_data["date"],
        utc=True,
        format="ISO8601"
    )

    positions_data["SessionTime"] = (
        positions_data["date"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    positions_data = positions_data[
    ["SessionTime"] + [c for c in positions_data.columns if c != "SessionTime"]]
    positions_data.sort_values("SessionTime")

    positions_data = positions_data.drop(columns=['date', 'meeting_key', 'session_key'])

    # > cleans any NaNs for JSON
    positions_data = positions_data.astype(object)
    positions_data = positions_data.where(pd.notna(positions_data), None)

    # get lap data
    laps_data_req = urlopen(f"https://api.openf1.org/v1/laps?session_key={session_df.loc[0, "session_key"]}&date_start>={session_df.loc[0, "date_start"]}")
    laps_data = pd.DataFrame(json.loads(laps_data_req.read().decode('utf-8')))
    laps_data["date_start"] = pd.to_datetime(
        laps_data["date_start"],
        utc=True,
        format="ISO8601"
    )

    laps_data["SessionTime"] = (
        laps_data["date_start"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    laps_data = laps_data.drop(columns=['meeting_key', 'session_key', 'date_start'])

    laps_data = laps_data[
    ["SessionTime"] + [c for c in laps_data.columns if c != "SessionTime"]
    ]

    laps_data = laps_data.astype(object)
    laps_data = laps_data.where(pd.notna(laps_data), None)

    # get stint data
    stint_data_req = urlopen(f"https://api.openf1.org/v1/stints?session_key={session_df.loc[0, "session_key"]}")
    stint_data = pd.DataFrame(json.loads(stint_data_req.read().decode('utf-8')))
    stint_data = stint_data.drop(columns=['meeting_key', 'session_key'])

    stint_data = stint_data.astype(object)
    stint_data = stint_data.where(pd.notna(stint_data), None)

    # get pit data
    pit_data_req = urlopen(f"https://api.openf1.org/v1/pit?session_key={session_df.loc[0, 'session_key']}&date>={session_df.loc[0, 'date_start']}")
    pit_data = pd.DataFrame(json.loads(pit_data_req.read().decode('utf-8')))
    pit_data["date"] = pd.to_datetime(
        pit_data["date"],
        utc=True,
        format="ISO8601"
    )

    pit_data["SessionTime"] = (
        pit_data["date"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    pit_data = pit_data[
    ["SessionTime"] + [c for c in pit_data.columns if c != "SessionTime"]]
    pit_data.sort_values("SessionTime")

    pit_data = pit_data.drop(columns=['date', 'meeting_key', 'session_key'])

    # > cleans any NaNs for JSON
    pit_data = pit_data.astype(object)
    pit_data = pit_data.where(pd.notna(pit_data), None)

    # get car data
    # grid_positions = {}
    # results = session.results
    # if results is not None and not results.empty:
    #     for drv in session.drivers:
    #         try:
    #             grid_positions[drv] = int(results.loc[drv]["GridPosition"])
    #         except Exception:
    #             grid_positions[drv] = None
    # else:
    #     for drv in session.drivers:
    #         grid_positions[drv] = None

    # keep_cols = ["SessionTime", "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS", "Time"]

    # all_tel = []
    # for drv in session.drivers:
    #     print("Getting data for:",drv)
    #     laps = session.laps.pick_drivers(drv)  # pick_driver (singular) is the usual one
    #     tel = laps.get_telemetry().copy()

    #     # Reduce columns early
    #     tel = tel[[c for c in keep_cols if c in tel.columns]]

    #     # Downsample early (HUGE speed win + smaller JSON)
    #     step=10
    #     if step and step > 1:
    #         tel = tel.iloc[::step].copy()

    #     tel["driver_number"] = drv
    #     tel["SessionTime"] = tel["Time"].dt.total_seconds()
    #     all_tel.append(tel)

    # car_data = pd.concat(all_tel, ignore_index=True)
    # car_data = car_data[
    # ["SessionTime"] + [c for c in car_data.columns if c != "SessionTime"]
    # ]

    # car_data = car_data.astype(object)
    # car_data = car_data.where(pd.notna(car_data), None)
    # car_data["driver_number"] = pd.to_numeric(car_data["driver_number"], errors="coerce").astype("Int64") # because FastF1 gives str

    # car_data = car_data.drop(columns=['Time'])
    # car_data = car_data[car_data["SessionTime"] >= (fastf1_start - session.t0_date).total_seconds()]  # remove neglible times

    # car_data["grid_position"] = car_data["driver_number"].astype(str).map(grid_positions)

    # get gap data
    gap_data_req = urlopen(f"https://api.openf1.org/v1/intervals?meeting_key={session_df.loc[0, 'meeting_key']}")
    gap_data = pd.DataFrame(json.loads(gap_data_req.read().decode('utf-8')))
    gap_data["date"] = pd.to_datetime(
        gap_data["date"],
        utc=True,
        format="ISO8601"
    )

    gap_data["SessionTime"] = (
        gap_data["date"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    gap_data = gap_data[
    ["SessionTime"] + [c for c in gap_data.columns if c != "SessionTime"]]
    gap_data.sort_values("SessionTime")

    gap_data = gap_data.drop(columns=['date', 'meeting_key', 'session_key'])

    # > cleans any NaNs for JSON
    gap_data = gap_data.astype(object)
    gap_data = gap_data.where(pd.notna(gap_data), None)

    # -- get driver info / final structure
    drivers_data_req = urlopen(f"https://api.openf1.org/v1/drivers?session_key={session_df.loc[0, "session_key"]}")
    drivers_df = pd.DataFrame(json.loads(drivers_data_req.read().decode('utf-8')))
    finalJSON = {}
    for _, driver_row in drivers_df.iterrows():
        driver_info = {
            "driver_code": driver_row["name_acronym"],
            "driver_number": driver_row["driver_number"],
            "driver_fullName": driver_row["full_name"],
            "team_colour": driver_row["team_colour"],
            #"positions_data": positions_data[positions_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            #"laps_data": laps_data[laps_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            #"stint_data": stint_data[stint_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "car_data": car_data[car_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            #"gap_data": gap_data[gap_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            #"pit_data": pit_data[pit_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
        }
        finalJSON[driver_row["name_acronym"]] = driver_info

    print(json.dumps(finalJSON, indent=4))
    

session_leaderboard_view(2025, "United Kingdom", "Race")
