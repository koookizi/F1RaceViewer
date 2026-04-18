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

import numpy as np

def rotate(xy, angle: float):
    """
    Applies a rotation to 2D track coordinates.

    A custom rotation matrix is used to match the FastF1 coordinate system,
    which differs from the standard mathematical convention.

    Args:
        xy: Array of x/y coordinate pairs.
        angle (float): Rotation angle in radians.

    Returns:
        np.ndarray: Rotated coordinates.
    """

    # uses a rotation matrix (not standard as coordinate system of FastF1 is flipped, and it is clockwise rotation, not anticlockwise)
    rot_mat = np.array([[np.cos(angle), np.sin(angle)],
                        [-np.sin(angle), np.cos(angle)]])
    return np.matmul(xy, rot_mat)

def normalize_xy(x, y):
    """
    Normalises track coordinates for consistent visual scaling.

    Coordinates are centred using the mean and scaled based on the largest
    axis range so that the track fits within a standardised view.

    Args:
        x: Array of x coordinates.
        y: Array of y coordinates.

    Returns:
        tuple: Normalised x and y coordinate arrays.
    """
    # ensure that they are an array of floats
    x = np.asarray(x, dtype="float64")
    y = np.asarray(y, dtype="float64")

    # mask out NaNs / infs
    mask = np.isfinite(x) & np.isfinite(y)
    if not mask.any():
        # nothing usable, just return zeros so it doesn't crash
        return np.zeros_like(x), np.zeros_like(y)

    # works on a valid subset
    x_valid = x[mask]
    y_valid = y[mask]

    # centers the track using the mean
    # why mean? it gets the centre of a group of points basically
    # if u did (max+min)/2 it will break when the shape isn't symmetrical
    x_center = x_valid.mean()
    y_center = y_valid.mean()
    x = x - x_center # when subtracting the center (mean), it basically centres the data around that
    y = y - y_center

    # to see how wide or tall the track is
    max_extent = max(
        float(x_valid.max() - x_valid.min()),
        float(y_valid.max() - y_valid.min()),
    )

    if not np.isfinite(max_extent) or max_extent == 0.0: # basically, if it were invalid
        # avoid divide-by-zero; keep centered but unscaled
        return x, y

    # now scale x and y to fit roughly in [-1,1]
    x = x / max_extent * 2.0
    y = y / max_extent * 2.0
    return x, y


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
    })

print(session_playback_view(None, 2026, "Australia", "Race"))