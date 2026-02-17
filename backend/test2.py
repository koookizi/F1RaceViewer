from urllib.request import urlopen
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

#from api.models import Season, Circuit, Event, Session, Team, Driver

import fastf1
from fastf1.ergast import Ergast

def ingest_drivers():
    response = Ergast().get_drivers(limit=5000)

    created = 0

    for driver in response.content:
        ergast_id = driver["driverId"]

        _, was_created = Driver.objects.update_or_create(
            ergast_id=ergast_id,
            defaults={
                "given_name": driver.get("givenName", ""),
                "family_name": driver.get("familyName", ""),
                "nationality": driver.get("nationality", ""),
            },
        )

        if was_created:
            created += 1

    return created

def ingest_teams():
    response = Ergast().get_constructor_info(limit=1000)

    created = 0

    print(response)
    print(type(response))

    # for constructor in response.content:
    #     ergast_id = constructor["constructorId"]

    #     _, was_created = Team.objects.update_or_create(
    #         ergast_id=ergast_id,
    #         defaults={
    #             "name": constructor.get("name", ""),
    #             "nationality": constructor.get("nationality", ""),
    #         },
    #     )

    #     if was_created:
    #         created += 1

    # return created

ingest_teams()

def ingest_schedule(season_obj, year: int):
    session_names = ["Session1", "Session2", "Session3", "Session4","Session5"]

    schedule_df_fastf1 = pd.DataFrame(fastf1.get_event_schedule(year, include_testing=False))
    schedule_df_ergast = pd.DataFrame(Ergast().get_race_schedule(season=year))
    
    # get circuitId from ergast by matching round numbers
    schedule_df_fastf1["RoundNumber"] = schedule_df_fastf1["RoundNumber"].astype(int)
    schedule_df_ergast["round"] = schedule_df_ergast["round"].astype(int)
    ergast_necessary_columns = schedule_df_ergast[["round", "circuitId","circuitName"]]
    schedule_df_ergast["circuitId"] = schedule_df_ergast["Circuit"].apply(lambda x: x["circuitId"])

    merged_df = schedule_df_fastf1.merge(
        ergast_necessary_columns,
        left_on="RoundNumber",
        right_on="round",
        how="left"
    )

    merged_df = merged_df.drop(columns=["round"])

    for _, row in merged_df.iterrows():
        rnd = row["RoundNumber"]
        country = row["Country"]
        circuit_obj = _create_circuit_row(row)

        event_obj, _ = Event.objects.update_or_create(
                    season=season_obj,
                    round=rnd,
                    defaults={"country": country, "circuit": circuit_obj},
                )
        
        for session in session_names:
            if pd.notna(row[session]):
                Session.objects.update_or_create(
                    event=event_obj,
                    session_type=session,
                )

def _create_circuit_row(self, race_row) -> Circuit:
    circuit_id = (race_row["circuitId"] or "").strip()
    circuit_name = (race_row["circuitName"] or "").strip()
    country = (race_row["country"] or "").strip()

    if not circuit_id:
        # Fallback: derive a stable-ish id from the name
        circuit_id = circuit_name.lower().strip().replace(" ", "_")[:64] or "unknown"

    circuit_obj, _ = Circuit.objects.update_or_create(
        ergast_id=circuit_id,
        defaults={
            "name": circuit_name[:100] if circuit_name else circuit_id[:100],
            "country": country[:100],
        },
    )
    return circuit_obj


