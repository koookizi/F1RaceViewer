import fastf1 
import pandas as pd
import numpy as np
import openpyxl
import json


def session_leaderboard_view():
    session = fastf1.get_session(2025, "Australia", "Race")
    session.load()

    fastf1Response = ["VER","HAM"]

    finalJSON = {
        "drivers" : []
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
    ]

    drivers = []

    for drv in fastf1Response:
        laps = session.laps.pick_drivers(drv)[columns].copy()
        df_clean = prepare_laps_df_for_json(laps)
        laps_json = df_clean.to_dict(orient="records")

        drivers.append({
            "driver_code" : session.get_driver(drv)["Abbreviation"],
            "driver_fullName" : session.get_driver(drv)["FullName"],
            "teamColour" : session.get_driver(drv)["TeamColor"],
            "data" : laps_json
        })
    
    finalJSON["drivers"] = drivers
    
    return (finalJSON)

        
def prepare_laps_df_for_json(df: pd.DataFrame):
    df = df.copy()

    # Convert Timedelta → seconds
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

    # Convert Timestamps → seconds since session start
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

    # Convert numpy types → python native
    df = df.applymap(lambda x: x.item() if hasattr(x, "item") else x)

    return df




print(json.dumps(session_leaderboard_view(), indent=4))