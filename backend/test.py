import fastf1 
import pandas as pd
import numpy as np
import openpyxl
import json

def session_telemetry_view(year, country, session_name):
    session = fastf1.get_session(year, country, session_name)
    session.load()

    results = session.results
    grid_positions = {}
    if results is not None:
        for drv in session.drivers:
            try:
                grid_positions[drv] = int(results.loc[drv]["GridPosition"])
            except:
                grid_positions[drv] = None

    # ----- EXTRACT RAW TELEMETRY FOR EACH DRIVER -----

    all_tel = {}   # raw telemetry DataFrames per driver

    for drv in session.drivers:
        laps = session.laps.pick_drivers(drv)
        tel = laps.get_telemetry().copy()

        # FastF1 builtin: add driver ahead metadata
        tel = tel.add_driver_ahead()

        # unify name
        tel["DriverNumber"] = drv

        # compute session time as float seconds
        tel["SessionTime"] = tel["Time"].dt.total_seconds()

        all_tel[drv] = tel

    # ----- BUILD A MERGED TELEMETRY SNAPSHOT -----
    # At each telemetry sample point, we compute:
    #   - live position
    #   - gap to next car
    #   - position gained from grid

    # Combine all samples into one big table
    merged = pd.concat(all_tel.values(), ignore_index=True)

    # Sort chronologically
    merged = merged.sort_values("SessionTime")

    # Live order based on track Distance
    def compute_live_positions(df):
        df_sorted = df.sort_values("Distance", ascending=False)
        df_sorted["LivePosition"] = range(1, len(df_sorted) + 1)
        return df_sorted

    merged = merged.groupby("SessionTime").apply(compute_live_positions)
    merged.reset_index(drop=True, inplace=True)

    # Gap to car ahead (in meters)
    merged["GapToAhead_m"] = np.nan
    for t, grp in merged.groupby("SessionTime"):
        grp = grp.sort_values("LivePosition")
        gap = grp["Distance"].diff() * -1  # car behind sees positive gap
        merged.loc[grp.index, "GapToAhead_m"] = gap

    # Convert meter gap to time gap (approx)
    merged["GapToAhead_s"] = merged["GapToAhead_m"] / merged["Speed"]

    # Positions gained from grid
    merged["PositionsGained"] = merged.apply(
        lambda r: None
        if grid_positions.get(r["DriverNumber"]) is None
        else grid_positions[r["DriverNumber"]] - int(r["LivePosition"]),
        axis=1
    )

    # Format for frontend
    def fmt_gap(x):
        if pd.isna(x):
            return None
        return f"+{x:.3f}"

    merged["GapToAheadStr"] = merged["GapToAhead_s"].apply(fmt_gap)

    # ----- PACK RESPONSE -----
    final = {}

    for drv in session.drivers:
        df_drv = merged[merged["DriverNumber"] == drv].copy()

        # reduce columns for cleaner JSON
        keep = [
            "SessionTime", "Distance", "X", "Y",
            "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS",
            "DriverAhead", "GapToAhead_s", "GapToAheadStr",
            "LivePosition", "PositionsGained"
        ]

        df_drv = df_drv[keep]

        # convert to JSON-safe
        df_drv = df_drv.replace({np.nan: None})
        df_drv = df_drv.applymap(lambda x: x.item() if hasattr(x, "item") else x)

        final[session.get_driver(drv)["Abbreviation"]] = df_drv.to_dict(orient="records")

    return final


print(json.dumps(session_telemetry_view(2025, "Australia", "Race"), indent=4))