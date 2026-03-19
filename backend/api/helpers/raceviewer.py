import math
import pandas as pd 
import numpy as np

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
    """
    Formats a lap time value into a readable minute-second string.

    The function accepts either a pandas Timedelta or a numeric value in
    seconds and returns it in lap-time format.

    Args:
        value: Lap time value.

    Returns:
        str | None: Formatted lap time string, or None if no valid value is
        available.
    """
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
    """
    Prepares a laps dataframe for JSON serialisation.

    Timedelta and session-time columns are converted to seconds, numpy
    scalars are cast to native Python types, and missing values are replaced
    with None.

    Args:
        df (pd.DataFrame): Laps dataframe to clean.

    Returns:
        pd.DataFrame: Cleaned dataframe ready for JSON output.
    """
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

    # convert numpy scalar types to Python native
    df = df.map(lambda x: x.item() if hasattr(x, "item") else x)

    df = df.replace({np.nan: None})

    return df

def add_lap_number_from_lapstarts(tel: pd.DataFrame, laps_drv: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns lap numbers to telemetry rows using lap start times.

    Telemetry samples are matched to the most recent lap start at or before
    each telemetry timestamp so that each row can be linked to its lap.

    Args:
        tel (pd.DataFrame): Telemetry data for a single driver.
        laps_drv (pd.DataFrame): Lap data for the same driver.

    Returns:
        pd.DataFrame: Telemetry dataframe with lap numbers attached.
    """
    print("adding lap data to the tel data")
    tel = tel.sort_values("Time").copy()

    lapstarts = (
        laps_drv[["LapNumber", "LapStartTime"]]
        .dropna()
        .sort_values("LapStartTime")
        .copy()
    )

    # assign the latest lap start time that is less than or equal to each telemetry time
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
    """
    Assigns lap numbers to telemetry rows using lap start times.

    Telemetry samples are matched to the most recent lap start at or before
    each telemetry timestamp so that each row can be linked to its lap.

    Args:
        tel (pd.DataFrame): Telemetry data for a single driver.
        laps_drv (pd.DataFrame): Lap data for the same driver.

    Returns:
        pd.DataFrame: Telemetry dataframe with lap numbers attached.
    """
    print("assining the live positions")
    df_bin = df_bin.copy()

    # need one row per driver per TimeBin.
    # if i have multiple samples per driver per bin, keep the latest sample
    df_bin = df_bin.sort_values("Time").drop_duplicates(subset=["DriverNumber"], keep="last")

    df_bin = df_bin.sort_values(["LapNumber", "Distance"], ascending=[False, False])

    df_bin["LivePosition"] = range(1, len(df_bin) + 1)
    return df_bin

def clean_for_json(obj):
    print("-- cleaning json")
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