from django.shortcuts import render
from django.http import JsonResponse
from api.models import Season, Event, Session
import fastf1
import pandas as pd 
import numpy as np

from .helpers.geometry import rotate, normalize_xy


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

def session_circuit(request, year: int, country: str):
    event = Event.objects.filter(
        season__year=year,
        country=country
    ).first()
    if not event:
        return JsonResponse({"error": "Event not found"}, status=404)

    return JsonResponse({"circuit": event.circuit})

def session_playback_view(request, year: int, country: str, session: str):
    session = fastf1.get_session(year, country, session)
    session.load()

    circuit_info = session.get_circuit_info()

    # ---- Build track polyline (using fastest lap of pole or just first driver) ----
    ref_driver = session.drivers[0]
    ref_lap = session.laps.pick_driver(ref_driver).pick_fastest()
    pos = ref_lap.get_pos_data()   # contains X, Y, Date

    track_xy = pos.loc[:, ['X', 'Y']].to_numpy()
    track_angle = circuit_info.rotation / 180 * np.pi
    track_rot = rotate(track_xy, angle=track_angle)
    track_x, track_y = track_rot[:, 0], track_rot[:, 1]
    track_x, track_y = normalize_xy(track_x, track_y)

    track_points = np.stack([track_x, track_y], axis=1).tolist()

    # ---- Build per-driver time series ----
    drivers_payload = []

    for drv in session.drivers:
        drv_code = session.get_driver(drv)['Abbreviation']

        laps = session.laps.pick_drivers(drv)
        if laps.empty:
            continue

        # Collect positions for all laps of this driver
        samples = []
        for _, lap in laps.iterrows():
            lap_obj = lap  # Series

            lap_pos = lap_obj.get_pos_data()
            t = lap_pos['SessionTime'].dt.total_seconds().to_numpy()

            xy = lap_pos[['X', 'Y']].to_numpy()
            xy_rot = rotate(xy, angle=track_angle)
            x, y = xy_rot[:, 0], xy_rot[:, 1]
            x, y = normalize_xy(x, y)

            lap_num = int(lap_obj['LapNumber'])

            for ti, xi, yi in zip(t, x, y):
                samples.append({
                    "t": float(ti),
                    "lap": lap_num,
                    "x": float(xi),
                    "y": float(yi),
                })

        # Optionally sort + downsample to reduce size
        samples = sorted(samples, key=lambda s: s["t"])

        drivers_payload.append({
            "code": drv_code,
            "color": "#888888",  # you can map to team colors
            "samples": samples,
        })

    
    if drivers_payload:
        race_duration = max(
            sample["t"]
            for drv in drivers_payload
            for sample in drv["samples"]
        )
        total_laps = max(
            sample["lap"]
            for drv in drivers_payload
            for sample in drv["samples"]
        )
    else:
        race_duration = 0.0
        total_laps = 0


    total_laps = int(session.laps['LapNumber'].max())

    return JsonResponse({
        "track": {"points": track_points},
        "drivers": drivers_payload,
        "raceDuration": race_duration,
        "totalLaps": total_laps,
    })

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