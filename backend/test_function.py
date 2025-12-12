import fastf1 
import pandas as pd
import numpy as np

def session_leaderboard_view(year, country, session):
    session = fastf1.get_session(year, year, session)
    session.load()

    drivers_payload = []


    for drv in session.drivers:
        laps = session.laps.pick_drivers(drv)

        drv_code = session.get_driver(drv)['Abbreviation'] # driver code


        drivers_payload.append({
                "code": drv_code,
                "color": "#888888",  # you can map to team colors
                "samples": samples,
            })

    return {
            "drivers": drivers_payload,
        }

print(session_leaderboard_view[2025, "United Kingdom", "Race"])