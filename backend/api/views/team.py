from django.http import JsonResponse
from api.models import Team
from fastf1.ergast import Ergast
import pandas as pd

__all__ = [
    "teams_getTeams",
    "teams_getTeamSummary"
]

def teams_getTeams(request):
    teams = (
        Team.objects
        .order_by("name")
        .values("name", "ergast_id")
    )

    return JsonResponse({"teams": list(teams)})

def teams_getTeamSummary(request, team_ergast_id: str):
    ergast = Ergast(result_type="pandas", auto_cast=True)

    # main necessary ergast requests
    race_results_ergast = ergast.get_race_results(constructor=team_ergast_id, limit=1000)
    temp_df = []
    while True:
        temp_df.extend(race_results_ergast.content)
        try:
            race_results_ergast = race_results_ergast.get_next_result_page()
        except ValueError:
            break
    race_results_ergast_dfs = pd.concat(temp_df, ignore_index=True)

    seasons_ergast = ergast.get_seasons(constructor=team_ergast_id, limit=1000)
    seasons_ergast = list(seasons_ergast["season"])

    pole_positions_ergast = ergast.get_race_results(constructor=team_ergast_id, grid_position=1, limit=1)

    team_name = ""

    # grand prix entered
    race_results_gp_ergast = ergast.get_race_results(constructor="haas", limit=1000)
    
    race_count = 0

    while True:
        race_count += len(race_results_gp_ergast.content)  # one dataframe per race
        try:
            race_results_gp_ergast = race_results_gp_ergast.get_next_result_page()
        except ValueError:
            break

    # career points, world championships
    team_points = 0.0
    championships = 0

    for year in seasons_ergast:
        standing = ergast.get_constructor_standings(
            season=year,
            constructor=team_ergast_id,
            limit=1
        )
        if standing.content: 
            points_col = standing.content[0].loc[0, "points"]

            team_points += points_col # career points

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

            if team_name == "":
                team_name = standing.content[0].loc[0, "constructorName"]

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


    return JsonResponse({
        "team": f"{team_name}",
        "grand_prix_entered": int(race_count),
        "team_points": float(team_points),
        "highest_race_finish": int(hrf_best_position),                    # e.g. 1
        "highest_race_finish_count": int(hrf_count),        # e.g. 105
        "podiums": int(podiums),
        "highest_grid_position": int(hgp_best_position),                # e.g. 1
        "highest_grid_position_count": int(hgp_count),    # e.g. 104
        "pole_positions": int(pole_positions),
        "world_championships": int(championships),
    })