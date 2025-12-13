import fastf1 
import pandas as pd
import numpy as np
import json
import math
import openpyxl


def session_telemetry_view(year, country, session_name, step=10):
    session = fastf1.get_session(year, country, session_name)
    session.load()

    all_tel = []

    keep_cols = ["Time", "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS", "DistanceToDriverAhead", "DriverAhead"]

    # -- get telemetry data for all drivers
    for drv in session.drivers:
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

        all_tel.append(tel)

    merged_tel = pd.concat(all_tel, ignore_index=True)

    # -- time bin (for comparison of rows by time bin instead of sessionTime -since there has to be a common column in time to compare to)
    bin_size = 0.2 # seconds

    merged_tel["TimeBin"] = (merged_tel["SessionTime"] / bin_size).round().astype("int64") # remember: time bin is not a measurement in seconds, it is a bin allocation
    merged_tel["TimeBinSize"] = bin_size

    # to ensure that there is only one driver per bin (by first sorting sessiontimes, get rows by timebin and drivernumber (whcih gets possible duplicates),
    #  and remove the other duplicates via .tail(1)
    merged_tel = (
    merged_tel.sort_values(["DriverNumber", "SessionTime"])
          .groupby(["TimeBin", "DriverNumber"], as_index=False)
          .tail(1)
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
    merged_tel["GridPosition"] = merged_tel["DriverNumber"].map(grid_positions)

    # > live positions
    merged_tel["LivePosition"] = (
    merged_tel.groupby("TimeBin")["Distance"]
          .rank(ascending=False, method="first")
          .astype("int32")
          )
    
    # > positions gained
    diff = (merged_tel["GridPosition"] - merged_tel["LivePosition"]).round().astype("Int64")

    s = diff.astype("string")                 # "<NA>" supported
    merged_tel["PositionsGained"] = s.where(diff.notna(), None)  # nulls -> None
    merged_tel.loc[diff > 0, "PositionsGained"] = "+" + s[diff > 0]

    # Filter rows
    df_ver = merged_tel[merged_tel["DriverCode"] == "ALO"]

    # Export to Excel
    df_ver.to_excel("ALO_telemetry1.xlsx", index=False)
    
    # -- clean dataframe ready for json
    cols = [
        "TimeBin", "TimeBinSize", "SessionTime",
        "GridPosition", "LivePosition", "PositionsGained",
        "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS",
        "DistanceToDriverAhead", "DriverAhead"
    ]
    final = {}
    for drv in session.drivers:
        df_drv = merged_tel[merged_tel["DriverNumber"] == drv].copy()
        df_drv = df_drv[[c for c in cols if c in df_drv.columns]]

        df_drv = df_drv.map(lambda x: x.item() if hasattr(x, "item") else x)

        df_drv = df_drv.replace([np.inf, -np.inf], np.nan)
        df_drv = df_drv.where(pd.notnull(df_drv), None)

        code = session.get_driver(drv)["Abbreviation"]
        final[code] = df_drv.to_dict(orient="records")

    final = clean_for_json(final)
    return final
    


def clean_for_json(obj):
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


with open("telemetry.json", "w", encoding="utf-8") as f:
    json.dump(session_telemetry_view(2025, "Australia", "Race"), f, indent=2)
