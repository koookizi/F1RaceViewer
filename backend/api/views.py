from django.shortcuts import render
from django.http import JsonResponse
from api.models import Season, Event, Session
import fastf1
import math
import pandas as pd 
import numpy as np
from functools import lru_cache
from .helpers.geometry import rotate, normalize_xy
import json
from datetime import datetime
from urllib.request import urlopen
from datetime import timezone


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
    event = Event.objects.filter(
        season__year=year,
        country=country
    ).first()
    if not event:
        return JsonResponse({"error": "Event not found"}, status=404)

    return JsonResponse({"circuit": event.circuit})

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
        "playbackControlOffset" : playbackControlOffset
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


# Helpers
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