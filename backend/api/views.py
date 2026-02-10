from django.shortcuts import render
from django.http import HttpResponseBadRequest, JsonResponse
from api.models import Season, Event, Session
import fastf1
from fastf1.ergast import Ergast
import math
import pandas as pd 
import numpy as np
from functools import lru_cache
from .helpers.geometry import rotate, normalize_xy
import json
from datetime import datetime
from urllib.request import urlopen
from datetime import timezone
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
from django.views.decorators.csrf import csrf_exempt
import plotly.graph_objects as go


def season_years(request):
    years = (
        Season.objects
        .order_by('-year')
        .values_list('year', flat=True)
    )
    return JsonResponse({"years":list(years)})

def season_countries(request, year):
    countries = (
        Event.objects
        .filter(season__year=year)
        .values_list('country', flat=True)
        .distinct()
    )
    return JsonResponse({"countries": list(countries)})

def season_sessions(request, year, country):
    sessions = (
        Session.objects
        .filter(event__country=country)
        .filter(event__season__year=year)
        .values_list('session_type', flat=True)
        .distinct()
        .order_by('session_type')
    )
    return JsonResponse({"sessions": list(sessions)})

@lru_cache(maxsize=32)
def session_circuit(request, year: int, country: str):
    event = (
        Event.objects
        .select_related("circuit")
        .filter(season__year=year, country=country)
        .first()
    )
    if not event:
        return JsonResponse({"error": "Event not found"}, status=404)

    return JsonResponse({
        "circuit": event.circuit.name, 
    })

@lru_cache(maxsize=32)
def session_teamradio_view(request, year: int, country: str, session_name: str):    
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    fastf1_start = session.t0_date + session.session_start_time # gets the actual datetime of session start (first telemetry point)

    # ---

    # get team radio data
    teamradio_data_req = urlopen(f"https://api.openf1.org/v1/team_radio?session_key={session_df.loc[0, 'session_key']}&date>{session_df.loc[0, "date_start"]}")
    teamradio_data = pd.DataFrame(json.loads(teamradio_data_req.read().decode('utf-8')))
    teamradio_data["date"] = pd.to_datetime(
        teamradio_data["date"],
        utc=True,
        format="ISO8601"
    )

    teamradio_data["SessionTime"] = (
        teamradio_data["date"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    teamradio_data = teamradio_data[
    ["SessionTime"] + [c for c in teamradio_data.columns if c != "SessionTime"]]
    teamradio_data.sort_values("SessionTime")

    teamradio_data["time"] = (
    pd.to_datetime(teamradio_data["date"])
    .dt.strftime("%H:%M:%S")
)

    teamradio_data = teamradio_data.drop(columns=['date', 'meeting_key', 'session_key'])

    # > cleans any NaNs for JSON
    teamradio_data = teamradio_data.astype(object)
    teamradio_data = teamradio_data.where(pd.notna(teamradio_data), None)

    # -- final structure
    finalJSON = teamradio_data.to_dict(orient="records")

    return JsonResponse(finalJSON, safe=False)

@lru_cache(maxsize=32)
def session_racecontrol_view(request, year: int, country: str, session_name: str):    
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    fastf1_start = session.t0_date + session.session_start_time # gets the actual datetime of session start (first telemetry point)

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

@lru_cache(maxsize=32)
def session_leaderboard_view(request, year: int, country: str, session_name: str):    
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
    positions_data_req = urlopen(f"https://api.openf1.org/v1/position?meeting_key={session_df.loc[0, 'meeting_key']}&date>={session_df.loc[0, "date_start"]}")
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

    keep_cols = ["SessionTime", "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS", "Time"]

    all_tel = []
    for drv in session.drivers:
        print("Getting data for:",drv)
        laps = session.laps.pick_drivers(drv) 
        tel = laps.get_telemetry().copy()

        # Reduce columns early
        tel = tel[[c for c in keep_cols if c in tel.columns]]

        # Downsample early (HUGE speed win + smaller JSON)
        step=10
        if step and step > 1:
            tel = tel.iloc[::step].copy()

        tel["driver_number"] = drv
        tel["SessionTime"] = tel["SessionTime"].dt.total_seconds()
        all_tel.append(tel)

    car_data = pd.concat(all_tel, ignore_index=True)
    car_data = car_data[
    ["SessionTime"] + [c for c in car_data.columns if c != "SessionTime"]
    ]

    car_data = car_data.astype(object)
    car_data = car_data.where(pd.notna(car_data), None)
    car_data["driver_number"] = pd.to_numeric(car_data["driver_number"], errors="coerce").astype("Int64") # because FastF1 gives str

    car_data = car_data.drop(columns=['Time'])

    car_data["grid_position"] = car_data["driver_number"].astype(str).map(grid_positions)

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
    drivers = []
    for _, driver_row in drivers_df.iterrows():
        driver_info = {
            "driver_code": driver_row["name_acronym"],
            "driver_number": driver_row["driver_number"],
            "driver_fullName": driver_row["full_name"],
            "team_colour": driver_row["team_colour"],
            "positions_data": positions_data[positions_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "laps_data": laps_data[laps_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "stint_data": stint_data[stint_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "car_data": car_data[car_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "gap_data": gap_data[gap_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "pit_data": pit_data[pit_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
        }
        drivers.append(driver_info)

    finalJSON["drivers"] = drivers

    return JsonResponse(finalJSON, safe=False)

@lru_cache(maxsize=32)
def session_telemetry_view(request, year: int, country: str, session_name: str, step=10):
    session = fastf1.get_session(year, country, session_name)
    session.load()

    all_tel = []

    keep_cols = ["Time", "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS", "DistanceToDriverAhead", "DriverAhead"]

    # -- get telemetry data for all drivers
    print("-- Getting telemetry and laps data")
    for drv in session.drivers:
        print("Getting data for:",drv)
        laps = session.laps.pick_drivers(drv)  # pick_driver (singular) is the usual one
        tel = laps.get_telemetry().copy()

        # Reduce columns early
        tel = tel[[c for c in keep_cols if c in tel.columns]]

        # Downsample early (HUGE speed win + smaller JSON)
        if step and step > 1:
            tel = tel.iloc[::step].copy()

        tel["DriverNumber"] = drv
        tel["DriverCode"] = session.get_driver(drv)["Abbreviation"]
        tel["SessionTime"] = tel["Time"].dt.total_seconds()

        tel = add_lap_number_from_lapstarts(tel, laps)

        all_tel.append(tel)

    merged_tel = pd.concat(all_tel, ignore_index=True)

    # -- time bin (for comparison of rows by time bin instead of sessionTime -since there has to be a common column in time to compare to)
    print("-- doing time bin")
    bin_size = 0.2 # seconds

    merged_tel["TimeBin"] = (merged_tel["SessionTime"] / bin_size).round().astype("int64") # remember: time bin is not a measurement in seconds, it is a bin allocation
    merged_tel["TimeBinSize"] = bin_size

    # to ensure that there is only one driver per bin (by first sorting sessiontimes, get rows by timebin and drivernumber (whcih gets possible duplicates),
    #  and remove the other duplicates via .tail(1)
    # merged_tel = (
    # merged_tel.sort_values(["DriverNumber", "SessionTime"])
    #       .groupby(["TimeBin", "DriverNumber"], as_index=False)
    #       .tail(1)
    # )
    merged_tel = merged_tel.sort_values("SessionTime").drop_duplicates(
    subset=["TimeBin", "DriverNumber"], keep="last"
)

    # -- get additional details (e.g Grid positions ...) where applicable

    # > grid positions
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


    # -- apply additional details to main df

    # > grid positions
    print("-- grid positions")
    merged_tel["GridPosition"] = merged_tel["DriverNumber"].map(grid_positions)

    # > live positions
    print("-- live positions")
    # 1) Ensure one row per (TimeBin, DriverNumber): keep latest Time
    merged_tel = merged_tel.sort_values("Time").drop_duplicates(
        subset=["TimeBin", "DriverNumber"],
        keep="last"
    )

    # 2) Sort so that "ahead" rows come first within each TimeBin
    merged_tel = merged_tel.sort_values(
        ["TimeBin", "LapNumber", "Distance"],
        ascending=[True, False, False]
    )

    # 3) Assign positions 1..N within each TimeBin
    merged_tel["LivePosition"] = merged_tel.groupby("TimeBin").cumcount() + 1


    # > positions gained
    print("-- positions gained")
    diff = (merged_tel["GridPosition"] - merged_tel["LivePosition"]).round().astype("Int64")

    s = diff.astype("string")                 # "<NA>" supported
    merged_tel["PositionsGained"] = s.where(diff.notna(), None)  # nulls -> None
    merged_tel.loc[diff > 0, "PositionsGained"] = "+" + s[diff > 0]
    
    # -- clean dataframe ready for json
    print("-- preparing for json")
    cols = [
        "TimeBin", "TimeBinSize", "SessionTime",
        "GridPosition", "LivePosition", "PositionsGained", "LapNumber",
        "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS","DriverNumber","DriverCode"
    ]
    # 1) Select columns once
    df = merged_tel[[c for c in cols if c in merged_tel.columns]].copy()

    # 2) Clean once (vectorized)
    df = df.replace([np.inf, -np.inf], np.nan)

    # Convert numpy scalars -> python scalars + NaN->None in one go:
    # (this produces dtype=object, which is what you want for JSON)
    df = df.astype(object).where(df.notna(), None)

    print("-- get driver info")
    code_map = {int(d): session.get_driver(d)["Abbreviation"] for d in session.drivers}

    final = {code_map[int(drv)]: g.to_dict("records")
    for drv, g in df.groupby("DriverNumber", sort=False)}

    # Export to excel
    print("-- exporting to excel")
    #merged_tel.to_excel("test_tel.xlsx", index=False)

    return JsonResponse(final, safe=False)


@lru_cache(maxsize=32)
def session_laps_view(request, year: int, country: str, session: str):
    session = fastf1.get_session(year, country, session)
    session.load()

    finalJSON = {
        "drivers": []
    }

    columns = [
        "Time",
        "LapStartTime",
        "LapTime",
        "LapNumber",
        "Stint",
        "PitOutTime",
        "PitInTime",
        "Sector1Time",
        "Sector2Time",
        "Sector3Time",
        "Sector1SessionTime",
        "Sector2SessionTime",
        "Sector3SessionTime",
        "SpeedI1",
        "SpeedI2",
        "SpeedFL",
        "SpeedST",
        "IsPersonalBest",
        "Compound",
        "TyreLife",
        "FreshTyre",
        "Position",       # current position per lap (from Laps)
    ]

    drivers = []

    # Defensive guard in case results aren't available (e.g. practice)
    results = getattr(session, "results", None)

    for drv in session.drivers:
        laps = session.laps.pick_drivers(drv)[columns].copy()

        # Default: no grid position if results are missing
        grid_pos = None
        if results is not None and not results.empty:
            try:
                # SessionResults indexed by driver number; row has 'GridPosition'
                driver_result = results.loc[drv]
                grid_val = driver_result.get("GridPosition", None)
                if pd.notna(grid_val):
                    grid_pos = int(grid_val)
            except KeyError:
                grid_pos = None

        # Add GridPosition column (same value for all laps of that driver)
        laps["GridPosition"] = grid_pos

        # PositionsGainedString = "+3", "-1", "0", or None
        def compute_positions_gained_str(row):
            if grid_pos is None or pd.isna(row["Position"]):
                return None
            try:
                gained = int(grid_pos) - int(row["Position"])
                if gained > 0:
                    return f"+{gained}"
                elif gained < 0:
                    return f"{gained}"  # already has "-"
                else:
                    return "0"
            except (ValueError, TypeError):
                return None

        laps["PositionsGained"] = laps.apply(compute_positions_gained_str, axis=1)

        # Now convert to JSON-safe format
        df_clean = prepare_laps_df_for_json(laps)
        laps_json = df_clean.to_dict(orient="records")

        drivers.append({
            "driver_code": session.get_driver(drv)["Abbreviation"],
            "driver_fullName": session.get_driver(drv)["FullName"],
            "teamColour": session.get_driver(drv)["TeamColor"],
            "grid_position": grid_pos,  # useful to have at driver level too
            "data": laps_json
        })

    finalJSON["drivers"] = drivers

    return JsonResponse(finalJSON)

@lru_cache(maxsize=32)
def session_vrdetails_view(request, year: int, country: str, session_name: str):
    session = fastf1.get_session(year, country, session_name)

    session.load(telemetry=False)

    drivers = []
    teams = []

    results_df = session.results

    for _, row in results_df.iterrows():
        drivers.append(row.get("Abbreviation", ""),)
        teams.append(row.get("TeamName", ""))    

    teams = list(dict.fromkeys(teams))

    return JsonResponse({
         "drivers": drivers,
         "teams": teams,
         })

@lru_cache(maxsize=32)
def session_weather_view(request, year: int, country: str, session: str):
    session_obj = fastf1.get_session(year, country, session)

    session_obj.load(telemetry=False)

    weather_df = session_obj.laps.get_weather_data()

    if weather_df is None or weather_df.empty:
        return JsonResponse({"weather": []})

    # convert Time (timedelta) to seconds from session start and adds a column to the df
    weather_df = weather_df.copy()
    weather_df["TimeSec"] = weather_df["Time"].dt.total_seconds()

    rangeAirTemp = weather_df["AirTemp"].min().item(),weather_df["AirTemp"].max().item()
    rangeHumidity = weather_df["Humidity"].min().item(),weather_df["Humidity"].max().item()
    rangePressure = weather_df["Pressure"].min().item(),weather_df["Pressure"].max().item()
    rangeTrackTemp = weather_df["TrackTemp"].min().item(),weather_df["TrackTemp"].max().item()
    rangeWindSpeed = weather_df["WindSpeed"].min().item(),weather_df["WindSpeed"].max().item()


    samples = []
    for _, row in weather_df.iterrows():
        samples.append({
            "time_sec": float(row["TimeSec"]),         
            "air_temp": to_float_or_none(row["AirTemp"]),
            "track_temp": to_float_or_none(row["TrackTemp"]),
            "humidity": to_float_or_none(row["Humidity"]),
            "pressure": to_float_or_none(row["Pressure"]),
            "rainfall": to_float_or_none(row["Rainfall"]),
            "wind_dir": to_float_or_none(row["WindDirection"]),
            "wind_speed": to_float_or_none(row["WindSpeed"]),

        })

    return JsonResponse({
         "weather": samples,
         "rangeAirTemp": rangeAirTemp,
         "rangeHumidity": rangeHumidity,
         "rangePressure": rangePressure,
         "rangeTrackTemp": rangeTrackTemp,
         "rangeWindSpeed": rangeWindSpeed
         })

@lru_cache(maxsize=32)
def session_playback_view(request, year: int, country: str, session_name: str):
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    openf1_start = pd.to_datetime(session_df.loc[0, "date_start"], utc=True)
    openf1_end = pd.to_datetime(session_df.loc[0, "date_end"], utc=True)

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    circuit_info = session.get_circuit_info() # gets rotation angle, corner pos, numbers etc.

    fastf1_start = session.t0_date + session.session_start_time # gets the actual datetime of session start (first telemetry point)
    playbackControlOffset = (fastf1_start - session.t0_date).total_seconds() # in seconds
    fastf1_openf1_offset = (fastf1_start.replace(tzinfo=timezone.utc) - openf1_start).total_seconds() # in seconds. fastf1 is the later one

    # --- get session start time
    session_start_time = (
    session.t0_date
    .tz_localize("UTC")
    .strftime("%Y-%m-%dT%H:%M:%SZ")
)


    # --- build track polyline (using fastest lap of pole or just first driver) 
    ref_driver = session.drivers[0]
    ref_lap = session.laps.pick_drivers(ref_driver).pick_fastest()
    pos = ref_lap.get_pos_data()   # contains X, Y, Date, gives you a dataframe

    # pos.loc[row_selection, column_selection], : means all rows. so all X and Y only, and then turn into numpy
    track_xy = pos.loc[:, ['X', 'Y']].to_numpy()
    # it's converted to mumpy because it's fast at linear algebra, good for the rotate() and normalize_xy() func

    track_angle = circuit_info.rotation / 180 * np.pi # because np.cos and np.sin need radians
    track_rot = rotate(track_xy, angle=track_angle) # rotates all track points to recommended circuit rotation
    track_x, track_y = track_rot[:, 0], track_rot[:, 1] # split it into x y coords
    track_x, track_y = normalize_xy(track_x, track_y) # normalize to fit into a standard [-1, 1] box

    track_points = np.stack([track_x, track_y], axis=1).tolist() # combine xy back into normal list ready for JSON

    # --- build per-driver time series 
    drivers_payload = []

    for drv in session.drivers:
        drv_code = session.get_driver(drv)['Abbreviation']

        laps = session.laps.pick_drivers(drv) # pandas df
        if laps.empty:
            continue

        # Collect positions for all laps of this driver
        samples = []
        for _, lap in laps.iterrows(): # gives you index, row
            lap_obj = lap  # Series

            lap_pos = lap_obj.get_pos_data()
            t = lap_pos['SessionTime'].dt.total_seconds().to_numpy()

            xy = lap_pos[['X', 'Y']].to_numpy()
            xy_rot = rotate(xy, angle=track_angle)
            x, y = xy_rot[:, 0], xy_rot[:, 1]
            x, y = normalize_xy(x, y)

            lap_num = int(lap_obj['LapNumber'])

            # the zip basically gives t,x,y per row
            for ti, xi, yi in zip(t, x, y):
                samples.append({
                    "t": float(ti),
                    "lap": lap_num,
                    "x": float(xi),
                    "y": float(yi),
                })

        # ensures time is strictly increasing
        # sorted() needs a key because the data is complex
        # therefore uses a lambda func to get the time as the key per row in the samples array
        samples = sorted(samples, key=lambda s: s["t"])

        drivers_payload.append({
            "code": drv_code,
            "color": "#888888",  # you can map to team colors
            "samples": samples,
        })

    # --- calculation of race duration and total laps
    if drivers_payload:
        # gets race duration from the driver who finished last (basically)
        race_duration = max(
            sample["t"]
            for drv in drivers_payload
            for sample in drv["samples"]
        )
        # same concept
        # total_laps = max(
        #     sample["lap"]
        #     for drv in drivers_payload
        #     for sample in drv["samples"]
        # )
    else:
        race_duration = 0.0
        # total_laps = 0

    
    total_laps = int(session.laps['LapNumber'].max())

    return JsonResponse({
        "track": {"points": track_points},
        "drivers": drivers_payload,
        "raceDuration": race_duration,
        "totalLaps": total_laps,
        "playbackControlOffset" : playbackControlOffset,
        "sessionStart" : session_start_time
    })

@lru_cache(maxsize=32)
def results_view(request, year: int, country: str, session: str):
    sessionFF1 = fastf1.get_session(year, country, session)
    try:
        sessionFF1.load()
    except Exception as e:
        # If FastF1 itself fails to load the session
        return JsonResponse(
            {"error": f"Failed to load session data: {e}"},
            status=500,
        )

    # Base results (may be missing Position / BestLapTime / Laps for practice/quali)
    df = sessionFF1.results
    if df is None or df.empty:
        # No results; don't crash, just return empty
        return JsonResponse({"results": []})

    df = df.copy()

    # Ensure key columns exist
    if "BestLapTime" not in df.columns:
        df["BestLapTime"] = pd.NaT

    if "Laps" not in df.columns:
        df["Laps"] = pd.NA

    if "LastLapTime" not in df.columns:
        df["LastLapTime"] = pd.NA

    if "Position" not in df.columns:
        df["Position"] = pd.NA

    # ---------------------------
    # 1) Build per-driver data from laps
    # ---------------------------
    best_laps = None
    lap_counts = None
    last_laps = None

    try:
        laps = sessionFF1.laps  # <- this can raise DataNotLoadedError
        if laps is not None and not laps.empty:
            # Best lap per driver (only accurate laps with a LapTime)
            valid_laps = laps.pick_accurate().dropna(subset=["LapTime"])

            # Best lap per driver (only accurate, non-null LapTime)
            valid_laps = laps.pick_accurate().dropna(subset=["LapTime"])
            best_laps = (
                valid_laps
                .groupby("DriverNumber")["LapTime"]
                .min()
            )  # Series: DriverNumber -> Timedelta

            # Lap count per driver (use all laps with a LapTime)
            lap_counts = (
                laps
                .dropna(subset=["LapTime"])
                .groupby("DriverNumber")["LapNumber"]
                .count()
            )  # Series: DriverNumber -> int

            # Last lap per driver
            last_laps = (
            laps
            .dropna(subset=["LapTime"])
            .sort_values("LapNumber")
            .groupby("DriverNumber")["LapTime"]
            .last()
            )
    except Exception:
        # No lap data available for this session (common for very old seasons)
        best_laps = None
        lap_counts = None
        last_laps = None

    

    # ---------------------------
    # 2) Merge best lap + lap count into results df
    # ---------------------------
    if best_laps is not None:
        df = df.merge(
        best_laps.rename("BestSessionLapTime"),
        left_on="DriverNumber",
        right_index=True,
        how="left",
        )
        pd.set_option('future.no_silent_downcasting', True)
        # Ensure BestLapTime column exists; if not, create it
        if "BestLapTime" not in df.columns:
            df["BestLapTime"] = pd.NaT

        # Fill missing BestLapTime with our computed best session lap
        df["BestLapTime"] = df["BestLapTime"].fillna(df["BestSessionLapTime"])

    if lap_counts is not None:
        df = df.merge(
        lap_counts.rename("SessionLapCount"),
        left_on="DriverNumber",
        right_index=True,
        how="left",
        )
        # Ensure Laps column exists; if not, create it
        if "Laps" not in df.columns:
            df["Laps"] = pd.NA

        # Fill missing Laps with our computed session lap count
        df["Laps"] = df["Laps"].fillna(df["SessionLapCount"])

    if last_laps is not None:
        df = df.merge(
        last_laps.rename("FinalLapTime"),
        left_on="DriverNumber",
        right_index=True,
        how="left",
        )
        if "LastLapTime" not in df.columns:
            df["LastLapTime"] = pd.NaT



    # ---------------------------
    # 3) Create / fill Position when it's missing (practice etc.)
    # ---------------------------
    if "Position" not in df.columns:
        df["Position"] = pd.NA

    missing_pos_mask = df["Position"].isna()

    if missing_pos_mask.any() and df["BestLapTime"].notna().any():
        # Sort only the missing-position rows by best lap
        subset = (
            df.loc[missing_pos_mask]
            .sort_values("BestLapTime")
            .reset_index()
        )

        # Assign positions 1..N to them based on best lap order
        df.loc[subset["index"], "Position"] = range(1, len(subset) + 1)

    # ---------------------------
    # 4) Build JSON-friendly result list
    # ---------------------------
    results = []

    for _, row in df.iterrows():
        pos = row.get("Position", None)
        laps_val = row.get("Laps", None)
        points = row.get("Points", None)
        gridPos = row.get("GridPosition", None)

        results.append({
            "position": to_int_or_none(pos),
            "driverNumber": row.get("DriverNumber", ""),
            "abbreviation": row.get("Abbreviation", ""),
            "name": row.get("FullName", ""),
            "team": row.get("TeamName", ""),
            "team_color": row.get("TeamColor", ""),
            "headshot_url": row.get("HeadshotUrl", ""),
            "country_code": row.get("CountryCode", ""),
            "q1": format_lap_time(row.get("Q1")),
            "q2": format_lap_time(row.get("Q2")),
            "q3": format_lap_time(row.get("Q3")),
            # works for practice/quali/race now:
            "bestLapTime": format_lap_time(row.get("BestLapTime")),
            "lastLapTime": format_lap_time(row.get("FinalLapTime")),
            "status": row.get("Status", ""),
            # this now also filled for practice + quali:
            "numberOfLaps": to_int_or_none(laps_val),
            "points": to_int_or_none(points),
            "gridPos": to_int_or_none(gridPos),
        })

    return JsonResponse({"results": results})


# --- Helpers

def to_str_or_none(value):
    if pd.isna(value):
        return None
    return str(value)

def to_int_or_none(value):
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def format_lap_time(value):
    if pd.isna(value) or value is None:
        return None

    # make sure it's a Timedelta-like object
    if isinstance(value, pd.Timedelta):
        total_seconds = value.total_seconds()
    else:
        try:
            # sometimes it might already be a float seconds value
            total_seconds = float(value)
        except (TypeError, ValueError):
            return str(value)

    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60  # includes fractional part

    # M:SS.mmm  (e.g. 1:15.912)
    return f"{minutes}:{seconds:06.3f}"

def to_float_or_none(value):
        if pd.isna(value):
            return None
        return float(value)

def prepare_laps_df_for_json(df: pd.DataFrame):
    df = df.copy()

    timedelta_cols = [
        "Time",
        "LapTime",
        "PitOutTime",
        "PitInTime",
        "Sector1Time",
        "Sector2Time",
        "Sector3Time",
    ]
    for col in timedelta_cols:
        if col in df:
            df[col] = df[col].apply(
                lambda x: x.total_seconds() if pd.notna(x) else None
            )

    timestamp_cols = [
        "LapStartTime",
        "Sector1SessionTime",
        "Sector2SessionTime",
        "Sector3SessionTime",
    ]
    for col in timestamp_cols:
        if col in df:
            df[col] = df[col].apply(
                lambda x: x.total_seconds() if pd.notna(x) else None
            )

    # Convert numpy scalar types → Python native
    df = df.map(lambda x: x.item() if hasattr(x, "item") else x)

    df = df.replace({np.nan: None})

    return df

def add_lap_number_from_lapstarts(tel: pd.DataFrame, laps_drv: pd.DataFrame) -> pd.DataFrame:
    """
    tel: telemetry for ONE driver, must include column 'Time'
    laps_drv: session.laps filtered to ONE driver, must include 'LapNumber' and 'LapStartTime'
    """
    print("adding lap data to the tel data")
    tel = tel.sort_values("Time").copy()

    lapstarts = (
        laps_drv[["LapNumber", "LapStartTime"]]
        .dropna()
        .sort_values("LapStartTime")
        .copy()
    )

    # Assign the latest lap start that is <= telemetry time
    tel = pd.merge_asof(
        tel,
        lapstarts,
        left_on="Time",
        right_on="LapStartTime",
        direction="backward",
        allow_exact_matches=True,
    )

    return tel

def assign_live_position_from_lap_distance(df_bin: pd.DataFrame) -> pd.DataFrame:
    print("assining the live positions")
    df_bin = df_bin.copy()

    # You want exactly one row per driver per TimeBin.
    # If you have multiple samples per driver per bin, keep the latest sample.
    df_bin = df_bin.sort_values("Time").drop_duplicates(subset=["DriverNumber"], keep="last")

    # Sort "front to back"
    df_bin = df_bin.sort_values(["LapNumber", "Distance"], ascending=[False, False])

    df_bin["LivePosition"] = range(1, len(df_bin) + 1)
    return df_bin

def clean_for_json(obj):
    print("-- cleaning json")
    """Recursively replace NaN/Inf with None so JSON is valid."""
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (np.floating,)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    return obj

# --- Template Views

def _parse_bool(s: str) -> bool:
    return str(s).lower() in ("1", "true", "yes", "on")


def _parse_csv_param(request, name: str) -> list[str]:
    raw = request.GET.get(name, "")
    return [x.strip().upper() for x in raw.split(",") if x.strip()]

@csrf_exempt
def vr_create_view(request):
    body = json.loads(request.body)
    template_id = body["templateId"]
    year = int(body["year"])
    country = body["country"]
    session_name = body["session_name"]
    inputs = body.get("inputs", {})

    if template_id == "t1":
        return vr_pace_1(year, country, session_name, inputs)
    elif template_id == "t2":
        return vr_pace_2(year, country, session_name, inputs)
    elif template_id == "t3":
        return vr_pace_3(year, country, session_name, inputs)
    elif template_id == "t4":
        return vr_pace_4(year, country, session_name, inputs)
    elif template_id == "t23":
        return vr_positions_3(inputs)


    return JsonResponse({"error": "Unknown templateId"}, status=400)

# -	Driver laptimes (scatterplot)
def vr_pace_1(year, country, session_name, inputs):
    drivers = inputs.get("drivers", [])
    exclude_sc = _parse_bool(inputs.get("excludeSCVSC", False))

    # 1) Load session
    try:
        session = fastf1.get_session(year, country, session_name)
        session.load(laps=True, telemetry=False, weather=False)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to load session: {e}")

    laps = session.laps.copy()

    # 2) Filter to selected drivers
    laps = laps[laps["Driver"].isin(drivers)]

    # 3) Keep only laps with a valid LapTime
    laps = laps[laps["LapTime"].notna()]

    # 4) Exclude SC/VSC laps (only if column exists in your laps data)
    # FastF1 can vary by session/year; keep this defensive.
    if exclude_sc and "TrackStatus" in laps.columns:
        # TrackStatus is typically a string of marshalling flags.
        # This is a best-effort filter; adjust if you have a more reliable SC/VSC indicator.
        laps = laps[~laps["TrackStatus"].astype(str).str.contains("4|5", regex=True)]

    # 5) Convert LapTime (Timedelta) -> seconds float (JSON-friendly)
    # FastF1 LapTime is usually pandas Timedelta
    if pd.api.types.is_timedelta64_dtype(laps["LapTime"]):
        laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    else:
        # Fallback if it comes already numeric/string
        laps["LapTimeSeconds"] = pd.to_numeric(laps["LapTime"], errors="coerce")
        laps = laps[laps["LapTimeSeconds"].notna()]

    # 6) Build Plotly scatter
    fig = px.scatter(
        laps,
        x="LapNumber",
        y="LapTimeSeconds",
        color="Driver",
        title=f"{year} {country} {session_name} — Driver laptimes",
        labels={"LapNumber": "Lap", "LapTimeSeconds": "Lap time (s)"},
        hover_data=[c for c in ["Compound", "Stint", "TyreLife"] if c in laps.columns],
    )

    # Optional: make “faster = higher” by reversing y-axis (some people prefer this)
    # fig.update_yaxes(autorange="reversed")

    fig.update_layout(
        margin=dict(l=40, r=20, t=60, b=40),
        legend_title_text="Driver",
    )

    # 7) Convert figure to JSON-safe dict and return
    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "title": "Driver laptimes (scatter)",
        "result": {
            "type": "plotly",
            "figure": figure_dict,
        },
    }

    return JsonResponse(payload)

# - Driver laptimes (distribution chart)
def vr_pace_2(year, country, session_name, inputs):
    drivers = inputs.get("drivers", [])
    exclude_sc = _parse_bool(inputs.get("excludeSCVSC", False))
    show_points = _parse_bool(inputs.get("showPoints", True))

    # 1) Load session
    try:
        session = fastf1.get_session(year, country, session_name)
        session.load(laps=True, telemetry=False, weather=False)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to load session: {e}")

    laps = session.laps.copy()

    # 2) Filter to selected drivers (if provided)
    if drivers:
        laps = laps[laps["Driver"].isin(drivers)]

    # 3) Keep only laps with valid LapTime
    laps = laps[laps["LapTime"].notna()].copy()
    if laps.empty:
        return HttpResponseBadRequest("No valid laptimes found after filtering.")

    # 4) Exclude SC/VSC laps (defensive; TrackStatus can vary)
    if exclude_sc and "TrackStatus" in laps.columns:
        laps = laps[~laps["TrackStatus"].astype(str).str.contains("4|5", regex=True)]

    if laps.empty:
        return HttpResponseBadRequest("No laptimes left after SC/VSC filtering.")

    # 5) Convert LapTime (Timedelta) -> seconds float (JSON-friendly)
    if pd.api.types.is_timedelta64_dtype(laps["LapTime"]):
        laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    else:
        laps["LapTimeSeconds"] = pd.to_numeric(laps["LapTime"], errors="coerce")
        laps = laps[laps["LapTimeSeconds"].notna()]

    if laps.empty:
        return HttpResponseBadRequest("LapTime could not be converted to seconds.")

    # 6) Distribution chart (violin per driver)
    fig = px.violin(
        laps,
        x="Driver",
        y="LapTimeSeconds",
        box=True,  # show embedded boxplot
        points="all" if show_points else False,
        title=f"{year} {country} {session_name} — Driver laptime distribution",
        labels={"Driver": "Driver", "LapTimeSeconds": "Lap time (s)"},
        hover_data=[c for c in ["Compound", "Stint", "TyreLife", "LapNumber"] if c in laps.columns],
    )

    fig.update_layout(
        margin=dict(l=40, r=20, t=60, b=40),
        xaxis_title="Driver",
        yaxis_title="Lap time (s)",
    )

    # Optional: make faster times appear higher
    # fig.update_yaxes(autorange="reversed")

    # 7) Convert figure to JSON-safe dict and return
    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "title": "Driver laptimes (distribution)",
        "result": {
            "type": "plotly",
            "figure": figure_dict,
        },
    }

    return JsonResponse(payload)

# -	Lap time trend (line chart)
def vr_pace_3(year, country, session_name, inputs):
    drivers = inputs.get("drivers", [])
    exclude_sc = _parse_bool(inputs.get("excludeSCVSC", False))

    # 1) Load session
    try:
        session = fastf1.get_session(year, country, session_name)
        session.load(laps=True, telemetry=False, weather=False)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to load session: {e}")

    laps = session.laps.copy()

    # 2) Filter to selected drivers
    laps = laps[laps["Driver"].isin(drivers)]

    # 3) Keep only laps with a valid LapTime
    laps = laps[laps["LapTime"].notna()]

    # 4) Exclude SC/VSC laps (only if column exists in your laps data)
    # FastF1 can vary by session/year; keep this defensive.
    if exclude_sc and "TrackStatus" in laps.columns:
        # TrackStatus is typically a string of marshalling flags.
        # This is a best-effort filter; adjust if you have a more reliable SC/VSC indicator.
        laps = laps[~laps["TrackStatus"].astype(str).str.contains("4|5", regex=True)]

    # 5) Convert LapTime (Timedelta) -> seconds float (JSON-friendly)
    # FastF1 LapTime is usually pandas Timedelta
    if pd.api.types.is_timedelta64_dtype(laps["LapTime"]):
        laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    else:
        # Fallback if it comes already numeric/string
        laps["LapTimeSeconds"] = pd.to_numeric(laps["LapTime"], errors="coerce")
        laps = laps[laps["LapTimeSeconds"].notna()]

    # 6) Build Plotly line chart
    fig = px.line(
        laps,
        x="LapNumber",
        y="LapTimeSeconds",
        color="Driver",
        title=f"{year} {country} {session_name} — Driver laptimes",
        labels={"LapNumber": "Lap", "LapTimeSeconds": "Lap time (s)"},
        hover_data=[c for c in ["Compound", "Stint", "TyreLife"] if c in laps.columns],
    )

    # Optional: make “faster = higher” by reversing y-axis (some people prefer this)
    # fig.update_yaxes(autorange="reversed")

    fig.update_layout(
        margin=dict(l=40, r=20, t=60, b=40),
        legend_title_text="Driver",
    )

    # 7) Convert figure to JSON-safe dict and return
    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "title": "Driver laptimes (line chart)",
        "result": {
            "type": "plotly",
            "figure": figure_dict,
        },
    }

    return JsonResponse(payload)

# -	Sector time breakdown (S1/S2/S3 per driver) (grouped bar chart/line chart)
def vr_pace_4(year, country, session_name, inputs):
    drivers = inputs.get("drivers", [])
    exclude_sc = _parse_bool(inputs.get("excludeSCVSC", False))

    # 1) Load session
    try:
        session = fastf1.get_session(year, country, session_name)
        session.load(laps=True, telemetry=False, weather=False)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to load session: {e}")

    laps = session.laps.copy()

    # 2) Filter to selected drivers (if provided)
    if drivers:
        laps = laps[laps["Driver"].isin(drivers)]

    # 3) Ensure sector columns exist
    sector_cols = ["Sector1Time", "Sector2Time", "Sector3Time"]
    missing = [c for c in sector_cols if c not in laps.columns]
    if missing:
        return HttpResponseBadRequest(
            f"Sector columns missing in this session data: {missing}"
        )

    # 4) Exclude SC/VSC laps (best-effort defensive)
    if exclude_sc and "TrackStatus" in laps.columns:
        laps = laps[~laps["TrackStatus"].astype(str).str.contains("4|5", regex=True)]

    # 5) Keep only laps with all 3 sector times
    for c in sector_cols:
        laps = laps[laps[c].notna()]

    if laps.empty:
        return HttpResponseBadRequest(
            "No laps available after filtering (sectors missing/filtered out)."
        )

    # 6) Convert sector timedeltas to seconds
    for c in sector_cols:
        out = c + "Seconds"
        if pd.api.types.is_timedelta64_dtype(laps[c]):
            laps[out] = laps[c].dt.total_seconds()
        else:
            laps[out] = pd.to_numeric(laps[c], errors="coerce")
            laps = laps[laps[out].notna()]

    s1, s2, s3 = "Sector1TimeSeconds", "Sector2TimeSeconds", "Sector3TimeSeconds"

    # 7) Aggregate per driver
    cols = [s1, s2, s3]
    grp = laps.groupby("Driver", as_index=False)[cols].median()
    agg_label = "Median"

    if grp.empty:
        return HttpResponseBadRequest("No aggregated sector data to plot.")

    # Optional: stable ordering (fastest total first)
    grp["TotalSeconds"] = grp[s1] + grp[s2] + grp[s3]
    grp = grp.sort_values("TotalSeconds", ascending=True)

    # 8) Build grouped bar chart + line overlay
    sectors = ["Sector 1", "Sector 2", "Sector 3"]
    fig = go.Figure()

    for _, row in grp.iterrows():
        drv = row["Driver"]

        s1 = row["Sector1TimeSeconds"]
        s2 = row["Sector2TimeSeconds"]
        s3 = row["Sector3TimeSeconds"]

        cumulative = [s1, s1 + s2, s1 + s2 + s3]

        # Bars: sector times
        fig.add_trace(go.Bar(
            name=drv,
            x=sectors,
            y=[s1, s2, s3],
            legendgroup=drv,
            hovertemplate=(
                "Driver=%{fullData.name}<br>"
                "%{x}=%{y:.3f}s<extra></extra>"
            ),
        ))

        # Line overlay: cumulative total
        fig.add_trace(go.Scatter(
            name=f"{drv} total",
            x=sectors,
            y=cumulative,
            mode="lines+markers",
            yaxis="y2",
            legendgroup=drv,
            showlegend=False,  # prevents legend spam
            hovertemplate=(
                "Driver=" + drv + "<br>"
                "Cumulative=%{y:.3f}s<extra></extra>"
            ),
        ))
        
    fig.update_layout(
        title=f"Sector time breakdown (S1/S2/S3 per driver) — grouped bar chart",
        barmode="group",
        xaxis=dict(title="Sector", type="category"),
        yaxis=dict(title="Sector time (s)"),
        yaxis2=dict(
            title="Cumulative time (s)",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend_title_text="Driver",
    )

    # 9) Convert to JSON-safe dict and return
    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "title": "Sector time breakdown (S1/S2/S3 per driver) — grouped bar chart",
        "result": {"type": "plotly", "figure": figure_dict}
    }

    return JsonResponse(payload)


def _ergast_to_df(resp):
    # supports resp.content[0], resp.df, or DataFrame directly
    if resp is None:
        return None
    if isinstance(resp, pd.DataFrame):
        return resp
    if hasattr(resp, "content"):
        c = resp.content
        if isinstance(c, (list, tuple)) and len(c) > 0:
            return c[0] if isinstance(c[0], pd.DataFrame) else pd.DataFrame(c[0])
    if hasattr(resp, "df") and isinstance(resp.df, pd.DataFrame):
        return resp.df
    try:
        return pd.DataFrame(resp)
    except Exception:
        return None


def vr_positions_3(inputs):
    # --- Inputs ---
    SEASON = int(inputs.get("season", 2024))
    ROUND = int(inputs.get("round", 1))

    ergast = Ergast()

    # 1) standings
    try:
        standings = ergast.get_driver_standings(season=SEASON, round=ROUND)
        driver_standings = _ergast_to_df(standings)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to fetch driver standings: {e}")

    if driver_standings is None or driver_standings.empty:
        return HttpResponseBadRequest("No driver standings returned.")

    # normalize
    for col in ["position", "points", "givenName", "familyName"]:
        if col not in driver_standings.columns:
            return HttpResponseBadRequest(f"Standings missing '{col}' column.")

    driver_standings = driver_standings.copy()
    driver_standings["points"] = pd.to_numeric(driver_standings["points"], errors="coerce")
    driver_standings["position_num"] = pd.to_numeric(driver_standings["position"], errors="coerce")
    driver_standings = driver_standings.dropna(subset=["points", "position_num"])
    driver_standings = driver_standings.sort_values("position_num").reset_index(drop=True)

    # 2) remaining points model (same as FastF1 example)
    POINTS_FOR_SPRINT = 8 + 25          # sprint win + race win
    POINTS_FOR_CONVENTIONAL = 25        # race win

    try:
        events = fastf1.events.get_event_schedule(SEASON, backend="ergast").copy()
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to fetch event schedule: {e}")

    if "RoundNumber" not in events.columns or "EventFormat" not in events.columns:
        return HttpResponseBadRequest("Event schedule missing RoundNumber/EventFormat.")

    events["RoundNumber"] = pd.to_numeric(events["RoundNumber"], errors="coerce")
    events = events.dropna(subset=["RoundNumber"])
    remaining = events[events["RoundNumber"] > ROUND]

    sprint_events = int((remaining["EventFormat"] == "sprint_shootout").sum())
    conventional_events = int((remaining["EventFormat"] == "conventional").sum())

    max_points_remaining = sprint_events * POINTS_FOR_SPRINT + conventional_events * POINTS_FOR_CONVENTIONAL

    # 3) compute table rows
    leader_points = int(driver_standings.loc[0, "points"])

    out = driver_standings.copy()
    out["Driver"] = out["givenName"].astype(str) + " " + out["familyName"].astype(str)
    out["CurrentPoints"] = out["points"].round(0).astype(int)
    out["TheoreticalMax"] = (out["CurrentPoints"] + int(max_points_remaining)).astype(int)
    out["CanWin"] = out["TheoreticalMax"].apply(lambda p: "Yes" if p >= leader_points else "No")

    # sort: can win first, then points desc
    out["CanWinSort"] = out["CanWin"].map({"Yes": 0, "No": 1})
    out = out.sort_values(["CanWinSort", "CurrentPoints"], ascending=[True, False]).drop(columns=["CanWinSort"])

    # 4) build plotly Table figure
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=["Rank", "Driver", "Points", "Theoretical Max", "Can still win?"],
                    align="left",
                ),
                cells=dict(
                    values=[
                        out["position"].tolist(),
                        out["Driver"].tolist(),
                        out["CurrentPoints"].tolist(),
                        out["TheoreticalMax"].tolist(),
                        out["CanWin"].tolist(),
                    ],
                    align="left",
                ),
            )
        ]
    )

    fig.update_layout(
        title=f"{SEASON} — WDC still possible after Round {ROUND} (max remaining points={int(max_points_remaining)})",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    # 5) JSON-safe payload (same shape as your scatter example)
    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "title": "Who can still win the WDC? (table)",
        "result": {
            "type": "plotly",
            "figure": figure_dict,
        },
        "meta": {
            "season": SEASON,
            "round": ROUND,
            "max_points_remaining": int(max_points_remaining),
            "sprint_events_remaining": sprint_events,
            "conventional_events_remaining": conventional_events,
        },
    }

    return JsonResponse(payload)