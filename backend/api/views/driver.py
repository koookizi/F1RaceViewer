from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from api.models import Driver, DriverStanding, Result
from fastf1.ergast import Ergast
from django.db.models import Sum, Min
from django.db.models.functions import Coalesce

__all__ = [
    "drivers_getDrivers",
    "driver_getDriverCode",
    "driver_getDriverSummary"
]

def drivers_getDrivers(request):
    drivers = (
        Driver.objects
        .order_by("ergast_id")
        .values("ergast_id", "given_name", "family_name")
        .distinct()
    )

    return JsonResponse({"drivers": list(drivers)})

def driver_getDriverCode(request, driver_ergast_id: str):
    ergast = Ergast()
    df = ergast.get_driver_info(driver=driver_ergast_id)
    abbr = df.loc[0, "driverCode"]
    return JsonResponse({"driverCode": abbr})
    

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

    # Pole positions
    pole_positions = race_qs.filter(grid=1).count()

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