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

import fastf1
from fastf1.ergast import Ergast

ergast = Ergast(result_type="pandas", auto_cast=True)

def grandPrixEntered():
    resp = ergast.get_race_results(driver="hamilton", limit=1)
    print(resp.total_results) 

def careerPoints():
    seasons = ergast.get_seasons(driver="perez", limit=1000)
    seasons = list(seasons["season"])

    total_points = 0.0

    for year in seasons:
        standing = ergast.get_driver_standings(
            season=year,
            driver="perez",
            limit=1
        )
        if standing.content:
            points = standing.content[0].loc[0, "points"]
            if points > 0:
                total_points += points
    
    print(total_points)

def highest_race_finish():
    resp = ergast.get_race_results(driver="hamilton", limit=100)

    all_dfs = []

    # gets all rows with pagintation
    while True:
        all_dfs.extend(resp.content)
        try:
            resp = resp.get_next_result_page()
        except ValueError:
            break

    hrf_df = pd.concat(all_dfs, ignore_index=True)
    hrf_df["position"] = pd.to_numeric(hrf_df["position"], errors="coerce")
    best_position = hrf_df["position"].min()
    count = (hrf_df["position"] == best_position).sum()

    print(best_position)
    print(count)

def podiums():
    resp = ergast.get_race_results(driver="hamilton", limit=100)

    podiums = 0

    all_dfs = []

    # gets all rows with pagintation
    while True:
        all_dfs.extend(resp.content)
        try:
            resp = resp.get_next_result_page()
        except ValueError:
            break

    podiums_df = pd.concat(all_dfs, ignore_index=True)
    podiums_df["position"] = pd.to_numeric(podiums_df["position"], errors="coerce")

    for c in range(1,4):
        podiums += (podiums_df["position"] == c).sum()

    print(podiums)

def highest_grid_position():
    resp = ergast.get_race_results(driver="max_verstappen", limit=100)

    all_dfs = []

    # gets all rows with pagintation
    while True:
        all_dfs.extend(resp.content)
        try:
            resp = resp.get_next_result_page()
        except ValueError:
            break

    hgp_df = pd.concat(all_dfs, ignore_index=True)
    hgp_df["grid"] = pd.to_numeric(hgp_df["grid"], errors="coerce")
    best_grid_position = 1 if hgp_df["grid"].min() == 0 else hgp_df["grid"].min()
    count = (hgp_df["grid"] == best_grid_position).sum()

    print(best_grid_position)
    print(count)

def pole_positions():
    resp = ergast.get_race_results(driver="hamilton", grid_position=1, limit=1)
    print(resp.total_results)

def world_championships():
    seasons = ergast.get_seasons(driver="alonso", limit=1000)
    seasons = list(seasons["season"])

    count = 0

    for year in seasons:
        standing = ergast.get_driver_standings(
            season=year,
            driver="alonso",
            limit=1
        )
        if standing.content:
            try:
                position_col = standing.content[0].loc[0, "position"]
            except KeyError:
                position_col = standing.content[0].loc[0, "positionText"]
                if position_col == "-":
                    position_col = 0
                else:
                    position_col = int(position_col)
            if position_col == 1:
                count += 1
    
    print(count)

def DNFs():
    resp = ergast.get_finishing_status(driver="hamilton", limit=1000)
    df = pd.DataFrame(resp)

    finished_mask = (
        (df["status"] == "Finished") |
        (df["status"].str.startswith("+")) |
        (df["status"] == "Lapped")
    )

    # because disqualified is not equal to DNF
    dsq_mask = df["status"] == "Disqualified"

    dnfs = df.loc[~finished_mask & ~dsq_mask, "count"].sum()

    print(dnfs)


def mainFunction():
    driver_ergast_id = "piastri"

    # main necessary ergast requests
    race_results_ergast = ergast.get_race_results(driver=driver_ergast_id, limit=100)
    temp_df = []
    while True:
        temp_df.extend(race_results_ergast.content)
        try:
            race_results_ergast = race_results_ergast.get_next_result_page()
        except ValueError:
            break
    race_results_ergast_dfs = pd.concat(temp_df, ignore_index=True)

    seasons_ergast = ergast.get_seasons(driver=driver_ergast_id, limit=1000)
    seasons_ergast = list(seasons_ergast["season"])

    pole_positions_ergast = ergast.get_race_results(driver=driver_ergast_id, grid_position=1, limit=1)

    DNFs_ergast = ergast.get_finishing_status(driver=driver_ergast_id, limit=1000)

    driver_given_name = ""
    driver_family_name = ""

    # grand prix entered
    gp_entered = race_results_ergast.total_results

    # career points, world championships
    career_points = 0.0
    championships = 0

    for year in seasons_ergast:
        standing = ergast.get_driver_standings(
            season=year,
            driver=driver_ergast_id,
            limit=1
        )
        if standing.content: 
            points_col = standing.content[0].loc[0, "points"]

            career_points += points_col # career points

            try:
                position_col = standing.content[0].loc[0, "position"]
            except KeyError:
                position_col = standing.content[0].loc[0, "positionText"]
                if position_col == "-":
                    position_col = 0
                else:
                    position_col = int(position_col)
            if position_col == 1:
                championships += 1 # world championships

            if driver_given_name == "":
                driver_given_name = standing.content[0].loc[0, "givenName"]
            if driver_family_name == "":
                driver_family_name = standing.content[0].loc[0, "familyName"]


    # highest race finish
    hrf_valid = race_results_ergast_dfs.loc[race_results_ergast_dfs["position"].notna() & (race_results_ergast_dfs["position"] > 0), "position"]
    hrf_best_position = int(hrf_valid.min())
    hrf_count = (race_results_ergast_dfs["position"] == hrf_best_position).sum()

    # podiums
    podiums = 0
    for c in range(1,4):
        podiums += (race_results_ergast_dfs["position"] == c).sum()

    # highest grid position
    hgp_valid = race_results_ergast_dfs.loc[race_results_ergast_dfs["grid"].notna() & (race_results_ergast_dfs["grid"] > 0), "grid"]
    hgp_best_position = int(hgp_valid.min())
    hgp_count = (race_results_ergast_dfs["grid"] == hgp_best_position).sum()

    # pole positions
    pole_positions = pole_positions_ergast.total_results

    # DNFs
    dnf_df = pd.DataFrame(DNFs_ergast)

    finished_mask = (
        (dnf_df["status"] == "Finished") |
        (dnf_df["status"].str.startswith("+")) |
        (dnf_df["status"] == "Lapped")
    )

    # because disqualified is not equal to DNF
    dsq_mask = dnf_df["status"] == "Disqualified"

    dnfs = dnf_df.loc[~finished_mask & ~dsq_mask, "count"].sum()

    return ({
        "driver": f"{driver_given_name} {driver_family_name}",
        "grand_prix_entered": int(gp_entered),
        "career_points": float(career_points),
        "highest_race_finish": int(hrf_best_position),                    # e.g. 1
        "highest_race_finish_count": int(hrf_count),        # e.g. 105
        "podiums": int(podiums),
        "highest_grid_position": int(hgp_best_position),                # e.g. 1
        "highest_grid_position_count": int(hgp_count),    # e.g. 104
        "pole_positions": int(pole_positions),
        "world_championships": int(championships),
        "dnfs": int(dnfs),
    })

print(json.dumps(mainFunction(), indent=4))



    
    




#highest_grid_position()