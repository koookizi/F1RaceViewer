from django.shortcuts import render
from django.http import HttpResponseBadRequest, JsonResponse
from api.models import Circuit, Result, Season, Event, Session, Team, TeamStanding
import fastf1
from fastf1.ergast import Ergast
import math
import pandas as pd 
import numpy as np
from functools import lru_cache
from .helpers.geometry import rotate, normalize_xy
import json
from datetime import datetime
from urllib.request import urlopen
from datetime import timezone
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
from django.views.decorators.csrf import csrf_exempt
import plotly.graph_objects as go
from django.db.models import Sum, Min
from django.db.models.functions import Coalesce


def season_years(request):
    years = (
        Season.objects
        .order_by('-year')
        .values_list('year', flat=True)
    )
    return JsonResponse({"years":list(years)})

def season_countries(request, year):
    countries = (
        Event.objects
        .filter(season__year=year)
        .values_list('country', flat=True)
        .distinct()
    )
    return JsonResponse({"countries": list(countries)})

def season_sessions(request, year, country):
    sessions = (
        Session.objects
        .filter(event__country=country)
        .filter(event__season__year=year)
        .values_list('session_type', flat=True)
        .distinct()
        .order_by('session_type')
    )
    return JsonResponse({"sessions": list(sessions)})

def drivers_getDrivers(request):
    drivers = (
        Result.objects
        .order_by("driver_name")
        .values("driver_name", "driver_number", "team__name")
        .distinct()
    )

    return JsonResponse({"drivers": list(drivers)})

def teams_getTeams(request):
    teams = (
        Team.objects
        .order_by("name")
        .values("name", "ergast_id")
    )

    return JsonResponse({"teams": list(teams)})

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

def teams_getCurrentSeason(request, team: str):    
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
    print(last_championship_teams_df)

    if team not in last_championship_teams_df["team_name"].tolist():
        return JsonResponse({"error": "Team not found in current season"}, status=404)

    drivers_req = urlopen(f"https://api.openf1.org/v1/drivers?team_name={team}&session_key={session_key}")
    drivers_df = pd.DataFrame(json.loads(drivers_req.read().decode('utf-8')))

    driver_numbers = drivers_df["driver_number"].tolist()

    drivers_df = drivers_df.drop(columns=["broadcast_name","meeting_key","session_key"])
    drivers_json = drivers_df.to_dict(orient="records")


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
    season_position = int(last_championship_teams_df["position_current"].iloc[0]) if not last_championship_teams_df.empty else 0
    season_points   = float(last_championship_teams_df["points_current"].iloc[0])  if not last_championship_teams_df.empty else 0.0

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

    return JsonResponse(finalJSON, safe=False)




@lru_cache(maxsize=32)
def session_circuit(request, year: int, country: str):
    event = (
        Event.objects
        .select_related("circuit")
        .filter(season__year=year, country=country)
        .first()
    )
    if not event:
        return JsonResponse({"error": "Event not found"}, status=404)

    return JsonResponse({
        "circuit": event.circuit.name, 
    })

@lru_cache(maxsize=32)
def session_teamradio_view(request, year: int, country: str, session_name: str):    
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    fastf1_start = session.t0_date + session.session_start_time # gets the actual datetime of session start (first telemetry point)

    # ---

    # get team radio data
    teamradio_data_req = urlopen(f"https://api.openf1.org/v1/team_radio?session_key={session_df.loc[0, 'session_key']}&date>{session_df.loc[0, "date_start"]}")
    teamradio_data = pd.DataFrame(json.loads(teamradio_data_req.read().decode('utf-8')))
    teamradio_data["date"] = pd.to_datetime(
        teamradio_data["date"],
        utc=True,
        format="ISO8601"
    )

    teamradio_data["SessionTime"] = (
        teamradio_data["date"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    teamradio_data = teamradio_data[
    ["SessionTime"] + [c for c in teamradio_data.columns if c != "SessionTime"]]
    teamradio_data.sort_values("SessionTime")

    teamradio_data["time"] = (
    pd.to_datetime(teamradio_data["date"])
    .dt.strftime("%H:%M:%S")
)

    teamradio_data = teamradio_data.drop(columns=['date', 'meeting_key', 'session_key'])

    # > cleans any NaNs for JSON
    teamradio_data = teamradio_data.astype(object)
    teamradio_data = teamradio_data.where(pd.notna(teamradio_data), None)

    # -- final structure
    finalJSON = teamradio_data.to_dict(orient="records")

    return JsonResponse(finalJSON, safe=False)

@lru_cache(maxsize=32)
def session_racecontrol_view(request, year: int, country: str, session_name: str):    
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    fastf1_start = session.t0_date + session.session_start_time # gets the actual datetime of session start (first telemetry point)

    # ---

    # get race control data
    racecontrol_data_req = urlopen(f"https://api.openf1.org/v1/race_control?session_key={session_df.loc[0, 'session_key']}&date>{session_df.loc[0, "date_start"]}")
    racecontrol_data = pd.DataFrame(json.loads(racecontrol_data_req.read().decode('utf-8')))
    racecontrol_data["date"] = pd.to_datetime(
        racecontrol_data["date"],
        utc=True,
        format="ISO8601"
    )

    racecontrol_data["SessionTime"] = (
        racecontrol_data["date"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    racecontrol_data = racecontrol_data[
    ["SessionTime"] + [c for c in racecontrol_data.columns if c != "SessionTime"]]
    racecontrol_data.sort_values("SessionTime")

    racecontrol_data["time"] = (
    pd.to_datetime(racecontrol_data["date"])
    .dt.strftime("%H:%M:%S")
)

    racecontrol_data = racecontrol_data.drop(columns=['date', 'meeting_key', 'session_key'])

    # > cleans any NaNs for JSON
    racecontrol_data = racecontrol_data.astype(object)
    racecontrol_data = racecontrol_data.where(pd.notna(racecontrol_data), None)

    # -- final structure
    finalJSON = racecontrol_data.to_dict(orient="records")

    return JsonResponse(finalJSON, safe=False)

@lru_cache(maxsize=32)
def session_leaderboard_view(request, year: int, country: str, session_name: str):    
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    openf1_start = pd.to_datetime(session_df.loc[0, "date_start"], utc=True)
    openf1_end = pd.to_datetime(session_df.loc[0, "date_end"], utc=True)

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    fastf1_start = session.t0_date + session.session_start_time # gets the actual datetime of session start (first telemetry point)

    # ---

    # get position data
    positions_data_req = urlopen(f"https://api.openf1.org/v1/position?meeting_key={session_df.loc[0, 'meeting_key']}&date>={session_df.loc[0, "date_start"]}")
    positions_data = pd.DataFrame(json.loads(positions_data_req.read().decode('utf-8')))
    positions_data["date"] = pd.to_datetime(
        positions_data["date"],
        utc=True,
        format="ISO8601"
    )

    positions_data["SessionTime"] = (
        positions_data["date"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    positions_data = positions_data[
    ["SessionTime"] + [c for c in positions_data.columns if c != "SessionTime"]]
    positions_data.sort_values("SessionTime")

    positions_data = positions_data.drop(columns=['date', 'meeting_key', 'session_key'])

    # > cleans any NaNs for JSON
    positions_data = positions_data.astype(object)
    positions_data = positions_data.where(pd.notna(positions_data), None)

    # get lap data
    laps_data_req = urlopen(f"https://api.openf1.org/v1/laps?session_key={session_df.loc[0, "session_key"]}&date_start>={session_df.loc[0, "date_start"]}")
    laps_data = pd.DataFrame(json.loads(laps_data_req.read().decode('utf-8')))
    laps_data["date_start"] = pd.to_datetime(
        laps_data["date_start"],
        utc=True,
        format="ISO8601"
    )

    laps_data["SessionTime"] = (
        laps_data["date_start"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    laps_data = laps_data.drop(columns=['meeting_key', 'session_key', 'date_start'])

    laps_data = laps_data[
    ["SessionTime"] + [c for c in laps_data.columns if c != "SessionTime"]
    ]

    laps_data = laps_data.astype(object)
    laps_data = laps_data.where(pd.notna(laps_data), None)

    # get stint data
    stint_data_req = urlopen(f"https://api.openf1.org/v1/stints?session_key={session_df.loc[0, "session_key"]}")
    stint_data = pd.DataFrame(json.loads(stint_data_req.read().decode('utf-8')))
    stint_data = stint_data.drop(columns=['meeting_key', 'session_key'])

    stint_data = stint_data.astype(object)
    stint_data = stint_data.where(pd.notna(stint_data), None)

    # get pit data
    pit_data_req = urlopen(f"https://api.openf1.org/v1/pit?session_key={session_df.loc[0, 'session_key']}&date>={session_df.loc[0, 'date_start']}")
    pit_data = pd.DataFrame(json.loads(pit_data_req.read().decode('utf-8')))
    pit_data["date"] = pd.to_datetime(
        pit_data["date"],
        utc=True,
        format="ISO8601"
    )

    pit_data["SessionTime"] = (
        pit_data["date"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    pit_data = pit_data[
    ["SessionTime"] + [c for c in pit_data.columns if c != "SessionTime"]]
    pit_data.sort_values("SessionTime")

    pit_data = pit_data.drop(columns=['date', 'meeting_key', 'session_key'])

    # > cleans any NaNs for JSON
    pit_data = pit_data.astype(object)
    pit_data = pit_data.where(pd.notna(pit_data), None)

    # get car data
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

    keep_cols = ["SessionTime", "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS", "Time"]

    all_tel = []
    for drv in session.drivers:
        print("Getting data for:",drv)
        laps = session.laps.pick_drivers(drv) 
        tel = laps.get_telemetry().copy()

        # Reduce columns early
        tel = tel[[c for c in keep_cols if c in tel.columns]]

        # Downsample early (HUGE speed win + smaller JSON)
        step=10
        if step and step > 1:
            tel = tel.iloc[::step].copy()

        tel["driver_number"] = drv
        tel["SessionTime"] = tel["SessionTime"].dt.total_seconds()
        all_tel.append(tel)

    car_data = pd.concat(all_tel, ignore_index=True)
    car_data = car_data[
    ["SessionTime"] + [c for c in car_data.columns if c != "SessionTime"]
    ]

    car_data = car_data.astype(object)
    car_data = car_data.where(pd.notna(car_data), None)
    car_data["driver_number"] = pd.to_numeric(car_data["driver_number"], errors="coerce").astype("Int64") # because FastF1 gives str

    car_data = car_data.drop(columns=['Time'])

    car_data["grid_position"] = car_data["driver_number"].astype(str).map(grid_positions)

    # get gap data
    gap_data_req = urlopen(f"https://api.openf1.org/v1/intervals?meeting_key={session_df.loc[0, 'meeting_key']}")
    gap_data = pd.DataFrame(json.loads(gap_data_req.read().decode('utf-8')))
    gap_data["date"] = pd.to_datetime(
        gap_data["date"],
        utc=True,
        format="ISO8601"
    )

    gap_data["SessionTime"] = (
        gap_data["date"] - session.t0_date.replace(tzinfo=timezone.utc)
    ).dt.total_seconds()

    gap_data = gap_data[
    ["SessionTime"] + [c for c in gap_data.columns if c != "SessionTime"]]
    gap_data.sort_values("SessionTime")

    gap_data = gap_data.drop(columns=['date', 'meeting_key', 'session_key'])

    # > cleans any NaNs for JSON
    gap_data = gap_data.astype(object)
    gap_data = gap_data.where(pd.notna(gap_data), None)

    # -- get driver info / final structure
    drivers_data_req = urlopen(f"https://api.openf1.org/v1/drivers?session_key={session_df.loc[0, "session_key"]}")
    drivers_df = pd.DataFrame(json.loads(drivers_data_req.read().decode('utf-8')))
    finalJSON = {}
    drivers = []
    for _, driver_row in drivers_df.iterrows():
        driver_info = {
            "driver_code": driver_row["name_acronym"],
            "driver_number": driver_row["driver_number"],
            "driver_fullName": driver_row["full_name"],
            "team_colour": driver_row["team_colour"],
            "positions_data": positions_data[positions_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "laps_data": laps_data[laps_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "stint_data": stint_data[stint_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "car_data": car_data[car_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "gap_data": gap_data[gap_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
            "pit_data": pit_data[pit_data["driver_number"] == driver_row["driver_number"]].to_dict(orient="records"),
        }
        drivers.append(driver_info)

    finalJSON["drivers"] = drivers

    return JsonResponse(finalJSON, safe=False)

@lru_cache(maxsize=32)
def session_telemetry_view(request, year: int, country: str, session_name: str, step=10):
    session = fastf1.get_session(year, country, session_name)
    session.load()

    all_tel = []

    keep_cols = ["Time", "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS", "DistanceToDriverAhead", "DriverAhead"]

    # -- get telemetry data for all drivers
    print("-- Getting telemetry and laps data")
    for drv in session.drivers:
        print("Getting data for:",drv)
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

        tel = add_lap_number_from_lapstarts(tel, laps)

        all_tel.append(tel)

    merged_tel = pd.concat(all_tel, ignore_index=True)

    # -- time bin (for comparison of rows by time bin instead of sessionTime -since there has to be a common column in time to compare to)
    print("-- doing time bin")
    bin_size = 0.2 # seconds

    merged_tel["TimeBin"] = (merged_tel["SessionTime"] / bin_size).round().astype("int64") # remember: time bin is not a measurement in seconds, it is a bin allocation
    merged_tel["TimeBinSize"] = bin_size

    # to ensure that there is only one driver per bin (by first sorting sessiontimes, get rows by timebin and drivernumber (whcih gets possible duplicates),
    #  and remove the other duplicates via .tail(1)
    # merged_tel = (
    # merged_tel.sort_values(["DriverNumber", "SessionTime"])
    #       .groupby(["TimeBin", "DriverNumber"], as_index=False)
    #       .tail(1)
    # )
    merged_tel = merged_tel.sort_values("SessionTime").drop_duplicates(
    subset=["TimeBin", "DriverNumber"], keep="last"
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
    print("-- grid positions")
    merged_tel["GridPosition"] = merged_tel["DriverNumber"].map(grid_positions)

    # > live positions
    print("-- live positions")
    # 1) Ensure one row per (TimeBin, DriverNumber): keep latest Time
    merged_tel = merged_tel.sort_values("Time").drop_duplicates(
        subset=["TimeBin", "DriverNumber"],
        keep="last"
    )

    # 2) Sort so that "ahead" rows come first within each TimeBin
    merged_tel = merged_tel.sort_values(
        ["TimeBin", "LapNumber", "Distance"],
        ascending=[True, False, False]
    )

    # 3) Assign positions 1..N within each TimeBin
    merged_tel["LivePosition"] = merged_tel.groupby("TimeBin").cumcount() + 1


    # > positions gained
    print("-- positions gained")
    diff = (merged_tel["GridPosition"] - merged_tel["LivePosition"]).round().astype("Int64")

    s = diff.astype("string")                 # "<NA>" supported
    merged_tel["PositionsGained"] = s.where(diff.notna(), None)  # nulls -> None
    merged_tel.loc[diff > 0, "PositionsGained"] = "+" + s[diff > 0]
    
    # -- clean dataframe ready for json
    print("-- preparing for json")
    cols = [
        "TimeBin", "TimeBinSize", "SessionTime",
        "GridPosition", "LivePosition", "PositionsGained", "LapNumber",
        "Distance", "X", "Y", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS","DriverNumber","DriverCode"
    ]
    # 1) Select columns once
    df = merged_tel[[c for c in cols if c in merged_tel.columns]].copy()

    # 2) Clean once (vectorized)
    df = df.replace([np.inf, -np.inf], np.nan)

    # Convert numpy scalars -> python scalars + NaN->None in one go:
    # (this produces dtype=object, which is what you want for JSON)
    df = df.astype(object).where(df.notna(), None)

    print("-- get driver info")
    code_map = {int(d): session.get_driver(d)["Abbreviation"] for d in session.drivers}

    final = {code_map[int(drv)]: g.to_dict("records")
    for drv, g in df.groupby("DriverNumber", sort=False)}

    # Export to excel
    print("-- exporting to excel")
    #merged_tel.to_excel("test_tel.xlsx", index=False)

    return JsonResponse(final, safe=False)


@lru_cache(maxsize=32)
def session_laps_view(request, year: int, country: str, session: str):
    session = fastf1.get_session(year, country, session)
    session.load()

    finalJSON = {
        "drivers": []
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
        "Position",       # current position per lap (from Laps)
    ]

    drivers = []

    # Defensive guard in case results aren't available (e.g. practice)
    results = getattr(session, "results", None)

    for drv in session.drivers:
        laps = session.laps.pick_drivers(drv)[columns].copy()

        # Default: no grid position if results are missing
        grid_pos = None
        if results is not None and not results.empty:
            try:
                # SessionResults indexed by driver number; row has 'GridPosition'
                driver_result = results.loc[drv]
                grid_val = driver_result.get("GridPosition", None)
                if pd.notna(grid_val):
                    grid_pos = int(grid_val)
            except KeyError:
                grid_pos = None

        # Add GridPosition column (same value for all laps of that driver)
        laps["GridPosition"] = grid_pos

        # PositionsGainedString = "+3", "-1", "0", or None
        def compute_positions_gained_str(row):
            if grid_pos is None or pd.isna(row["Position"]):
                return None
            try:
                gained = int(grid_pos) - int(row["Position"])
                if gained > 0:
                    return f"+{gained}"
                elif gained < 0:
                    return f"{gained}"  # already has "-"
                else:
                    return "0"
            except (ValueError, TypeError):
                return None

        laps["PositionsGained"] = laps.apply(compute_positions_gained_str, axis=1)

        # Now convert to JSON-safe format
        df_clean = prepare_laps_df_for_json(laps)
        laps_json = df_clean.to_dict(orient="records")

        drivers.append({
            "driver_code": session.get_driver(drv)["Abbreviation"],
            "driver_fullName": session.get_driver(drv)["FullName"],
            "teamColour": session.get_driver(drv)["TeamColor"],
            "grid_position": grid_pos,  # useful to have at driver level too
            "data": laps_json
        })

    finalJSON["drivers"] = drivers

    return JsonResponse(finalJSON)

@lru_cache(maxsize=32)
def session_vrdetails_view(request, year: int, country: str, session_name: str):
    session = fastf1.get_session(year, country, session_name)

    session.load(telemetry=False)

    drivers = []
    teams = []

    results_df = session.results

    for _, row in results_df.iterrows():
        drivers.append(row.get("Abbreviation", ""),)
        teams.append(row.get("TeamName", ""))    

    teams = list(dict.fromkeys(teams))

    return JsonResponse({
         "drivers": drivers,
         "teams": teams,
         })

@lru_cache(maxsize=32)
def session_weather_view(request, year: int, country: str, session: str):
    session_obj = fastf1.get_session(year, country, session)

    session_obj.load(telemetry=False)

    weather_df = session_obj.laps.get_weather_data()

    if weather_df is None or weather_df.empty:
        return JsonResponse({"weather": []})

    # convert Time (timedelta) to seconds from session start and adds a column to the df
    weather_df = weather_df.copy()
    weather_df["TimeSec"] = weather_df["Time"].dt.total_seconds()

    rangeAirTemp = weather_df["AirTemp"].min().item(),weather_df["AirTemp"].max().item()
    rangeHumidity = weather_df["Humidity"].min().item(),weather_df["Humidity"].max().item()
    rangePressure = weather_df["Pressure"].min().item(),weather_df["Pressure"].max().item()
    rangeTrackTemp = weather_df["TrackTemp"].min().item(),weather_df["TrackTemp"].max().item()
    rangeWindSpeed = weather_df["WindSpeed"].min().item(),weather_df["WindSpeed"].max().item()


    samples = []
    for _, row in weather_df.iterrows():
        samples.append({
            "time_sec": float(row["TimeSec"]),         
            "air_temp": to_float_or_none(row["AirTemp"]),
            "track_temp": to_float_or_none(row["TrackTemp"]),
            "humidity": to_float_or_none(row["Humidity"]),
            "pressure": to_float_or_none(row["Pressure"]),
            "rainfall": to_float_or_none(row["Rainfall"]),
            "wind_dir": to_float_or_none(row["WindDirection"]),
            "wind_speed": to_float_or_none(row["WindSpeed"]),

        })

    return JsonResponse({
         "weather": samples,
         "rangeAirTemp": rangeAirTemp,
         "rangeHumidity": rangeHumidity,
         "rangePressure": rangePressure,
         "rangeTrackTemp": rangeTrackTemp,
         "rangeWindSpeed": rangeWindSpeed
         })

@lru_cache(maxsize=32)
def session_playback_view(request, year: int, country: str, session_name: str):
    # OpenF1
    session_data_req = urlopen(f"https://api.openf1.org/v1/sessions?country_name={country.replace(" ","+")}&session_name={session_name.replace(" ","+")}&year={year}")
    session_df = pd.DataFrame(json.loads(session_data_req.read().decode('utf-8')))

    openf1_start = pd.to_datetime(session_df.loc[0, "date_start"], utc=True)
    openf1_end = pd.to_datetime(session_df.loc[0, "date_end"], utc=True)

    # FastF1
    session = fastf1.get_session(year, country, session_name)
    session.load()

    circuit_info = session.get_circuit_info() # gets rotation angle, corner pos, numbers etc.

    fastf1_start = session.t0_date + session.session_start_time # gets the actual datetime of session start (first telemetry point)
    playbackControlOffset = (fastf1_start - session.t0_date).total_seconds() # in seconds
    fastf1_openf1_offset = (fastf1_start.replace(tzinfo=timezone.utc) - openf1_start).total_seconds() # in seconds. fastf1 is the later one

    # --- get session start time
    session_start_time = (
    session.t0_date
    .tz_localize("UTC")
    .strftime("%Y-%m-%dT%H:%M:%SZ")
)


    # --- build track polyline (using fastest lap of pole or just first driver) 
    ref_driver = session.drivers[0]
    ref_lap = session.laps.pick_drivers(ref_driver).pick_fastest()
    pos = ref_lap.get_pos_data()   # contains X, Y, Date, gives you a dataframe

    # pos.loc[row_selection, column_selection], : means all rows. so all X and Y only, and then turn into numpy
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

        # Collect positions for all laps of this driver
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
        # same concept
        # total_laps = max(
        #     sample["lap"]
        #     for drv in drivers_payload
        #     for sample in drv["samples"]
        # )
    else:
        race_duration = 0.0
        # total_laps = 0

    
    total_laps = int(session.laps['LapNumber'].max())

    return JsonResponse({
        "track": {"points": track_points},
        "drivers": drivers_payload,
        "raceDuration": race_duration,
        "totalLaps": total_laps,
        "playbackControlOffset" : playbackControlOffset,
        "sessionStart" : session_start_time
    })

@lru_cache(maxsize=32)
def results_view(request, year: int, country: str, session: str):
    sessionFF1 = fastf1.get_session(year, country, session)
    try:
        sessionFF1.load()
    except Exception as e:
        # If FastF1 itself fails to load the session
        return JsonResponse(
            {"error": f"Failed to load session data: {e}"},
            status=500,
        )

    # Base results (may be missing Position / BestLapTime / Laps for practice/quali)
    df = sessionFF1.results
    if df is None or df.empty:
        # No results; don't crash, just return empty
        return JsonResponse({"results": []})

    df = df.copy()

    # Ensure key columns exist
    if "BestLapTime" not in df.columns:
        df["BestLapTime"] = pd.NaT

    if "Laps" not in df.columns:
        df["Laps"] = pd.NA

    if "LastLapTime" not in df.columns:
        df["LastLapTime"] = pd.NA

    if "Position" not in df.columns:
        df["Position"] = pd.NA

    # ---------------------------
    # 1) Build per-driver data from laps
    # ---------------------------
    best_laps = None
    lap_counts = None
    last_laps = None

    try:
        laps = sessionFF1.laps  # <- this can raise DataNotLoadedError
        if laps is not None and not laps.empty:
            # Best lap per driver (only accurate laps with a LapTime)
            valid_laps = laps.pick_accurate().dropna(subset=["LapTime"])

            # Best lap per driver (only accurate, non-null LapTime)
            valid_laps = laps.pick_accurate().dropna(subset=["LapTime"])
            best_laps = (
                valid_laps
                .groupby("DriverNumber")["LapTime"]
                .min()
            )  # Series: DriverNumber -> Timedelta

            # Lap count per driver (use all laps with a LapTime)
            lap_counts = (
                laps
                .dropna(subset=["LapTime"])
                .groupby("DriverNumber")["LapNumber"]
                .count()
            )  # Series: DriverNumber -> int

            # Last lap per driver
            last_laps = (
            laps
            .dropna(subset=["LapTime"])
            .sort_values("LapNumber")
            .groupby("DriverNumber")["LapTime"]
            .last()
            )
    except Exception:
        # No lap data available for this session (common for very old seasons)
        best_laps = None
        lap_counts = None
        last_laps = None

    

    # ---------------------------
    # 2) Merge best lap + lap count into results df
    # ---------------------------
    if best_laps is not None:
        df = df.merge(
        best_laps.rename("BestSessionLapTime"),
        left_on="DriverNumber",
        right_index=True,
        how="left",
        )
        pd.set_option('future.no_silent_downcasting', True)
        # Ensure BestLapTime column exists; if not, create it
        if "BestLapTime" not in df.columns:
            df["BestLapTime"] = pd.NaT

        # Fill missing BestLapTime with our computed best session lap
        df["BestLapTime"] = df["BestLapTime"].fillna(df["BestSessionLapTime"])

    if lap_counts is not None:
        df = df.merge(
        lap_counts.rename("SessionLapCount"),
        left_on="DriverNumber",
        right_index=True,
        how="left",
        )
        # Ensure Laps column exists; if not, create it
        if "Laps" not in df.columns:
            df["Laps"] = pd.NA

        # Fill missing Laps with our computed session lap count
        df["Laps"] = df["Laps"].fillna(df["SessionLapCount"])

    if last_laps is not None:
        df = df.merge(
        last_laps.rename("FinalLapTime"),
        left_on="DriverNumber",
        right_index=True,
        how="left",
        )
        if "LastLapTime" not in df.columns:
            df["LastLapTime"] = pd.NaT



    # ---------------------------
    # 3) Create / fill Position when it's missing (practice etc.)
    # ---------------------------
    if "Position" not in df.columns:
        df["Position"] = pd.NA

    missing_pos_mask = df["Position"].isna()

    if missing_pos_mask.any() and df["BestLapTime"].notna().any():
        # Sort only the missing-position rows by best lap
        subset = (
            df.loc[missing_pos_mask]
            .sort_values("BestLapTime")
            .reset_index()
        )

        # Assign positions 1..N to them based on best lap order
        df.loc[subset["index"], "Position"] = range(1, len(subset) + 1)

    # ---------------------------
    # 4) Build JSON-friendly result list
    # ---------------------------
    results = []

    for _, row in df.iterrows():
        pos = row.get("Position", None)
        laps_val = row.get("Laps", None)
        points = row.get("Points", None)
        gridPos = row.get("GridPosition", None)

        results.append({
            "position": to_int_or_none(pos),
            "driverNumber": row.get("DriverNumber", ""),
            "abbreviation": row.get("Abbreviation", ""),
            "name": row.get("FullName", ""),
            "team": row.get("TeamName", ""),
            "team_color": row.get("TeamColor", ""),
            "headshot_url": row.get("HeadshotUrl", ""),
            "country_code": row.get("CountryCode", ""),
            "q1": format_lap_time(row.get("Q1")),
            "q2": format_lap_time(row.get("Q2")),
            "q3": format_lap_time(row.get("Q3")),
            # works for practice/quali/race now:
            "bestLapTime": format_lap_time(row.get("BestLapTime")),
            "lastLapTime": format_lap_time(row.get("FinalLapTime")),
            "status": row.get("Status", ""),
            # this now also filled for practice + quali:
            "numberOfLaps": to_int_or_none(laps_val),
            "points": to_int_or_none(points),
            "gridPos": to_int_or_none(gridPos),
        })

    return JsonResponse({"results": results})


# --- Helpers

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

    # Convert numpy scalar types → Python native
    df = df.map(lambda x: x.item() if hasattr(x, "item") else x)

    df = df.replace({np.nan: None})

    return df

def add_lap_number_from_lapstarts(tel: pd.DataFrame, laps_drv: pd.DataFrame) -> pd.DataFrame:
    """
    tel: telemetry for ONE driver, must include column 'Time'
    laps_drv: session.laps filtered to ONE driver, must include 'LapNumber' and 'LapStartTime'
    """
    print("adding lap data to the tel data")
    tel = tel.sort_values("Time").copy()

    lapstarts = (
        laps_drv[["LapNumber", "LapStartTime"]]
        .dropna()
        .sort_values("LapStartTime")
        .copy()
    )

    # Assign the latest lap start that is <= telemetry time
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
    print("assining the live positions")
    df_bin = df_bin.copy()

    # You want exactly one row per driver per TimeBin.
    # If you have multiple samples per driver per bin, keep the latest sample.
    df_bin = df_bin.sort_values("Time").drop_duplicates(subset=["DriverNumber"], keep="last")

    # Sort "front to back"
    df_bin = df_bin.sort_values(["LapNumber", "Distance"], ascending=[False, False])

    df_bin["LivePosition"] = range(1, len(df_bin) + 1)
    return df_bin

def clean_for_json(obj):
    print("-- cleaning json")
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

# --- Template Views

def _parse_bool(s: str) -> bool:
    return str(s).lower() in ("1", "true", "yes", "on")


def _parse_csv_param(request, name: str) -> list[str]:
    raw = request.GET.get(name, "")
    return [x.strip().upper() for x in raw.split(",") if x.strip()]

@csrf_exempt
def vr_create_view(request):
    body = json.loads(request.body)
    template_id = body["templateId"]
    inputs = body.get("inputs", {})

    if template_id == "t1":
        return vr_pace_1(int(inputs.get("year", "")), inputs.get("country", ""), inputs.get("session_name", ""), inputs)
    elif template_id == "t2":
        return vr_pace_2(int(inputs.get("year", "")), inputs.get("country", ""), inputs.get("session_name", ""), inputs)
    elif template_id == "t3":
        return vr_pace_3(int(inputs.get("year", "")), inputs.get("country", ""), inputs.get("session_name", ""), inputs)
    elif template_id == "t4":
        return vr_pace_4(int(inputs.get("year", "")), inputs.get("country", ""), inputs.get("session_name", ""), inputs)
    elif template_id == "t23":
        return vr_positions_3(inputs)
    elif template_id == "t24":
        return vr_tsp_1(int(inputs.get("season", 0)), inputs.get("team", ""), inputs)
    elif template_id == "t25":
        return vr_tsp_2(int(inputs.get("season", 0)), inputs.get("team", ""), inputs)
    elif template_id == "t26":
        return vr_tsp_3(int(inputs.get("season", 0)), inputs.get("team", ""), inputs)
    elif template_id == "t27":
        return vr_tsp_4(int(inputs.get("seasonFrom", 0)), inputs.get("seasonTo", ""), inputs.get("team", ""), inputs)
    elif template_id == "t28":
        return vr_tsp_5(int(inputs.get("seasonFrom", 0)), inputs.get("seasonTo", ""), inputs.get("team", ""), inputs)
    elif template_id == "t29":
        return vr_tsp_6(int(inputs.get("seasonFrom", 0)), inputs.get("seasonTo", ""), inputs.get("team", ""), inputs)
    elif template_id == "t30":
        return vr_tsp_7(int(inputs.get("season", 0)), inputs.get("team", ""), inputs)
    elif template_id == "t31":
        return vr_tsp_8(int(inputs.get("season", 0)), inputs.get("team", ""), inputs)


    return JsonResponse({"error": "Unknown templateId"}, status=400)


def vr_tsp_1(season_year: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()

    # 1) Load season schedule
    try:
        schedule = fastf1.get_event_schedule(season_year)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to load schedule: {e}")

    if schedule is None or schedule.empty:
        return HttpResponseBadRequest(f"No schedule found for {season_year}")

    round_col = "RoundNumber"
    if round_col not in schedule.columns:
        return HttpResponseBadRequest("Schedule missing 'RoundNumber' column.")

    rows = []

    # 2) Iterate through rounds
    for _, event in schedule.iterrows():
        round_number = int(event["RoundNumber"])

        # Skip invalid rounds (testing etc.)
        if round_number <= 0:
            continue

        try:
            session = fastf1.get_session(season_year, round_number, session_type)
            session.load(laps=False, telemetry=False, weather=False, messages=False)
        except Exception:
            continue  # Skip failed rounds safely

        results = session.results
        if results is None or results.empty:
            continue

        if "TeamName" not in results.columns or "Points" not in results.columns:
            continue

        # Direct exact match
        team_results = results[results["TeamName"] == team_name]

        if team_results.empty:
            continue

        points = pd.to_numeric(team_results["Points"], errors="coerce").fillna(0).sum()

        rows.append({
            "Round": round_number,
            "Event": event.get("EventName", f"Round {round_number}"),
            "Points": float(points),
        })

    if not rows:
        return HttpResponseBadRequest(
            f"No results found for team='{team_name}' in {season_year}"
        )

    df = pd.DataFrame(rows).sort_values("Round")

    # 3) Create Plotly figure
    fig = px.line(
        df,
        x="Round",
        y="Points",
        markers=True,
        title=f"{season_year} — {team_name} points per round",
        labels={"Round": "Round", "Points": "Points"},
        hover_data=["Event", "Points"],
    )

    fig.update_layout(
        margin=dict(l=40, r=20, t=60, b=40),
        legend_title_text="",
    )

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "id": "t24",
        "title": "Team points per race (season trend)",
        "result": {
            "type": "plotly",
            "figure": figure_dict,
        },
        "meta": {
            "season": season_year,
            "team": team_name,
            "session_type": session_type,
            "source": "fastf1",
        },
    }

    return JsonResponse(payload)

# ---------------------------
# Helpers (FastF1-only)
# ---------------------------

def _get_schedule(year: int):
    schedule = fastf1.get_event_schedule(year)
    if schedule is None or schedule.empty:
        return None
    if "RoundNumber" not in schedule.columns:
        return None
    return schedule


def _safe_event_name(event_row):
    # EventName exists in recent FastF1, but keep defensive
    return event_row.get("EventName", None) or event_row.get("OfficialEventName", None) or f"Round {int(event_row['RoundNumber'])}"


def _safe_circuit_label(event_row):
    # FastF1 schedule doesn't always expose circuit name directly.
    # Location is usually a good proxy (e.g., "Silverstone", "Monza").
    loc = event_row.get("Location", "") or ""
    country = event_row.get("Country", "") or ""
    if loc and country:
        return f"{loc} ({country})"
    return loc or country or _safe_event_name(event_row)


def _load_session(year: int, round_number: int, session_type: str, laps: bool = False):
    session = fastf1.get_session(year, round_number, session_type)
    session.load(laps=laps, telemetry=False, weather=False, messages=False)
    return session


def _timedelta_to_seconds(series: pd.Series) -> pd.Series:
    if pd.api.types.is_timedelta64_dtype(series):
        return series.dt.total_seconds()
    return pd.to_numeric(series, errors="coerce")


def _clean_laps(laps: pd.DataFrame, exclude_pit: bool = True, exclude_sc: bool = True) -> pd.DataFrame:
    """Best-effort clean lap filtering across seasons/years."""
    out = laps.copy()
    if "LapTime" in out.columns:
        out = out[out["LapTime"].notna()]
    if exclude_pit:
        for c in ["PitInTime", "PitOutTime"]:
            if c in out.columns:
                out = out[out[c].isna()]
    if "IsAccurate" in out.columns:
        out = out[out["IsAccurate"] == True]
    if exclude_sc and "TrackStatus" in out.columns:
        # Best-effort: SC/VSC often encoded with 4/5 among other flags
        out = out[~out["TrackStatus"].astype(str).str.contains("4|5", regex=True)]
    return out


# ============================================================
# t25 — Finish position distribution (boxplot)
# ============================================================

def vr_tsp_2(season_year: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()

    schedule = _get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"Failed to load schedule for {season_year} (missing/empty schedule or RoundNumber).")

    positions = []

    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        if rnd <= 0:
            continue

        try:
            session = _load_session(season_year, rnd, session_type, laps=False)
        except Exception:
            continue

        results = session.results
        if results is None or results.empty:
            continue
        if "TeamName" not in results.columns:
            continue

        team_res = results[results["TeamName"] == team_name].copy()
        if team_res.empty:
            continue

        # "Position" is commonly present; be defensive
        pos_col = "Position" if "Position" in team_res.columns else ("ClassifiedPosition" if "ClassifiedPosition" in team_res.columns else None)
        if pos_col is None:
            continue

        team_res[pos_col] = pd.to_numeric(team_res[pos_col], errors="coerce")
        team_res = team_res[team_res[pos_col].notna()]

        for _, r in team_res.iterrows():
            positions.append({
                "Round": rnd,
                "Event": _safe_event_name(event),
                "Driver": r.get("Abbreviation", r.get("FullName", "")),
                "Position": int(r[pos_col]),
            })

    if not positions:
        return HttpResponseBadRequest(f"No finishing positions found for team='{team_name}' in {season_year}.")

    df = pd.DataFrame(positions)

    fig = px.box(
        df,
        y="Position",
        points="all",
        title=f"{season_year} — {team_name} finish position distribution",
        labels={"Position": "Finish position"},
        hover_data=["Round", "Event", "Driver", "Position"],
    )
    # Lower position number is better; invert y-axis so P1 is at top
    fig.update_yaxes(autorange="reversed")

    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40))

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t25",
        "title": "Finish position distribution (consistency boxplot)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "team": team_name, "session_type": session_type, "source": "fastf1"},
    }
    return JsonResponse(payload)


# ============================================================
# t26 — Grid vs finish scatter (race execution)
# ============================================================

def vr_tsp_3(season_year: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    exclude_nc = bool(inputs.get("exclude_non_classified", True))

    schedule = _get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"Failed to load schedule for {season_year}.")

    rows = []

    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        if rnd <= 0:
            continue

        try:
            session = _load_session(season_year, rnd, session_type, laps=False)
        except Exception:
            continue

        results = session.results
        if results is None or results.empty:
            continue

        if "TeamName" not in results.columns:
            continue

        team_res = results[results["TeamName"] == team_name].copy()
        if team_res.empty:
            continue

        # Column names vary slightly across versions
        grid_col = "GridPosition" if "GridPosition" in team_res.columns else ("Grid" if "Grid" in team_res.columns else None)
        pos_col = "Position" if "Position" in team_res.columns else ("ClassifiedPosition" if "ClassifiedPosition" in team_res.columns else None)

        if grid_col is None or pos_col is None:
            continue

        team_res[grid_col] = pd.to_numeric(team_res[grid_col], errors="coerce")
        team_res[pos_col] = pd.to_numeric(team_res[pos_col], errors="coerce")
        team_res = team_res[team_res[grid_col].notna() & team_res[pos_col].notna()]

        if exclude_nc and "Status" in team_res.columns:
            team_res = team_res[~team_res["Status"].astype(str).str.contains("DNF|DNS|DSQ|NC", case=False, na=False)]

        for _, r in team_res.iterrows():
            rows.append({
                "Round": rnd,
                "Event": _safe_event_name(event),
                "Driver": r.get("Abbreviation", r.get("FullName", "")),
                "Grid": int(r[grid_col]),
                "Finish": int(r[pos_col]),
                "PositionsGained": int(r[grid_col]) - int(r[pos_col]),
            })

    if not rows:
        return HttpResponseBadRequest(f"No grid/finish pairs found for team='{team_name}' in {season_year}.")

    df = pd.DataFrame(rows)

    fig = px.scatter(
        df,
        x="Grid",
        y="Finish",
        color="Driver",
        title=f"{season_year} — {team_name} grid vs finish",
        labels={"Grid": "Grid position", "Finish": "Finish position"},
        hover_data=["Round", "Event", "Driver", "Grid", "Finish", "PositionsGained"],
    )
    # Invert y so better finishes are higher on chart
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40), legend_title_text="Driver")

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t26",
        "title": "Grid vs finish scatter (race execution)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "team": team_name, "session_type": session_type, "source": "fastf1"},
    }
    return JsonResponse(payload)


# ============================================================
# t27 — Average points by circuit (bar)
# ============================================================

def vr_tsp_4(season_from: int, season_to: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    min_races = int(inputs.get("min_races", 2))

    if season_from > season_to:
        season_from, season_to = season_to, season_from

    rows = []

    for year in range(season_from, season_to + 1):
        schedule = _get_schedule(year)
        if schedule is None:
            continue

        for _, event in schedule.iterrows():
            rnd = int(event["RoundNumber"])
            if rnd <= 0:
                continue

            try:
                session = _load_session(year, rnd, session_type, laps=False)
            except Exception:
                continue

            results = session.results
            if results is None or results.empty:
                continue
            if "TeamName" not in results.columns or "Points" not in results.columns:
                continue

            team_res = results[results["TeamName"] == team_name]
            if team_res.empty:
                continue

            points = pd.to_numeric(team_res["Points"], errors="coerce").fillna(0).sum()
            rows.append({
                "Season": year,
                "Round": rnd,
                "Circuit": _safe_circuit_label(event),
                "Event": _safe_event_name(event),
                "Points": float(points),
            })

    if not rows:
        return HttpResponseBadRequest(f"No points found for team='{team_name}' from {season_from} to {season_to}.")

    df = pd.DataFrame(rows)

    agg = (
        df.groupby("Circuit", as_index=False)
          .agg(Races=("Points", "size"), AvgPoints=("Points", "mean"), TotalPoints=("Points", "sum"))
    )
    agg = agg[agg["Races"] >= min_races].sort_values("AvgPoints", ascending=False)

    if agg.empty:
        return HttpResponseBadRequest(f"No circuits meet min_races={min_races} for team='{team_name}' in {season_from}-{season_to}.")

    fig = px.bar(
        agg,
        x="Circuit",
        y="AvgPoints",
        title=f"{team_name} — average points by circuit ({season_from}–{season_to})",
        labels={"Circuit": "Circuit (proxy)", "AvgPoints": "Average points"},
        hover_data=["Races", "TotalPoints", "AvgPoints"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=80))
    fig.update_xaxes(tickangle=30)

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t27",
        "title": "Average points by circuit",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season_from": season_from, "season_to": season_to, "team": team_name, "session_type": session_type, "min_races": min_races, "source": "fastf1"},
    }
    return JsonResponse(payload)


# ============================================================
# t28 — Best and worst circuits table
# ============================================================

def vr_tsp_5(season_from: int, season_to: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    min_races = int(inputs.get("min_races", 2))
    top_n = int(inputs.get("top_n", 5))

    if season_from > season_to:
        season_from, season_to = season_to, season_from

    # Reuse the same aggregation approach as t27
    rows = []
    for year in range(season_from, season_to + 1):
        schedule = _get_schedule(year)
        if schedule is None:
            continue

        for _, event in schedule.iterrows():
            rnd = int(event["RoundNumber"])
            if rnd <= 0:
                continue
            try:
                session = _load_session(year, rnd, session_type, laps=False)
            except Exception:
                continue
            results = session.results
            if results is None or results.empty:
                continue
            if "TeamName" not in results.columns or "Points" not in results.columns:
                continue

            team_res = results[results["TeamName"] == team_name]
            if team_res.empty:
                continue

            points = pd.to_numeric(team_res["Points"], errors="coerce").fillna(0).sum()
            rows.append({
                "Circuit": _safe_circuit_label(event),
                "Points": float(points),
            })

    if not rows:
        return HttpResponseBadRequest(f"No points found for team='{team_name}' from {season_from} to {season_to}.")

    df = pd.DataFrame(rows)
    agg = (
        df.groupby("Circuit", as_index=False)
          .agg(Races=("Points", "size"), AvgPoints=("Points", "mean"), TotalPoints=("Points", "sum"))
    )
    agg = agg[agg["Races"] >= min_races].copy()
    if agg.empty:
        return HttpResponseBadRequest(f"No circuits meet min_races={min_races} for team='{team_name}' in {season_from}-{season_to}.")

    best = agg.sort_values("AvgPoints", ascending=False).head(top_n)
    worst = agg.sort_values("AvgPoints", ascending=True).head(top_n)

    # Build a single table with a "Bucket" column
    table_df = pd.concat([
        best.assign(Bucket="Best"),
        worst.assign(Bucket="Worst"),
    ], ignore_index=True)

    table_df = table_df[["Bucket", "Circuit", "Races", "AvgPoints", "TotalPoints"]]
    table_df["AvgPoints"] = table_df["AvgPoints"].round(2)
    table_df["TotalPoints"] = table_df["TotalPoints"].round(1)

    payload = {
        "id": "t28",
        "title": "Best and worst circuits table",
        "result": {
            "type": "table",
            "columns": list(table_df.columns),
            "rows": table_df.values.tolist(),
        },
        "meta": {
            "season_from": season_from,
            "season_to": season_to,
            "team": team_name,
            "session_type": session_type,
            "min_races": min_races,
            "top_n": top_n,
            "source": "fastf1",
        },
    }
    return JsonResponse(payload)


# ============================================================
# t29 — Circuit performance heatmap (circuits x seasons)
# ============================================================

def vr_tsp_6(season_from: int, season_to: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    min_races = int(inputs.get("min_races", 1))

    if season_from > season_to:
        season_from, season_to = season_to, season_from

    rows = []

    for year in range(season_from, season_to + 1):
        schedule = _get_schedule(year)
        if schedule is None:
            continue

        for _, event in schedule.iterrows():
            rnd = int(event["RoundNumber"])
            if rnd <= 0:
                continue

            try:
                session = _load_session(year, rnd, session_type, laps=False)
            except Exception:
                continue

            results = session.results
            if results is None or results.empty:
                continue
            if "TeamName" not in results.columns or "Points" not in results.columns:
                continue

            team_res = results[results["TeamName"] == team_name]
            if team_res.empty:
                continue

            points = pd.to_numeric(team_res["Points"], errors="coerce").fillna(0).sum()

            rows.append({
                "Season": year,
                "Circuit": _safe_circuit_label(event),
                "Points": float(points),
            })

    if not rows:
        return HttpResponseBadRequest(f"No circuit/season points found for team='{team_name}' in {season_from}-{season_to}.")

    df = pd.DataFrame(rows)

    # Aggregate to season x circuit mean points
    agg = (
        df.groupby(["Season", "Circuit"], as_index=False)
          .agg(Races=("Points", "size"), AvgPoints=("Points", "mean"))
    )
    agg = agg[agg["Races"] >= min_races].copy()
    if agg.empty:
        return HttpResponseBadRequest(f"No cells meet min_races={min_races} for team='{team_name}' in {season_from}-{season_to}.")

    pivot = agg.pivot(index="Circuit", columns="Season", values="AvgPoints").fillna(0.0)

    fig = px.imshow(
        pivot,
        aspect="auto",
        title=f"{team_name} — circuit performance heatmap ({season_from}–{season_to})",
        labels={"x": "Season", "y": "Circuit (proxy)", "color": "Avg points"},
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=60))

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t29",
        "title": "Circuit performance heatmap",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season_from": season_from, "season_to": season_to, "team": team_name, "session_type": session_type, "min_races": min_races, "source": "fastf1"},
    }
    return JsonResponse(payload)


# ============================================================
# t30 — Race pace delta vs field (boxplot)
# ============================================================

def vr_tsp_7(season_year: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    exclude_pit = bool(inputs.get("exclude_pit_laps", True))
    exclude_sc = bool(inputs.get("exclude_sc_vsc", True))

    schedule = _get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"Failed to load schedule for {season_year}.")

    rows = []

    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        if rnd <= 0:
            continue

        try:
            session = _load_session(season_year, rnd, session_type, laps=True)
        except Exception:
            continue

        laps = session.laps
        if laps is None or laps.empty:
            continue

        laps = _clean_laps(laps, exclude_pit=exclude_pit, exclude_sc=exclude_sc)
        if laps.empty:
            continue

        # Convert lap time to seconds
        laps = laps.copy()
        laps["LapTimeSeconds"] = _timedelta_to_seconds(laps["LapTime"])
        laps = laps[laps["LapTimeSeconds"].notna()]

        if laps.empty:
            continue

        # Field median (one value per race)
        field_median = float(laps["LapTimeSeconds"].median())

        # Team laps
        if "Team" in laps.columns:
            team_laps = laps[laps["Team"] == team_name].copy()
        elif "TeamName" in laps.columns:
            team_laps = laps[laps["TeamName"] == team_name].copy()
        else:
            # If laps doesn't carry team, use results to map drivers -> team
            # (rare; but defensive)
            res = session.results
            if res is None or res.empty or "TeamName" not in res.columns:
                continue
            team_drivers = res.loc[res["TeamName"] == team_name, "Abbreviation"].dropna().unique().tolist()
            if "Driver" in laps.columns:
                team_laps = laps[laps["Driver"].isin(team_drivers)].copy()
            else:
                continue

        if team_laps.empty:
            continue

        # Delta per team lap vs field median
        team_laps["DeltaToFieldMedian"] = team_laps["LapTimeSeconds"] - field_median

        # Keep for plot
        for _, r in team_laps.iterrows():
            rows.append({
                "Round": rnd,
                "Event": _safe_event_name(event),
                "Driver": r.get("Driver", ""),
                "Compound": r.get("Compound", ""),
                "Stint": int(r["Stint"]) if "Stint" in team_laps.columns and pd.notna(r.get("Stint")) else None,
                "DeltaToFieldMedian": float(r["DeltaToFieldMedian"]),
            })

    if not rows:
        return HttpResponseBadRequest(f"No pace delta data found for team='{team_name}' in {season_year}.")

    df = pd.DataFrame(rows)

    fig = px.box(
        df,
        y="DeltaToFieldMedian",
        points="all",
        title=f"{season_year} — {team_name} race pace delta vs field median",
        labels={"DeltaToFieldMedian": "Lap time delta to field median (s)"},
        hover_data=["Round", "Event", "Driver", "Compound", "Stint", "DeltaToFieldMedian"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40))

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t30",
        "title": "Race pace delta vs field (boxplot)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "team": team_name, "session_type": session_type, "exclude_pit_laps": exclude_pit, "exclude_sc_vsc": exclude_sc, "source": "fastf1"},
    }
    return JsonResponse(payload)


# ============================================================
# t31 — Tyre degradation by compound (stint analysis line)
# ============================================================

def vr_tsp_8(season_year: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    min_stint_laps = int(inputs.get("min_stint_laps", 6))
    exclude_pit = bool(inputs.get("exclude_pit_laps", True))
    exclude_sc = bool(inputs.get("exclude_sc_vsc", True))

    schedule = _get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"Failed to load schedule for {season_year}.")

    all_rows = []

    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        if rnd <= 0:
            continue

        try:
            session = _load_session(season_year, rnd, session_type, laps=True)
        except Exception:
            continue

        laps = session.laps
        if laps is None or laps.empty:
            continue

        laps = _clean_laps(laps, exclude_pit=exclude_pit, exclude_sc=exclude_sc)
        if laps.empty:
            continue

        # Need team column + compound + stint
        if "Team" not in laps.columns or "Compound" not in laps.columns or "Stint" not in laps.columns:
            continue

        team_laps = laps[laps["Team"] == team_name].copy()
        if team_laps.empty:
            continue

        team_laps["LapTimeSeconds"] = _timedelta_to_seconds(team_laps["LapTime"])
        team_laps = team_laps[team_laps["LapTimeSeconds"].notna()]
        if team_laps.empty:
            continue

        # Compute LapInStint as sequence count per (Driver, Stint)
        if "Driver" not in team_laps.columns or "LapNumber" not in team_laps.columns:
            continue

        team_laps = team_laps.sort_values(["Driver", "Stint", "LapNumber"])
        team_laps["LapInStint"] = team_laps.groupby(["Driver", "Stint"]).cumcount() + 1

        # Filter out short stints (to reduce SC/oddity noise)
        stint_sizes = team_laps.groupby(["Driver", "Stint"]).size().rename("StintSize").reset_index()
        team_laps = team_laps.merge(stint_sizes, on=["Driver", "Stint"], how="left")
        team_laps = team_laps[team_laps["StintSize"] >= min_stint_laps]

        if team_laps.empty:
            continue

        # Keep for aggregation
        team_laps["Round"] = rnd
        team_laps["Event"] = _safe_event_name(event)

        all_rows.append(team_laps[["Compound", "LapInStint", "LapTimeSeconds"]])

    if not all_rows:
        return HttpResponseBadRequest(f"No stint/compound lap data found for team='{team_name}' in {season_year}.")

    df = pd.concat(all_rows, ignore_index=True)

    # Aggregate median lap time by compound and lap-in-stint
    agg = (
        df.groupby(["Compound", "LapInStint"], as_index=False)
          .agg(MedianLapTime=("LapTimeSeconds", "median"), N=("LapTimeSeconds", "size"))
          .sort_values(["Compound", "LapInStint"])
    )

    fig = px.line(
        agg,
        x="LapInStint",
        y="MedianLapTime",
        color="Compound",
        markers=True,
        title=f"{season_year} — {team_name} tyre degradation by compound",
        labels={"LapInStint": "Lap in stint", "MedianLapTime": "Median lap time (s)"},
        hover_data=["Compound", "LapInStint", "MedianLapTime", "N"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40), legend_title_text="Compound")

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t31",
        "title": "Tyre degradation by compound (stint analysis)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "team": team_name, "session_type": session_type, "min_stint_laps": min_stint_laps, "exclude_pit_laps": exclude_pit, "exclude_sc_vsc": exclude_sc, "source": "fastf1"},
    }
    return JsonResponse(payload)

# -- Race templates

# -	Driver laptimes (scatterplot)
def vr_pace_1(year, country, session_name, inputs):
    drivers = inputs.get("drivers", [])
    exclude_sc = _parse_bool(inputs.get("excludeSCVSC", False))

    # 1) Load session
    try:
        session = fastf1.get_session(year, country, session_name)
        session.load(laps=True, telemetry=False, weather=False)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to load session: {e}")

    laps = session.laps.copy()

    # 2) Filter to selected drivers
    laps = laps[laps["Driver"].isin(drivers)]

    # 3) Keep only laps with a valid LapTime
    laps = laps[laps["LapTime"].notna()]

    # 4) Exclude SC/VSC laps (only if column exists in your laps data)
    # FastF1 can vary by session/year; keep this defensive.
    if exclude_sc and "TrackStatus" in laps.columns:
        # TrackStatus is typically a string of marshalling flags.
        # This is a best-effort filter; adjust if you have a more reliable SC/VSC indicator.
        laps = laps[~laps["TrackStatus"].astype(str).str.contains("4|5", regex=True)]

    # 5) Convert LapTime (Timedelta) -> seconds float (JSON-friendly)
    # FastF1 LapTime is usually pandas Timedelta
    if pd.api.types.is_timedelta64_dtype(laps["LapTime"]):
        laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    else:
        # Fallback if it comes already numeric/string
        laps["LapTimeSeconds"] = pd.to_numeric(laps["LapTime"], errors="coerce")
        laps = laps[laps["LapTimeSeconds"].notna()]

    # 6) Build Plotly scatter
    fig = px.scatter(
        laps,
        x="LapNumber",
        y="LapTimeSeconds",
        color="Driver",
        title=f"{year} {country} {session_name} — Driver laptimes",
        labels={"LapNumber": "Lap", "LapTimeSeconds": "Lap time (s)"},
        hover_data=[c for c in ["Compound", "Stint", "TyreLife"] if c in laps.columns],
    )

    # Optional: make “faster = higher” by reversing y-axis (some people prefer this)
    # fig.update_yaxes(autorange="reversed")

    fig.update_layout(
        margin=dict(l=40, r=20, t=60, b=40),
        legend_title_text="Driver",
    )

    # 7) Convert figure to JSON-safe dict and return
    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "title": "Driver laptimes (scatter)",
        "result": {
            "type": "plotly",
            "figure": figure_dict,
        },
    }

    return JsonResponse(payload)

# - Driver laptimes (distribution chart)
def vr_pace_2(year, country, session_name, inputs):
    drivers = inputs.get("drivers", [])
    exclude_sc = _parse_bool(inputs.get("excludeSCVSC", False))
    show_points = _parse_bool(inputs.get("showPoints", True))

    # 1) Load session
    try:
        session = fastf1.get_session(year, country, session_name)
        session.load(laps=True, telemetry=False, weather=False)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to load session: {e}")

    laps = session.laps.copy()

    # 2) Filter to selected drivers (if provided)
    if drivers:
        laps = laps[laps["Driver"].isin(drivers)]

    # 3) Keep only laps with valid LapTime
    laps = laps[laps["LapTime"].notna()].copy()
    if laps.empty:
        return HttpResponseBadRequest("No valid laptimes found after filtering.")

    # 4) Exclude SC/VSC laps (defensive; TrackStatus can vary)
    if exclude_sc and "TrackStatus" in laps.columns:
        laps = laps[~laps["TrackStatus"].astype(str).str.contains("4|5", regex=True)]

    if laps.empty:
        return HttpResponseBadRequest("No laptimes left after SC/VSC filtering.")

    # 5) Convert LapTime (Timedelta) -> seconds float (JSON-friendly)
    if pd.api.types.is_timedelta64_dtype(laps["LapTime"]):
        laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    else:
        laps["LapTimeSeconds"] = pd.to_numeric(laps["LapTime"], errors="coerce")
        laps = laps[laps["LapTimeSeconds"].notna()]

    if laps.empty:
        return HttpResponseBadRequest("LapTime could not be converted to seconds.")

    # 6) Distribution chart (violin per driver)
    fig = px.violin(
        laps,
        x="Driver",
        y="LapTimeSeconds",
        box=True,  # show embedded boxplot
        points="all" if show_points else False,
        title=f"{year} {country} {session_name} — Driver laptime distribution",
        labels={"Driver": "Driver", "LapTimeSeconds": "Lap time (s)"},
        hover_data=[c for c in ["Compound", "Stint", "TyreLife", "LapNumber"] if c in laps.columns],
    )

    fig.update_layout(
        margin=dict(l=40, r=20, t=60, b=40),
        xaxis_title="Driver",
        yaxis_title="Lap time (s)",
    )

    # Optional: make faster times appear higher
    # fig.update_yaxes(autorange="reversed")

    # 7) Convert figure to JSON-safe dict and return
    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "title": "Driver laptimes (distribution)",
        "result": {
            "type": "plotly",
            "figure": figure_dict,
        },
    }

    return JsonResponse(payload)

# -	Lap time trend (line chart)
def vr_pace_3(year, country, session_name, inputs):
    drivers = inputs.get("drivers", [])
    exclude_sc = _parse_bool(inputs.get("excludeSCVSC", False))

    # 1) Load session
    try:
        session = fastf1.get_session(year, country, session_name)
        session.load(laps=True, telemetry=False, weather=False)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to load session: {e}")

    laps = session.laps.copy()

    # 2) Filter to selected drivers
    laps = laps[laps["Driver"].isin(drivers)]

    # 3) Keep only laps with a valid LapTime
    laps = laps[laps["LapTime"].notna()]

    # 4) Exclude SC/VSC laps (only if column exists in your laps data)
    # FastF1 can vary by session/year; keep this defensive.
    if exclude_sc and "TrackStatus" in laps.columns:
        # TrackStatus is typically a string of marshalling flags.
        # This is a best-effort filter; adjust if you have a more reliable SC/VSC indicator.
        laps = laps[~laps["TrackStatus"].astype(str).str.contains("4|5", regex=True)]

    # 5) Convert LapTime (Timedelta) -> seconds float (JSON-friendly)
    # FastF1 LapTime is usually pandas Timedelta
    if pd.api.types.is_timedelta64_dtype(laps["LapTime"]):
        laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    else:
        # Fallback if it comes already numeric/string
        laps["LapTimeSeconds"] = pd.to_numeric(laps["LapTime"], errors="coerce")
        laps = laps[laps["LapTimeSeconds"].notna()]

    # 6) Build Plotly line chart
    fig = px.line(
        laps,
        x="LapNumber",
        y="LapTimeSeconds",
        color="Driver",
        title=f"{year} {country} {session_name} — Driver laptimes",
        labels={"LapNumber": "Lap", "LapTimeSeconds": "Lap time (s)"},
        hover_data=[c for c in ["Compound", "Stint", "TyreLife"] if c in laps.columns],
    )

    # Optional: make “faster = higher” by reversing y-axis (some people prefer this)
    # fig.update_yaxes(autorange="reversed")

    fig.update_layout(
        margin=dict(l=40, r=20, t=60, b=40),
        legend_title_text="Driver",
    )

    # 7) Convert figure to JSON-safe dict and return
    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "title": "Driver laptimes (line chart)",
        "result": {
            "type": "plotly",
            "figure": figure_dict,
        },
    }

    return JsonResponse(payload)

# -	Sector time breakdown (S1/S2/S3 per driver) (grouped bar chart/line chart)
def vr_pace_4(year, country, session_name, inputs):
    drivers = inputs.get("drivers", [])
    exclude_sc = _parse_bool(inputs.get("excludeSCVSC", False))

    # 1) Load session
    try:
        session = fastf1.get_session(year, country, session_name)
        session.load(laps=True, telemetry=False, weather=False)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to load session: {e}")

    laps = session.laps.copy()

    # 2) Filter to selected drivers (if provided)
    if drivers:
        laps = laps[laps["Driver"].isin(drivers)]

    # 3) Ensure sector columns exist
    sector_cols = ["Sector1Time", "Sector2Time", "Sector3Time"]
    missing = [c for c in sector_cols if c not in laps.columns]
    if missing:
        return HttpResponseBadRequest(
            f"Sector columns missing in this session data: {missing}"
        )

    # 4) Exclude SC/VSC laps (best-effort defensive)
    if exclude_sc and "TrackStatus" in laps.columns:
        laps = laps[~laps["TrackStatus"].astype(str).str.contains("4|5", regex=True)]

    # 5) Keep only laps with all 3 sector times
    for c in sector_cols:
        laps = laps[laps[c].notna()]

    if laps.empty:
        return HttpResponseBadRequest(
            "No laps available after filtering (sectors missing/filtered out)."
        )

    # 6) Convert sector timedeltas to seconds
    for c in sector_cols:
        out = c + "Seconds"
        if pd.api.types.is_timedelta64_dtype(laps[c]):
            laps[out] = laps[c].dt.total_seconds()
        else:
            laps[out] = pd.to_numeric(laps[c], errors="coerce")
            laps = laps[laps[out].notna()]

    s1, s2, s3 = "Sector1TimeSeconds", "Sector2TimeSeconds", "Sector3TimeSeconds"

    # 7) Aggregate per driver
    cols = [s1, s2, s3]
    grp = laps.groupby("Driver", as_index=False)[cols].median()
    agg_label = "Median"

    if grp.empty:
        return HttpResponseBadRequest("No aggregated sector data to plot.")

    # Optional: stable ordering (fastest total first)
    grp["TotalSeconds"] = grp[s1] + grp[s2] + grp[s3]
    grp = grp.sort_values("TotalSeconds", ascending=True)

    # 8) Build grouped bar chart + line overlay
    sectors = ["Sector 1", "Sector 2", "Sector 3"]
    fig = go.Figure()

    for _, row in grp.iterrows():
        drv = row["Driver"]

        s1 = row["Sector1TimeSeconds"]
        s2 = row["Sector2TimeSeconds"]
        s3 = row["Sector3TimeSeconds"]

        cumulative = [s1, s1 + s2, s1 + s2 + s3]

        # Bars: sector times
        fig.add_trace(go.Bar(
            name=drv,
            x=sectors,
            y=[s1, s2, s3],
            legendgroup=drv,
            hovertemplate=(
                "Driver=%{fullData.name}<br>"
                "%{x}=%{y:.3f}s<extra></extra>"
            ),
        ))

        # Line overlay: cumulative total
        fig.add_trace(go.Scatter(
            name=f"{drv} total",
            x=sectors,
            y=cumulative,
            mode="lines+markers",
            yaxis="y2",
            legendgroup=drv,
            showlegend=False,  # prevents legend spam
            hovertemplate=(
                "Driver=" + drv + "<br>"
                "Cumulative=%{y:.3f}s<extra></extra>"
            ),
        ))
        
    fig.update_layout(
        title=f"Sector time breakdown (S1/S2/S3 per driver) — grouped bar chart",
        barmode="group",
        xaxis=dict(title="Sector", type="category"),
        yaxis=dict(title="Sector time (s)"),
        yaxis2=dict(
            title="Cumulative time (s)",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend_title_text="Driver",
    )

    # 9) Convert to JSON-safe dict and return
    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "title": "Sector time breakdown (S1/S2/S3 per driver) — grouped bar chart",
        "result": {"type": "plotly", "figure": figure_dict}
    }

    return JsonResponse(payload)


def _ergast_to_df(resp):
    # supports resp.content[0], resp.df, or DataFrame directly
    if resp is None:
        return None
    if isinstance(resp, pd.DataFrame):
        return resp
    if hasattr(resp, "content"):
        c = resp.content
        if isinstance(c, (list, tuple)) and len(c) > 0:
            return c[0] if isinstance(c[0], pd.DataFrame) else pd.DataFrame(c[0])
    if hasattr(resp, "df") and isinstance(resp.df, pd.DataFrame):
        return resp.df
    try:
        return pd.DataFrame(resp)
    except Exception:
        return None


def vr_positions_3(inputs):
    # --- Inputs ---
    SEASON = int(inputs.get("season", 2024))
    ROUND = int(inputs.get("round", 1))

    ergast = Ergast()

    # 1) standings
    try:
        standings = ergast.get_driver_standings(season=SEASON, round=ROUND)
        driver_standings = _ergast_to_df(standings)
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to fetch driver standings: {e}")

    if driver_standings is None or driver_standings.empty:
        return HttpResponseBadRequest("No driver standings returned.")

    # normalize
    for col in ["position", "points", "givenName", "familyName"]:
        if col not in driver_standings.columns:
            return HttpResponseBadRequest(f"Standings missing '{col}' column.")

    driver_standings = driver_standings.copy()
    driver_standings["points"] = pd.to_numeric(driver_standings["points"], errors="coerce")
    driver_standings["position_num"] = pd.to_numeric(driver_standings["position"], errors="coerce")
    driver_standings = driver_standings.dropna(subset=["points", "position_num"])
    driver_standings = driver_standings.sort_values("position_num").reset_index(drop=True)

    # 2) remaining points model (same as FastF1 example)
    POINTS_FOR_SPRINT = 8 + 25          # sprint win + race win
    POINTS_FOR_CONVENTIONAL = 25        # race win

    try:
        events = fastf1.events.get_event_schedule(SEASON, backend="ergast").copy()
    except Exception as e:
        return HttpResponseBadRequest(f"Failed to fetch event schedule: {e}")

    if "RoundNumber" not in events.columns or "EventFormat" not in events.columns:
        return HttpResponseBadRequest("Event schedule missing RoundNumber/EventFormat.")

    events["RoundNumber"] = pd.to_numeric(events["RoundNumber"], errors="coerce")
    events = events.dropna(subset=["RoundNumber"])
    remaining = events[events["RoundNumber"] > ROUND]

    sprint_events = int((remaining["EventFormat"] == "sprint_shootout").sum())
    conventional_events = int((remaining["EventFormat"] == "conventional").sum())

    max_points_remaining = sprint_events * POINTS_FOR_SPRINT + conventional_events * POINTS_FOR_CONVENTIONAL

    # 3) compute table rows
    leader_points = int(driver_standings.loc[0, "points"])

    out = driver_standings.copy()
    out["Driver"] = out["givenName"].astype(str) + " " + out["familyName"].astype(str)
    out["CurrentPoints"] = out["points"].round(0).astype(int)
    out["TheoreticalMax"] = (out["CurrentPoints"] + int(max_points_remaining)).astype(int)
    out["CanWin"] = out["TheoreticalMax"].apply(lambda p: "Yes" if p >= leader_points else "No")

    # sort: can win first, then points desc
    out["CanWinSort"] = out["CanWin"].map({"Yes": 0, "No": 1})
    out = out.sort_values(["CanWinSort", "CurrentPoints"], ascending=[True, False]).drop(columns=["CanWinSort"])

    # 4) build plotly Table figure
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=["Rank", "Driver", "Points", "Theoretical Max", "Can still win?"],
                    align="left",
                ),
                cells=dict(
                    values=[
                        out["position"].tolist(),
                        out["Driver"].tolist(),
                        out["CurrentPoints"].tolist(),
                        out["TheoreticalMax"].tolist(),
                        out["CanWin"].tolist(),
                    ],
                    align="left",
                ),
            )
        ]
    )

    fig.update_layout(
        title=f"{SEASON} — WDC still possible after Round {ROUND} (max remaining points={int(max_points_remaining)})",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    # 5) JSON-safe payload (same shape as your scatter example)
    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))

    payload = {
        "title": "Who can still win the WDC? (table)",
        "result": {
            "type": "plotly",
            "figure": figure_dict,
        },
        "meta": {
            "season": SEASON,
            "round": ROUND,
            "max_points_remaining": int(max_points_remaining),
            "sprint_events_remaining": sprint_events,
            "conventional_events_remaining": conventional_events,
        },
    }

    return JsonResponse(payload)