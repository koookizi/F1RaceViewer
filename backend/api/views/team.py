from django.http import JsonResponse
from api.models import Result, Team, TeamStanding
from django.db.models import Sum, Min
from django.db.models.functions import Coalesce

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