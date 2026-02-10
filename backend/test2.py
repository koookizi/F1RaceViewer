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

#def teams_getTeamSummary(request, team: str):


def teams_getCurrentSeason(request, team: str):    
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    # -- this whole section gets the session_key for the next upcoming session, or if there are no upcoming sessions, the most recent past session. This is just for testing purposes, to avoid hardcoding a session_key that might not be valid in the future when the database is updated with new sessions.
    session_df["date_start"] = pd.to_datetime(session_df["date_start"], utc=True)
    session_df["date_end"] = pd.to_datetime(session_df["date_end"], utc=True)

    # to use only the last active season until new season starts
    now = datetime.now(timezone.utc)
    session_df["date_start"] = pd.to_datetime(session_df["date_start"], utc=True)
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
    
    # -- from the session key, get teams championship
    last_championship_teams_req = urlopen(f"https://api.openf1.org/v1/championship_teams?session_key={session_key}")
    last_championship_teams_df = pd.DataFrame(json.loads(last_championship_teams_req.read().decode('utf-8')))

    last_championship_teams_req = urlopen(f"https://api.openf1.org/v1/championship_teams?session_key={session_key}")
    last_championship_teams_df = pd.DataFrame(json.loads(last_championship_teams_req.read().decode('utf-8')))
    print(last_championship_teams_df)

    if team not in last_championship_teams_df["team_name"].tolist():
        return JsonResponse({"error": "Team not found in current season"}, status=404)



    championship_teams_req = urlopen(f"https://api.openf1.org/v1/championship_teams?team_name={team}")
    championship_teams_df = pd.DataFrame(json.loads(championship_teams_req.read().decode('utf-8')))

    drivers_req = urlopen(f"https://api.openf1.org/v1/drivers?team_name={team}&session_key={session_key}")
    drivers_df = pd.DataFrame(json.loads(drivers_req.read().decode('utf-8')))

    driver_numbers = drivers_df["driver_number"].tolist()

    # getting sprint races
    sprint_query = "&".join(f"session_key={k}" for k in sprint_session_keys)
    driver_numbers_query = "&".join(f"driver_number={n}" for n in driver_numbers)
    sprint_results_req = urlopen(f"https://api.openf1.org/v1/session_result?{sprint_query}&{driver_numbers_query}")
    sprint_results_df = pd.DataFrame(json.loads(sprint_results_req.read().decode('utf-8')))
    print(sprint_results_df)

    # getting GP races
    race_query = "&".join(f"session_key={k}" for k in race_session_keys)    
    grand_prix_results_req = urlopen(f"https://api.openf1.org/v1/session_result?{race_query}&{driver_numbers_query}")
    grand_prix_results_df = pd.DataFrame(json.loads(grand_prix_results_req.read().decode('utf-8')))
    print(grand_prix_results_df)

    # getting GP starting grid positions
    grid_query = "&".join(f"session_key={k}" for k in qualifying_session_keys)
    grid_results_req = urlopen(f"https://api.openf1.org/v1/starting_grid?{grid_query}&{driver_numbers_query}")
    grid_results_df = pd.DataFrame(json.loads(grid_results_req.read().decode('utf-8')))

    # season variables
    season_position = int(last_championship_teams_df["position_current"].iloc[0]) if not last_championship_teams_df.empty else 0
    season_points   = float(last_championship_teams_df["points_current"].iloc[0])  if not last_championship_teams_df.empty else 0.0

    # GP variables
    gp_races   = int(championship_teams_df[championship_teams_df["session_key"].isin(race_session_keys)].shape[0])
    gp_points  = float(grand_prix_results_df["points"].sum())
    gp_wins    = int(grand_prix_results_df[grand_prix_results_df["position"] == 1].shape[0])
    gp_podiums = int(grand_prix_results_df[grand_prix_results_df["position"] <= 3].shape[0])
    gp_poles   = int(grid_results_df[grid_results_df["position"] == 1].shape[0])
    gp_top10s  = int(grand_prix_results_df[grand_prix_results_df["position"] <= 10].shape[0])
    gp_DNFs    = int(grand_prix_results_df[grand_prix_results_df["dnf"] == True].shape[0])

    # sprint variables
    sprint_races   = int(championship_teams_df[championship_teams_df["session_key"].isin(sprint_session_keys)].shape[0])
    sprint_points  = float(sprint_results_df["points"].sum())
    sprint_wins    = int(sprint_results_df[sprint_results_df["position"] == 1].shape[0])
    sprint_podiums = int(sprint_results_df[sprint_results_df["position"] <= 3].shape[0])
    sprint_poles   = int(grid_results_df[grid_results_df["position"] == 1].shape[0])
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
        }
    }

    print(json.dumps(finalJSON, indent=4))
    #return JsonResponse(finalJSON, safe=False)

teams_getCurrentSeason(None, "McLaren")
