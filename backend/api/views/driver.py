from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from api.models import Driver
from fastf1.ergast import Ergast
import pandas as pd

__all__ = [
    "drivers_getDrivers",
    "driver_getDriverCode",
    "driver_getDriverSummary"
]


def drivers_getDrivers(request):
    """
    Returns the list of drivers available in the database.

    Driver records are ordered by Ergast identifier and reduced to the
    fields required for frontend selection.

    Args:
        request: HTTP request object.

    Returns:
        JsonResponse: List of drivers with Ergast ID, given name and family name.
    """
    drivers = (
        Driver.objects
        .order_by("ergast_id")
        .values("ergast_id", "given_name", "family_name")
        .distinct()
    )

    return JsonResponse({"drivers": list(drivers)})

def driver_getDriverCode(request, driver_ergast_id: str):
    """
    Returns the driver code for a given Ergast driver identifier.

    The code is retrieved from the Ergast driver information endpoint and is
    used where a short driver abbreviation is required in the frontend.

    Args:
        request: HTTP request object.
        driver_ergast_id (str): Ergast identifier for the driver.

    Returns:
        JsonResponse: Driver abbreviation for the selected driver.
    """
    ergast = Ergast()
    df = ergast.get_driver_info(driver=driver_ergast_id)
    abbr = df.loc[0, "driverCode"]
    return JsonResponse({"driverCode": abbr})
    

def driver_getDriverSummary(request, driver_ergast_id: str):
    """
    Returns summary statistics for a driver using historical Ergast data.

    Race results, standings and finishing status data are aggregated to
    calculate overall career measures such as points, podiums, pole
    positions, championships, best finish and DNFs.

    Args:
        request: HTTP request object.
        driver_ergast_id (str): Ergast identifier for the driver.

    Returns:
        JsonResponse: Career summary statistics for the selected driver.
    """
    ergast = Ergast(result_type="pandas", auto_cast=True)

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

    return JsonResponse({
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