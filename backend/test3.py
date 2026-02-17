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

def ingest_teams():
    response = Ergast().get_constructor_info(limit=1000)
    
    temp_df = []
    while True:
        temp_df.append(response)
        try:
            response = response.get_next_result_page()
        except ValueError:
            break
    teams_dfs = pd.concat(temp_df, ignore_index=True)
    
    created = 0

    for _, row in teams_dfs.iterrows():
        ergast_id = row["constructorId"]

        _, was_created = Team.objects.update_or_create(
            ergast_id=ergast_id,
            defaults={
                "name": row.get("constructorName", "") or "",
                "nationality": row.get("constructorNationality", "") or "",
            },
        )

        if was_created:
            created += 1

    return created

ingest_teams()