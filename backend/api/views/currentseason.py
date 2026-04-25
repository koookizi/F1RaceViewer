from django.http import JsonResponse
from django.core.cache import cache
import pandas as pd 
import json
from datetime import datetime
from urllib.request import urlopen
from datetime import timezone
from urllib.error import HTTPError
from urllib.parse import urlencode

__all__ = [
    "getCurrentSeason",
]

def getCurrentSeason(request, data, teamOrDriver=None):
    """
    Returns current-season summary data for a selected team or driver.

    Logic:
    - Load sessions from the current and previous calendar year.
    - Identify the latest season that has at least one started race.
    - For championship standings, walk backwards through completed race sessions
      until OpenF1 returns actual championship data.
    - Aggregate race, sprint and grid data across that selected season.
    """

    def openf1_cache_timeout(url):
        if "/sessions?" in url:
            return 60 * 60 * 6
        if "/drivers?" in url:
            return 60 * 60 * 24
        if "/championship_" in url:
            return 60 * 30
        return 60 * 15

    def openf1_json(url):
        cache_key = f"openf1:{url}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            req = urlopen(url)
            data = json.loads(req.read().decode("utf-8"))
        except HTTPError as e:
            try:
                body = e.read().decode("utf-8")
                data = json.loads(body)
            except Exception:
                data = {"detail": f"HTTP {e.code}"}

        is_rate_limited = isinstance(data, dict) and data.get("error") == "Too Many Requests"
        if not is_rate_limited:
            cache.set(cache_key, data, timeout=openf1_cache_timeout(url))

        return data

    response_cache_key = f"currentseason:{teamOrDriver}:{data}"
    cached_response = cache.get(response_cache_key)
    if cached_response is not None:
        return JsonResponse(cached_response, safe=False)

    now = datetime.now(timezone.utc)
    year_now = now.year

    # Load sessions from current and previous year
    sessions = []
    for y in (year_now - 1, year_now):
        raw_sessions = openf1_json(f"https://api.openf1.org/v1/sessions?year={y}")
        if isinstance(raw_sessions, list):
            sessions.extend(raw_sessions)

    if not sessions:
        return JsonResponse({"error": "No session data available"}, status=503)

    session_df = pd.DataFrame(sessions)

    if session_df.empty:
        return JsonResponse({"error": "No session data available"}, status=503)

    session_df["date_start"] = pd.to_datetime(session_df["date_start"], utc=True)
    session_df["date_end"] = pd.to_datetime(session_df["date_end"], utc=True)

    # Keep only sessions we care about for seasonal summaries
    session_df = session_df[
        session_df["session_name"].isin(["Qualifying", "Sprint", "Race"])
    ].copy()

    if session_df.empty:
        return JsonResponse(
            {"error": "No qualifying, sprint, or race sessions found"},
            status=503
        )

    # Find seasons that already have at least one started race
    started_races = session_df[
        (session_df["session_name"] == "Race") &
        (session_df["date_start"] <= now)
    ].copy()

    if started_races.empty:
        return JsonResponse({"error": "No started race sessions found yet"}, status=404)

    latest_year = int(started_races["year"].max())

    # Restrict to the selected season
    df = session_df[session_df["year"] == latest_year].copy()
    df = df.sort_values("date_start").reset_index(drop=True)

    # Session keys for seasonal aggregation
    race_session_keys = df.loc[df["session_name"] == "Race", "session_key"].astype(int).tolist()
    sprint_session_keys = df.loc[df["session_name"] == "Sprint", "session_key"].astype(int).tolist()
    qualifying_session_keys = df.loc[df["session_name"] == "Qualifying", "session_key"].astype(int).tolist()

    # Candidate race sessions for standings lookup:
    # latest completed race first, then walk backwards until OpenF1 returns data
    candidate_races = (
        df[(df["session_name"] == "Race") & (df["date_end"] <= now)]
        .sort_values("date_start", ascending=False)
        .reset_index(drop=True)
    )

    if candidate_races.empty:
        return JsonResponse(
            {"error": f"No completed race sessions found for season {latest_year}"},
            status=404
        )

    standings_session_key = None
    last_championship_df = pd.DataFrame()

    if teamOrDriver == "team":
        for _, race_row in candidate_races.iterrows():
            candidate_session_key = int(race_row["session_key"])
            raw = openf1_json(
                f"https://api.openf1.org/v1/championship_teams?session_key={candidate_session_key}"
            )

            print("trying team championship session_key:", candidate_session_key)
            print("raw response:", raw)

            if isinstance(raw, dict) and raw.get("error") == "Too Many Requests":
                return JsonResponse(
                    {"error": f"API - Rate Limit Hit (429). Please retry shortly."},
                    status=429
                )

            if isinstance(raw, dict) and raw.get("detail") == "No results found.":
                continue


            if not isinstance(raw, list) or len(raw) == 0:
                continue

            candidate_championship_df = pd.DataFrame(raw)

            if not candidate_championship_df.empty:
                standings_session_key = candidate_session_key
                last_championship_df = candidate_championship_df
                break

        if standings_session_key is None:
            return JsonResponse({"error": "No championship team data available"}, status=404)

        print("selected standings_session_key:", standings_session_key)

        matching_team = last_championship_df[last_championship_df["team_name"] == data]
        if matching_team.empty:
            print("matching team is empty")
            return JsonResponse(
                {"error": f"Team '{data}' not found in season {latest_year} championship data"},
                status=404,
            )

        drivers_query = urlencode({
            "team_name": data,
            "session_key": standings_session_key,
        })
        drivers_raw = openf1_json(f"https://api.openf1.org/v1/drivers?{drivers_query}")
        drivers_df = pd.DataFrame(drivers_raw if isinstance(drivers_raw, list) else [])

        if isinstance(drivers_raw, dict) and drivers_raw.get("error") == "Too Many Requests":
            return JsonResponse(
                {"error": f"API - Rate Limit Hit (429). Please retry shortly."},
                status=429
            )

        if drivers_df.empty:
            return JsonResponse(
                {"error": f"No drivers found for team '{data}' in season {latest_year}"},
                status=404,
            )
        
        drivers_df = drivers_df.drop_duplicates(subset=["driver_number"]).reset_index(drop=True)

        driver_numbers = drivers_df["driver_number"].dropna().astype(int).tolist()

        drivers_df = drivers_df.drop(
            columns=["broadcast_name", "meeting_key", "session_key"],
            errors="ignore"
        )
        drivers_json = drivers_df.to_dict(orient="records")
        last_championship_df = matching_team

    elif teamOrDriver == "driver":
        for _, race_row in candidate_races.iterrows():
            candidate_session_key = int(race_row["session_key"])
            raw = openf1_json(
                f"https://api.openf1.org/v1/championship_drivers?session_key={candidate_session_key}"
            )

            print("trying driver championship session_key:", candidate_session_key)
            print("raw response:", raw)

            if isinstance(raw, dict) and raw.get("error") == "Too Many Requests":
                return JsonResponse(
                    {"error": f"API - Rate Limit Hit (429). Please retry shortly."},
                    status=429
                )

            if isinstance(raw, dict) and raw.get("detail") == "No results found.":
                continue

            if not isinstance(raw, list) or len(raw) == 0:
                continue

            candidate_championship_df = pd.DataFrame(raw)

            if not candidate_championship_df.empty:
                standings_session_key = candidate_session_key
                last_championship_df = candidate_championship_df
                break

        if standings_session_key is None:
            return JsonResponse({"error": "No championship driver data available"}, status=404)

        print("selected standings_session_key:", standings_session_key)

        parts = data.split(" ", 1)
        if len(parts) != 2:
            return JsonResponse(
                {"error": "Driver name must be in 'First Last' format"},
                status=400,
            )

        first_name, last_name = parts

        print(parts)

        drivers_query = urlencode({
            "first_name": first_name,
            "last_name": last_name,
            "session_key": standings_session_key,
        })
        drivers_raw = openf1_json(f"https://api.openf1.org/v1/drivers?{drivers_query}")
        drivers_df = pd.DataFrame(drivers_raw if isinstance(drivers_raw, list) else [])

        if isinstance(drivers_raw, dict) and drivers_raw.get("error") == "Too Many Requests":
            return JsonResponse(
                {"error": f"API - Rate Limit Hit (429). Please retry shortly."},
                status=429
            )


        if drivers_df.empty:
            return JsonResponse(
                {"error": f"Driver '{data}' not found in season {latest_year}"},
                status=404,
            )
        
        drivers_df = drivers_df.drop_duplicates(subset=["driver_number"]).reset_index(drop=True)

        driver_numbers = drivers_df["driver_number"].dropna().astype(int).tolist()
        if not driver_numbers:
            return JsonResponse(
                {"error": f"No driver number found for '{data}'"},
                status=404,
            )

        drivers_df = drivers_df.drop(
            columns=["broadcast_name", "meeting_key", "session_key"],
            errors="ignore"
        )
        drivers_json = drivers_df.to_dict(orient="records")

        last_championship_df = last_championship_df[
            last_championship_df["driver_number"] == driver_numbers[0]
        ]

    else:
        return JsonResponse({"error": "teamOrDriver must be 'team' or 'driver'"}, status=400)

    if not driver_numbers:
        return JsonResponse({"error": "No driver numbers available"}, status=404)

    driver_numbers_query = "&".join(f"driver_number={n}" for n in driver_numbers)

    # Race + sprint results
    all_result_keys = sprint_session_keys + race_session_keys
    if all_result_keys:
        all_results_query = "&".join(f"session_key={k}" for k in all_result_keys)
        all_results_raw = openf1_json(
            f"https://api.openf1.org/v1/session_result?{all_results_query}&{driver_numbers_query}"
        )
        all_results_df = pd.DataFrame(all_results_raw if isinstance(all_results_raw, list) else [])
    else:
        all_results_df = pd.DataFrame()

    sprint_results_df = (
        all_results_df[all_results_df["session_key"].isin(sprint_session_keys)]
        if not all_results_df.empty else pd.DataFrame()
    )

    grand_prix_results_df = (
        all_results_df[all_results_df["session_key"].isin(race_session_keys)]
        if not all_results_df.empty else pd.DataFrame()
    )

    # Starting grid from qualifying sessions
    if qualifying_session_keys:
        grid_query = "&".join(f"session_key={k}" for k in qualifying_session_keys)
        grid_results_raw = openf1_json(
            f"https://api.openf1.org/v1/starting_grid?{grid_query}&{driver_numbers_query}"
        )
        if isinstance(grid_results_raw, dict) and grid_results_raw.get("error") == "Too Many Requests":
                return JsonResponse(
                    {"error": f"API - Rate Limit Hit (429). Please retry shortly."},
                    status=429
                )
        grid_results_df = pd.DataFrame(grid_results_raw if isinstance(grid_results_raw, list) else [])
    else:
        grid_results_df = pd.DataFrame()

    season_position = int(last_championship_df["position_current"].iloc[0]) if not last_championship_df.empty else 0
    season_points = float(last_championship_df["points_current"].iloc[0]) if not last_championship_df.empty else 0.0

    gp_races = len(race_session_keys)
    gp_points = float(grand_prix_results_df["points"].sum()) if not grand_prix_results_df.empty else 0.0
    gp_wins = int((grand_prix_results_df["position"] == 1).sum()) if not grand_prix_results_df.empty else 0
    gp_podiums = int((grand_prix_results_df["position"] <= 3).sum()) if not grand_prix_results_df.empty else 0
    gp_poles = int((grid_results_df["position"] == 1).sum()) if not grid_results_df.empty else 0
    gp_top10s = int((grand_prix_results_df["position"] <= 10).sum()) if not grand_prix_results_df.empty else 0
    gp_dnfs = int((grand_prix_results_df["dnf"] == True).sum()) if (not grand_prix_results_df.empty and "dnf" in grand_prix_results_df.columns) else 0

    sprint_races = len(sprint_session_keys)
    sprint_points = float(sprint_results_df["points"].sum()) if not sprint_results_df.empty else 0.0
    sprint_wins = int((sprint_results_df["position"] == 1).sum()) if not sprint_results_df.empty else 0
    sprint_podiums = int((sprint_results_df["position"] <= 3).sum()) if not sprint_results_df.empty else 0
    sprint_top10s = int((sprint_results_df["position"] <= 10).sum()) if not sprint_results_df.empty else 0

    print("standings_session_key:", standings_session_key)
    print("latest_year:", latest_year)
    print("requested data:", repr(data))
    if teamOrDriver == "team" and not last_championship_df.empty and "team_name" in last_championship_df.columns:
        print("championship teams returned:")
        print(last_championship_df[["team_name"]].drop_duplicates())

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
            "dnfs": gp_dnfs,
        },
        "sprint": {
            "races": sprint_races,
            "points": sprint_points,
            "wins": sprint_wins,
            "podiums": sprint_podiums,
            "top10s": sprint_top10s,
        },
        "drivers": drivers_json,
        "year": latest_year,
    }

    print("finalJSON:", finalJSON)

    cache.set(response_cache_key, finalJSON, timeout=60 * 10)

    return JsonResponse(finalJSON, safe=False)
