from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from api.models import Season, Event, Session
import fastf1
import pandas as pd 
import numpy as np
from functools import lru_cache
from api.helpers.geometry import rotate, normalize_xy
import json
from urllib.request import urlopen
from datetime import timezone
from api.helpers.raceviewer import (
    add_lap_number_from_lapstarts,
    prepare_laps_df_for_json,to_float_or_none,
    to_int_or_none,
    format_lap_time)

__all__ = [
    "season_years",
    "season_countries",
    "season_sessions",
    "session_circuit",
    "session_teamradio_view",
    "session_racecontrol_view",
    "session_leaderboard_view",
    "session_laps_view",
    "session_weather_view",
    "session_playback_view",
    "results_view"
]

fastf1.Cache.enable_cache("api/fastf1_cache")

def season_years(request):
    """
    Returns a list of available season years in descending order.

    The data is retrieved from the Season model and used to populate
    frontend selection components.

    Args:
        request: HTTP request object.

    Returns:
        JsonResponse: List of season years ordered from most recent to oldest.
    """
    years = (
        Season.objects
        .order_by('-year')
        .values_list('year', flat=True)
    )
    return JsonResponse({"years":list(years)})

def season_countries(request, year):
    """
    Returns the list of countries for a given season year.

    Event data is filtered by season and reduced to distinct country names
    to support race selection in the frontend.

    Args:
        request: HTTP request object.
        year (int): Season year.

    Returns:
        JsonResponse: List of unique countries for the specified season.
    """
    countries = (
        Event.objects
        .filter(season__year=year)
        .values_list('country', flat=True)
        .distinct()
    )
    return JsonResponse({"countries": list(countries)})

def season_sessions(request, year, country):
    """
    Returns the available session types for a given race weekend.

    Sessions are filtered by season year and country, then reduced to a
    distinct, ordered list to populate frontend selection options.

    Args:
        request: HTTP request object.
        year (int): Season year.
        country (str): Grand Prix location.

    Returns:
        JsonResponse: List of session types for the specified event.
    """
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
    """
    Returns the circuit name for a given season and race location.

    The event is queried with its related circuit to avoid additional
    database lookups. If no matching event is found, an error is returned.

    Args:
        request: HTTP request object.
        year (int): Season year.
        country (str): Grand Prix location.

    Returns:
        JsonResponse: Circuit name for the specified event, or an error if
        no event exists.
    """
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
    """
    Retrieves and formats team radio messages for a given session using OpenF1 data.

    Session metadata is first obtained to identify the session key, after which
    team radio events are fetched and aligned to session-relative time using
    FastF1 timing references. The data is then cleaned and structured for
    frontend playback.

    Args:
        request: HTTP request object.
        year (int): Race year.
        country (str): Grand Prix location.
        session_name (str): Session type.

    Returns:
        JsonResponse: List of team radio messages with timestamps aligned to
        session time, formatted for playback.
    """
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
    """
    Builds the session leaderboard dataset used by the race playback view.

    The function combines OpenF1 timing feeds with FastF1 telemetry to
    assemble per-driver position, lap, stint, pit, gap and car data, all
    aligned to a common session time reference before being returned in a
    frontend-ready structure.

    Args:
        request: HTTP request object.
        year (int): Race year.
        country (str): Grand Prix location.
        session_name (str): Session type.

    Returns:
        JsonResponse: Driver-level leaderboard and telemetry data for the
        selected session, formatted for playback.
    """
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

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
        tel = laps.get_telemetry(frequency=10).copy() # downsampled

        # reduce columns early
        tel = tel[[c for c in keep_cols if c in tel.columns]]

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
def session_laps_view(request, year: int, country: str, session: str):
    """
    Returns lap-by-lap session data for each driver.

    FastF1 lap data is loaded per driver and extended with derived fields
    such as grid position and positions gained relative to the start. The
    result is then cleaned and structured for frontend use.

    Args:
        request: HTTP request object.
        year (int): Race year.
        country (str): Grand Prix location.
        session (str): Session type.

    Returns:
        JsonResponse: Driver-level lap data for the selected session,
        formatted for JSON output.
    """

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

    results = getattr(session, "results", None)

    for drv in session.drivers:
        laps = session.laps.pick_drivers(drv)[columns].copy()

        grid_pos = None
        if results is not None and not results.empty:
            try:
                driver_result = results.loc[drv]
                grid_val = driver_result.get("GridPosition", None)
                if pd.notna(grid_val):
                    grid_pos = int(grid_val)
            except KeyError:
                grid_pos = None

        laps["GridPosition"] = grid_pos

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

        # convert to JSON-safe format
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
def session_weather_view(request, year: int, country: str, session: str):
    """Return weather data of a race given its year, country and session via FastF1.

    Args:
        request: HTTP request object
        year (int): Year for which to retrieve weather data
        country (str): Country for which to retrieve weather data
        session (str): Session name for which to retrieve weather data
    """
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
    """
    Builds the core playback dataset for a given session.

    OpenF1 and FastF1 session data are combined to align timing, generate a
    normalised track map, and produce per-driver position samples for race
    playback. The response also includes overall session values such as race
    duration, lap count and playback timing offsets.

    Args:
        request: HTTP request object.
        year (int): Race year.
        country (str): Grand Prix location.
        session_name (str): Session type.

    Returns:
        JsonResponse: Track geometry, per-driver playback samples, and
        session-level timing metadata for the selected session.
    """

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

        # collect positions for all laps of this driver
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
    """
    Returns the classified session results for a given event.

    FastF1 result data is loaded and supplemented with lap-derived values
    where required, including best lap time, final lap time, lap count and
    position when these are missing from the base dataset. The result is then
    formatted into a consistent JSON structure for frontend display.

    Args:
        request: HTTP request object.
        year (int): Race year.
        country (str): Grand Prix location.
        session (str): Session type.

    Returns:
        JsonResponse: Structured session results for each driver, or an
        error response if the session data cannot be loaded.
    """
    sessionFF1 = fastf1.get_session(year, country, session)
    try:
        sessionFF1.load()
    except Exception as e:
        return JsonResponse(
            {"error": f"Failed to load session data: {e}"},
            status=500,
        )

    df = sessionFF1.results
    if df is None or df.empty:
        return JsonResponse({"results": []})

    df = df.copy()

    # ensure key columns exist
    if "BestLapTime" not in df.columns:
        df["BestLapTime"] = pd.NaT

    if "Laps" not in df.columns:
        df["Laps"] = pd.NA

    if "LastLapTime" not in df.columns:
        df["LastLapTime"] = pd.NA

    if "Position" not in df.columns:
        df["Position"] = pd.NA

    # -- build per-driver data from laps
    best_laps = None
    lap_counts = None
    last_laps = None

    try:
        laps = sessionFF1.laps  # <- this can raise DataNotLoadedError
        if laps is not None and not laps.empty:
            valid_laps = laps.pick_accurate().dropna(subset=["LapTime"])
            best_laps = (
                valid_laps
                .groupby("DriverNumber")["LapTime"]
                .min()
            ) 

            lap_counts = (
                laps
                .dropna(subset=["LapTime"])
                .groupby("DriverNumber")["LapNumber"]
                .count()
            ) 

            # last lap per driver
            last_laps = (
            laps
            .dropna(subset=["LapTime"])
            .sort_values("LapNumber")
            .groupby("DriverNumber")["LapTime"]
            .last()
            )
    except Exception:
        best_laps = None
        lap_counts = None
        last_laps = None

    # -- merge best lap + lap count into results df
    if best_laps is not None:
        df = df.merge(
        best_laps.rename("BestSessionLapTime"),
        left_on="DriverNumber",
        right_index=True,
        how="left",
        )
        pd.set_option('future.no_silent_downcasting', True)
        if "BestLapTime" not in df.columns:
            df["BestLapTime"] = pd.NaT

        df["BestLapTime"] = df["BestLapTime"].fillna(df["BestSessionLapTime"])

    if lap_counts is not None:
        df = df.merge(
        lap_counts.rename("SessionLapCount"),
        left_on="DriverNumber",
        right_index=True,
        how="left",
        )
        if "Laps" not in df.columns:
            df["Laps"] = pd.NA

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



    # -- create / fill position when it's missing
    if "Position" not in df.columns:
        df["Position"] = pd.NA

    missing_pos_mask = df["Position"].isna()

    if missing_pos_mask.any() and df["BestLapTime"].notna().any():
        subset = (
            df.loc[missing_pos_mask]
            .sort_values("BestLapTime")
            .reset_index()
        )

        df.loc[subset["index"], "Position"] = range(1, len(subset) + 1)

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