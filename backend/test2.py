import os
import sys

# Ensure project root (the folder that contains manage.py) is on PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # .../backend
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from api.models import Driver, Team, Result, TeamStanding, DriverStanding


from urllib.request import urlopen
from django.http import JsonResponse
import fastf1 
import pandas as pd
import numpy as np
import json
from datetime import datetime
import math
import openpyxl
from datetime import datetime, timedelta
from datetime import timezone
from django.shortcuts import get_object_or_404

from django.db.models import Sum, Min
from django.db.models.functions import Coalesce

from api.models import Team, Result, TeamStanding

def driver_getDriverSummary(request, driver_ergast_id: str):
    driver = get_object_or_404(Driver, ergast_id=driver_ergast_id)

    # IMPORTANT: adapt these if you store "Race"/"Qualifying" instead of "R"/"Q"
    RACE = "R"
    QUALI = "Q"

    race_qs = Result.objects.filter(driver=driver, session_type=RACE)
    quali_qs = Result.objects.filter(driver=driver, session_type=QUALI)

    # Grand Prix entered = distinct events where driver has a race result
    gp_entered = race_qs.values("event_id").distinct().count()

    # Career points (race points)
    career_points = race_qs.aggregate(p=Coalesce(Sum("points"), 0.0))["p"]

    # Highest race finish + count (ignore null positions)
    highest_race_finish = race_qs.exclude(position__isnull=True).aggregate(
        m=Min("position")
    )["m"]
    highest_race_finish_count = 0
    if highest_race_finish is not None:
        highest_race_finish_count = race_qs.filter(position=highest_race_finish).count()

    # Podiums (race finishes <= 3; ignore null positions)
    podiums = race_qs.exclude(position__isnull=True).filter(position__lte=3).count()

    # Highest grid position + count (ignore null grid)
    highest_grid_position = race_qs.exclude(grid__isnull=True).aggregate(
        m=Min("grid")
    )["m"]
    highest_grid_position_count = 0
    if highest_grid_position is not None:
        highest_grid_position_count = race_qs.filter(grid=highest_grid_position).count()

    # Pole positions (qualifying grid == 1)
    pole_positions = quali_qs.filter(grid=1).count()

    # World Championships (seasons where driver finished P1 in DriverStanding)
    world_championships = DriverStanding.objects.filter(
        driver=driver, position=1
    ).count()

    # DNFs
    # If you don't store a status field, the best DB-only proxy is "no classified position"
    dnfs = race_qs.filter(position__isnull=True).count()

    return JsonResponse({
        "driver": f"{driver.given_name} {driver.family_name}",
        "grand_prix_entered": gp_entered,
        "career_points": float(career_points),
        "highest_race_finish": highest_race_finish,                    # e.g. 1
        "highest_race_finish_count": highest_race_finish_count,        # e.g. 105
        "podiums": podiums,
        "highest_grid_position": highest_grid_position,                # e.g. 1
        "highest_grid_position_count": highest_grid_position_count,    # e.g. 104
        "pole_positions": pole_positions,
        "world_championships": world_championships,
        "dnfs": dnfs,
    })

def teams_getTeamSummary(request, team_ergast_id: str):
    team = Team.objects.get(ergast_id=team_ergast_id)

    # IMPORTANT: adapt these if you store "Race"/"Qualifying" instead of "R"/"Q"
    RACE = "R"
    QUALI = "Q"

    race_qs = Result.objects.filter(team=team, session_type=RACE)
    quali_qs = Result.objects.filter(team=team, session_type=QUALI)

    # Grand Prix entered = distinct events where team has a race result
    gp_entered = race_qs.values("event_id").distinct().count()

    # Team points (race points)
    team_points = race_qs.aggregate(
        p=Coalesce(Sum("points"), 0.0)
    )["p"]

    # Highest race finish + count (ignore null positions)
    best_finish = race_qs.exclude(position__isnull=True).aggregate(
        m=Min("position")
    )["m"]
    best_finish_count = 0
    if best_finish is not None:
        best_finish_count = race_qs.filter(position=best_finish).count()

    # Podiums (counts podium FINISHES)
    podiums = race_qs.filter(position__lte=3).count()

    # Highest grid position + count (ignore null grid)
    best_grid = race_qs.exclude(grid__isnull=True).aggregate(
        m=Min("grid")
    )["m"]
    best_grid_count = 0
    if best_grid is not None:
        best_grid_count = race_qs.filter(grid=best_grid).count()

    # Poles (grid == 1)
    pole_positions = race_qs.filter(grid=1).count()

    # Constructors' championships
    world_championships = TeamStanding.objects.filter(
        team=team, position=1
    ).count()

    return JsonResponse({
        "team": team.name,
        "grand_prix_entered": gp_entered,
        "team_points": float(team_points),
        "highest_race_finish": best_finish,              # e.g. 1
        "highest_race_finish_count": best_finish_count,  # e.g. 21
        "podiums": podiums,
        "highest_grid_position": best_grid,              # e.g. 1
        "highest_grid_position_count": best_grid_count,  # e.g. 20
        "pole_positions": pole_positions,
        "world_championships": world_championships,
    })

teams_getTeamSummary(None, "mercedes")

def getCurrentSeason(request, data, teamOrDriver=None,):    
    year_now = datetime.now(timezone.utc).year

    sessions = []
    for y in (year_now - 1, year_now):
        req = urlopen(f"https://api.openf1.org/v1/sessions?year={y}")
        sessions.extend(json.loads(req.read().decode("utf-8")))

    session_df = pd.DataFrame(sessions)


    # -- this whole section gets the session_key for the next upcoming session, or if there are no upcoming sessions, the most recent past session. This is just for testing purposes, to avoid hardcoding a session_key that might not be valid in the future when the database is updated with new sessions.
    session_df["date_start"] = pd.to_datetime(session_df["date_start"], utc=True)
    session_df["date_end"] = pd.to_datetime(session_df["date_end"], utc=True)

    # to use only the last active season until new season starts
    now = datetime.now(timezone.utc)
    session_df["date_start"] = pd.to_datetime(session_df["date_start"], utc=True)
    session_df = session_df.loc[
    (session_df["session_type"].isin(["Qualifying", "Race"]))
].copy()
    started_sessions = session_df[session_df["date_start"] <= now]
    latest_year = started_sessions["year"].max()
    df = session_df.loc[session_df["year"] == latest_year].copy()    

    df = df.sort_values("date_start", ascending=True).reset_index(drop=True)

    race_session_keys = df.loc[df["session_name"] == "Race", "session_key"].astype(int).tolist()
    sprint_session_keys = df.loc[df["session_name"] == "Sprint", "session_key"].astype(int).tolist()
    qualifying_session_keys = df.loc[df["session_name"] == "Qualifying", "session_key"].astype(int).tolist()

    if latest_year != datetime.now().year:
        now = pd.Timestamp("2025-12-29T00:00:00Z")
    else:
        now = pd.Timestamp.now(tz="UTC")

    future = df[df["date_start"] >= now]
    if not future.empty:
        # next upcoming session = smallest date_start in the future
        next_row = future.sort_values("date_start", ascending=True).iloc[0]
    else:
        # if nothing upcoming, fall back to the most recent past session
        next_row = df.sort_values("date_start", ascending=True).iloc[-1]

    session_key = int(next_row["session_key"])
    print(session_key)
    
    # -- from the session key, get teams championship

    if teamOrDriver == "team":
        last_championship_req = urlopen(f"https://api.openf1.org/v1/championship_teams?session_key={session_key}")
        last_championship_df = pd.DataFrame(json.loads(last_championship_req.read().decode('utf-8')))

        if data not in last_championship_df["team_name"].tolist():
            return JsonResponse({"error": "Team not found in current season"}, status=404)

        drivers_req = urlopen(f"https://api.openf1.org/v1/drivers?team_name={data}&session_key={session_key}")
        drivers_df = pd.DataFrame(json.loads(drivers_req.read().decode('utf-8')))

        driver_numbers = drivers_df["driver_number"].tolist()

        drivers_df = drivers_df.drop(columns=["broadcast_name","meeting_key","session_key"])
        drivers_json = drivers_df.to_dict(orient="records")
    elif teamOrDriver == "driver":

        last_championship_req = urlopen(f"https://api.openf1.org/v1/championship_drivers?session_key={session_key}")
        last_championship_df = pd.DataFrame(json.loads(last_championship_req.read().decode('utf-8')))


        drivers_req = urlopen(f"https://api.openf1.org/v1/drivers?first_name={data.split(' ')[0]}&last_name={data.split(' ')[1]}&session_key={session_key}")
        drivers_df = pd.DataFrame(json.loads(drivers_req.read().decode('utf-8')))
        print(drivers_df)

        driver_numbers = drivers_df["driver_number"].tolist()
        print(driver_numbers)

        drivers_df = drivers_df.drop(columns=["broadcast_name","meeting_key","session_key"])
        drivers_json = drivers_df.to_dict(orient="records")

        last_championship_df = last_championship_df[last_championship_df["driver_number"] == driver_numbers[0]]

    # getting both race and sprint 
    driver_numbers_query = "&".join(f"driver_number={n}" for n in driver_numbers)
    all_result_keys = sprint_session_keys + race_session_keys
    all_results_query = "&".join(f"session_key={k}" for k in all_result_keys)
    all_results_req = urlopen(
        f"https://api.openf1.org/v1/session_result?{all_results_query}&{driver_numbers_query}"
    )
    all_results_df = pd.DataFrame(json.loads(all_results_req.read().decode("utf-8")))
    sprint_results_df = all_results_df[all_results_df["session_key"].isin(sprint_session_keys)]
    grand_prix_results_df = all_results_df[all_results_df["session_key"].isin(race_session_keys)]

    # getting GP starting grid positions
    # grid_query = "&".join(f"session_key={k}" for k in qualifying_session_keys)
    # grid_results_req = urlopen(f"https://api.openf1.org/v1/starting_grid?{grid_query}&{driver_numbers_query}")
    # grid_results_df = pd.DataFrame(json.loads(grid_results_req.read().decode('utf-8')))

    # season variables
    season_position = int(last_championship_df["position_current"].iloc[0]) if not last_championship_df.empty else 0
    season_points   = float(last_championship_df["points_current"].iloc[0])  if not last_championship_df.empty else 0.0

    # GP variables
    gp_races   = int(len(race_session_keys))
    gp_points  = float(grand_prix_results_df["points"].sum())
    gp_wins    = int(grand_prix_results_df[grand_prix_results_df["position"] == 1].shape[0])
    gp_podiums = int(grand_prix_results_df[grand_prix_results_df["position"] <= 3].shape[0])
    gp_poles   = 0 #int(grid_results_df[grid_results_df["position"] == 1].shape[0])
    gp_top10s  = int(grand_prix_results_df[grand_prix_results_df["position"] <= 10].shape[0])
    gp_DNFs    = int(grand_prix_results_df[grand_prix_results_df["dnf"] == True].shape[0])

    # sprint variables
    sprint_races   = int(len(sprint_session_keys))
    sprint_points  = float(sprint_results_df["points"].sum())
    sprint_wins    = int(sprint_results_df[sprint_results_df["position"] == 1].shape[0])
    sprint_podiums = int(sprint_results_df[sprint_results_df["position"] <= 3].shape[0])
    sprint_poles   = 0 #int(grid_results_df[grid_results_df["position"] == 1].shape[0])
    sprint_top10s  = int(sprint_results_df[sprint_results_df["position"] <= 10].shape[0])


    finalJSON = {
        "season_position": season_position,
        "season_points": season_points,
        "gp": {
            "races": gp_races,
            "points": gp_points,
            "wins": gp_wins,
            "podiums": gp_podiums,
            "poles": gp_poles,
            "top10s": gp_top10s,
            "dnfs": gp_DNFs
        },
        "sprint": {
            "races": sprint_races,
            "points": sprint_points,
            "wins": sprint_wins,
            "podiums": sprint_podiums,
            "poles": sprint_poles,
            "top10s": sprint_top10s
        },
        "drivers": drivers_json,
        "year": int(latest_year)
    }

    print(json.dumps(finalJSON, indent=4))
    #return JsonResponse(finalJSON, safe=False)

#getCurrentSeason(None, "Lewis Hamilton", "driver")
getCurrentSeason(None, "Mercedes", "team")
