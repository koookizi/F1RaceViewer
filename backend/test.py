from urllib.request import urlopen
from django.http import JsonResponse
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

def session_racecontrol_view(request, year: int, country: str, session_name: str):    
    """
    Retrieves and formats race control messages for a given session.

    Session details are used to obtain the relevant OpenF1 race control data,
    which is then aligned to session-relative time using FastF1 timestamps.
    The data is cleaned and structured for use in race playback.

    Args:
        request: HTTP request object.
        year (int): Race year.
        country (str): Grand Prix location.
        session_name (str): Session type.

    Returns:
        JsonResponse: List of race control events with timestamps aligned to
        session time, formatted for playback.
    """
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    print(session)

    # ---

    # get race control data
    racecontrol_data_req = urlopen(f"https://api.openf1.org/v1/race_control?session_key={session_df.loc[0, 'session_key']}&date>{session_df.loc[0, "date_start"]}")
    racecontrol_data = pd.DataFrame(json.loads(racecontrol_data_req.read().decode('utf-8')))
    racecontrol_data["date"] = pd.to_datetime(
        racecontrol_data["date"],
        utc=True,
        format="ISO8601"
    )

    racecontrol_data["SessionTime"] = (
        racecontrol_data["date"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    racecontrol_data = racecontrol_data[
    ["SessionTime"] + [c for c in racecontrol_data.columns if c != "SessionTime"]]
    racecontrol_data.sort_values("SessionTime")

    racecontrol_data["time"] = (
    pd.to_datetime(racecontrol_data["date"])
    .dt.strftime("%H:%M:%S")
)

    racecontrol_data = racecontrol_data.drop(columns=['date', 'meeting_key', 'session_key'])

    # > cleans any NaNs for JSON
    racecontrol_data = racecontrol_data.astype(object)
    racecontrol_data = racecontrol_data.where(pd.notna(racecontrol_data), None)

    # -- final structure
    finalJSON = racecontrol_data.to_dict(orient="records")

    return JsonResponse(finalJSON, safe=False)

print(session_racecontrol_view(None, 2026, "Australia", "Race"))


