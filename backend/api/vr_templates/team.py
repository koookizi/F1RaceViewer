from django.http import HttpResponseBadRequest, JsonResponse
import fastf1
import pandas as pd 
import json
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
from api.helpers.vr import (
    get_schedule,
    load_session,
    safe_event_name,
    safe_circuit_label,
    clean_laps,
    timedelta_to_seconds
)

def vr_tsp_1(season_year: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()

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

    for _, event in schedule.iterrows():
        round_number = int(event["RoundNumber"])

        if round_number <= 0:
            continue

        try:
            session = fastf1.get_session(season_year, round_number, session_type)
            session.load(laps=False, telemetry=False, weather=False, messages=False)
        except Exception:
            continue 

        results = session.results
        if results is None or results.empty:
            continue

        if "TeamName" not in results.columns or "Points" not in results.columns:
            continue

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

def vr_tsp_2(season_year: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"Failed to load schedule for {season_year} (missing/empty schedule or RoundNumber).")

    positions = []

    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        if rnd <= 0:
            continue

        try:
            session = load_session(season_year, rnd, session_type, laps=False)
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

        pos_col = "Position" if "Position" in team_res.columns else ("ClassifiedPosition" if "ClassifiedPosition" in team_res.columns else None)
        if pos_col is None:
            continue

        team_res[pos_col] = pd.to_numeric(team_res[pos_col], errors="coerce")
        team_res = team_res[team_res[pos_col].notna()]

        for _, r in team_res.iterrows():
            positions.append({
                "Round": rnd,
                "Event": safe_event_name(event),
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

def vr_tsp_3(season_year: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    exclude_nc = bool(inputs.get("exclude_non_classified", True))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"Failed to load schedule for {season_year}.")

    rows = []

    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        if rnd <= 0:
            continue

        try:
            session = load_session(season_year, rnd, session_type, laps=False)
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
                "Event": safe_event_name(event),
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

def vr_tca_1(season_from: int, season_to: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    min_races = int(inputs.get("min_races", 2))

    if season_from > season_to:
        season_from, season_to = season_to, season_from

    rows = []

    for year in range(season_from, season_to + 1):
        schedule = get_schedule(year)
        if schedule is None:
            continue

        for _, event in schedule.iterrows():
            rnd = int(event["RoundNumber"])
            if rnd <= 0:
                continue

            try:
                session = load_session(year, rnd, session_type, laps=False)
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
                "Circuit": safe_circuit_label(event),
                "Event": safe_event_name(event),
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

def vr_tca_2(season_from: int, season_to: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    min_races = int(inputs.get("min_races", 2))
    top_n = int(inputs.get("top_n", 5))

    if season_from > season_to:
        season_from, season_to = season_to, season_from

    rows = []
    for year in range(season_from, season_to + 1):
        schedule = get_schedule(year)
        if schedule is None:
            continue

        for _, event in schedule.iterrows():
            rnd = int(event["RoundNumber"])
            if rnd <= 0:
                continue
            try:
                session = load_session(year, rnd, session_type, laps=False)
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
                "Circuit": safe_circuit_label(event),
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

def vr_tca_3(season_from: int, season_to: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    min_races = int(inputs.get("min_races", 1))

    if season_from > season_to:
        season_from, season_to = season_to, season_from

    rows = []

    for year in range(season_from, season_to + 1):
        schedule = get_schedule(year)
        if schedule is None:
            continue

        for _, event in schedule.iterrows():
            rnd = int(event["RoundNumber"])
            if rnd <= 0:
                continue

            try:
                session = load_session(year, rnd, session_type, laps=False)
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
                "Circuit": safe_circuit_label(event),
                "Points": float(points),
            })

    if not rows:
        return HttpResponseBadRequest(f"No circuit/season points found for team='{team_name}' in {season_from}-{season_to}.")

    df = pd.DataFrame(rows)

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

def vr_tpc_1(season_year: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    exclude_pit = bool(inputs.get("exclude_pit_laps", True))
    exclude_sc = bool(inputs.get("exclude_sc_vsc", True))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"Failed to load schedule for {season_year}.")

    rows = []

    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        if rnd <= 0:
            continue

        try:
            session = load_session(season_year, rnd, session_type, laps=True)
        except Exception:
            continue

        laps = session.laps
        if laps is None or laps.empty:
            continue

        laps = clean_laps(laps, exclude_pit=exclude_pit, exclude_sc=exclude_sc)
        if laps.empty:
            continue

        laps = laps.copy()
        laps["LapTimeSeconds"] = timedelta_to_seconds(laps["LapTime"])
        laps = laps[laps["LapTimeSeconds"].notna()]

        if laps.empty:
            continue

        field_median = float(laps["LapTimeSeconds"].median())

        if "Team" in laps.columns:
            team_laps = laps[laps["Team"] == team_name].copy()
        elif "TeamName" in laps.columns:
            team_laps = laps[laps["TeamName"] == team_name].copy()
        else:
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

        team_laps["DeltaToFieldMedian"] = team_laps["LapTimeSeconds"] - field_median

        for _, r in team_laps.iterrows():
            rows.append({
                "Round": rnd,
                "Event": safe_event_name(event),
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

def vr_tpc_2(season_year: int, team_name: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    min_stint_laps = int(inputs.get("min_stint_laps", 6))
    exclude_pit = bool(inputs.get("exclude_pit_laps", True))
    exclude_sc = bool(inputs.get("exclude_sc_vsc", True))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"Failed to load schedule for {season_year}.")

    all_rows = []

    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        if rnd <= 0:
            continue

        try:
            session = load_session(season_year, rnd, session_type, laps=True)
        except Exception:
            continue

        laps = session.laps
        if laps is None or laps.empty:
            continue

        laps = clean_laps(laps, exclude_pit=exclude_pit, exclude_sc=exclude_sc)
        if laps.empty:
            continue

        if "Team" not in laps.columns or "Compound" not in laps.columns or "Stint" not in laps.columns:
            continue

        team_laps = laps[laps["Team"] == team_name].copy()
        if team_laps.empty:
            continue

        team_laps["LapTimeSeconds"] = timedelta_to_seconds(team_laps["LapTime"])
        team_laps = team_laps[team_laps["LapTimeSeconds"].notna()]
        if team_laps.empty:
            continue

        if "Driver" not in team_laps.columns or "LapNumber" not in team_laps.columns:
            continue

        team_laps = team_laps.sort_values(["Driver", "Stint", "LapNumber"])
        team_laps["LapInStint"] = team_laps.groupby(["Driver", "Stint"]).cumcount() + 1

        stint_sizes = team_laps.groupby(["Driver", "Stint"]).size().rename("StintSize").reset_index()
        team_laps = team_laps.merge(stint_sizes, on=["Driver", "Stint"], how="left")
        team_laps = team_laps[team_laps["StintSize"] >= min_stint_laps]

        if team_laps.empty:
            continue

        team_laps["Round"] = rnd
        team_laps["Event"] = safe_event_name(event)

        all_rows.append(team_laps[["Compound", "LapInStint", "LapTimeSeconds"]])

    if not all_rows:
        return HttpResponseBadRequest(f"No stint/compound lap data found for team='{team_name}' in {season_year}.")

    df = pd.concat(all_rows, ignore_index=True)

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