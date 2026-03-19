from django.http import HttpResponseBadRequest, JsonResponse
import pandas as pd 
import json
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
from api.helpers.vr import (
    get_schedule,
    load_session,
    find_driver_row,
    event_name,
    find_teammate_code,
    clean_laps,
    timedelta_to_seconds
)

def vr_dsp_1(season_year: int, driver_code: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    cumulative = bool(inputs.get("cumulative", False))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"No schedule found for {season_year} (or missing RoundNumber).")

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

        drow = find_driver_row(results, driver_code)
        if drow is None:
            continue

        if "Points" not in results.columns:
            continue

        points = pd.to_numeric(drow.get("Points"), errors="coerce")
        points = float(0 if pd.isna(points) else points)

        rows.append({"Round": rnd, "Event": event_name(event), "Points": points})

    if not rows:
        return HttpResponseBadRequest(f"No points found for driver='{driver_code}' in {season_year}.")

    df = pd.DataFrame(rows).sort_values("Round")
    if cumulative:
        df["Points"] = df["Points"].cumsum()

    fig = px.line(
        df,
        x="Round",
        y="Points",
        markers=True,
        title=f"{season_year} — {driver_code} points per round" + (" (cumulative)" if cumulative else ""),
        labels={"Round": "Round", "Points": "Points"},
        hover_data=["Event", "Points"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40), legend_title_text="")

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t32",
        "title": "Driver points per race (season trend)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "driver": driver_code, "session_type": session_type, "cumulative": cumulative, "source": "fastf1"},
    }
    return JsonResponse(payload)


def vr_dsp_2(season_year: int, driver_code: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    exclude_nc = bool(inputs.get("exclude_non_classified", True))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"No schedule found for {season_year}.")

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

        drow = find_driver_row(results, driver_code)
        if drow is None:
            continue

        if exclude_nc and "Status" in results.columns:
            status = str(drow.get("Status", ""))
            if any(x in status.upper() for x in ["DNF", "DNS", "DSQ", "NC"]):
                continue

        pos_col = "Position" if "Position" in results.columns else ("ClassifiedPosition" if "ClassifiedPosition" in results.columns else None)
        if pos_col is None:
            continue

        pos = pd.to_numeric(drow.get(pos_col), errors="coerce")
        if pd.isna(pos):
            continue

        rows.append({"Round": rnd, "Event": event_name(event), "Position": int(pos)})

    if not rows:
        return HttpResponseBadRequest(f"No finishing positions found for driver='{driver_code}' in {season_year}.")

    df = pd.DataFrame(rows)

    fig = px.box(
        df,
        y="Position",
        points="all",
        title=f"{season_year} — {driver_code} finish position distribution",
        labels={"Position": "Finish position"},
        hover_data=["Round", "Event", "Position"],
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40))

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t33",
        "title": "Finish position distribution (consistency boxplot)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "driver": driver_code, "session_type": session_type, "exclude_non_classified": exclude_nc, "source": "fastf1"},
    }
    return JsonResponse(payload)


def vr_dsp_3(season_year: int, driver_code: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    exclude_nc = bool(inputs.get("exclude_non_classified", True))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"No schedule found for {season_year}.")

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

        drow = find_driver_row(results, driver_code)
        if drow is None:
            continue

        if exclude_nc and "Status" in results.columns:
            status = str(drow.get("Status", ""))
            if any(x in status.upper() for x in ["DNF", "DNS", "DSQ", "NC"]):
                continue

        grid_col = "GridPosition" if "GridPosition" in results.columns else ("Grid" if "Grid" in results.columns else None)
        pos_col = "Position" if "Position" in results.columns else ("ClassifiedPosition" if "ClassifiedPosition" in results.columns else None)
        if grid_col is None or pos_col is None:
            continue

        grid = pd.to_numeric(drow.get(grid_col), errors="coerce")
        pos = pd.to_numeric(drow.get(pos_col), errors="coerce")
        if pd.isna(grid) or pd.isna(pos):
            continue

        gained = int(grid) - int(pos)

        rows.append({"Round": rnd, "Event": event_name(event), "PositionsGained": gained})

    if not rows:
        return HttpResponseBadRequest(f"No grid/finish deltas found for driver='{driver_code}' in {season_year}.")

    df = pd.DataFrame(rows)

    fig = px.histogram(
        df,
        x="PositionsGained",
        nbins=min(25, max(5, int(df["PositionsGained"].nunique()))),
        title=f"{season_year} — {driver_code} positions gained (grid → finish)",
        labels={"PositionsGained": "Positions gained (grid - finish)"},
        hover_data=["Round", "Event", "PositionsGained"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40))

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t34",
        "title": "Positions gained histogram (race execution)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "driver": driver_code, "session_type": session_type, "exclude_non_classified": exclude_nc, "source": "fastf1"},
    }
    return JsonResponse(payload)


def vr_dvt_1(season_year: int, driver_code: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"No schedule found for {season_year}.")

    rows = []
    teammate_code = None

    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        if rnd <= 0:
            continue

        try:
            session = load_session(season_year, rnd, session_type, laps=False)
        except Exception:
            continue

        results = session.results
        if results is None or results.empty or "Points" not in results.columns:
            continue

        drow = find_driver_row(results, driver_code)
        if drow is None:
            continue

        # set teammate once we can infer it from results
        if teammate_code is None:
            teammate_code = find_teammate_code(results, driver_code)

        # driver points
        dp = pd.to_numeric(drow.get("Points"), errors="coerce")
        dp = float(0 if pd.isna(dp) else dp)

        # teammate points (same round, if we can identify teammate)
        tp = None
        if teammate_code is not None:
            trow = find_driver_row(results, teammate_code)
            if trow is not None:
                tp_val = pd.to_numeric(trow.get("Points"), errors="coerce")
                tp = float(0 if pd.isna(tp_val) else tp_val)

        rows.append({"Round": rnd, "Event": event_name(event), "Driver": driver_code, "Points": dp})
        if teammate_code is not None and tp is not None:
            rows.append({"Round": rnd, "Event": event_name(event), "Driver": teammate_code, "Points": tp})

    if not rows:
        return HttpResponseBadRequest(f"No points found for driver='{driver_code}' in {season_year}.")

    df = pd.DataFrame(rows)

    if teammate_code is None:
        return HttpResponseBadRequest(
            f"Could not infer teammate for driver='{driver_code}' in {season_year} (TeamName missing or driver not present)."
        )

    totals = df.groupby("Driver", as_index=False)["Points"].sum()

    fig = px.bar(
        totals,
        x="Driver",
        y="Points",
        title=f"{season_year} — points comparison: {driver_code} vs {teammate_code}",
        labels={"Driver": "Driver", "Points": "Total points"},
        hover_data=["Driver", "Points"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40))

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t35",
        "title": "Points vs teammate (season comparison)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "driver": driver_code, "teammate": teammate_code, "session_type": session_type, "source": "fastf1"},
    }
    return JsonResponse(payload)


def vr_dvt_2(season_year: int, driver_code: str, inputs: dict):
    # Qualifying session for head-to-head
    session_type = (inputs.get("session_type") or "Q").upper()
    include_sprint_sessions = bool(inputs.get("include_sprint_sessions", False))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"No schedule found for {season_year}.")

    rows = []
    teammate_code = None

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

        drow = find_driver_row(results, driver_code)
        if drow is None:
            continue

        if teammate_code is None:
            teammate_code = find_teammate_code(results, driver_code)
        if teammate_code is None:
            continue

        trow = find_driver_row(results, teammate_code)
        if trow is None:
            continue

        pos_col = "Position" if "Position" in results.columns else ("ClassifiedPosition" if "ClassifiedPosition" in results.columns else None)
        if pos_col is None:
            continue

        dpos = pd.to_numeric(drow.get(pos_col), errors="coerce")
        tpos = pd.to_numeric(trow.get(pos_col), errors="coerce")
        if pd.isna(dpos) or pd.isna(tpos):
            continue

        winner = driver_code if int(dpos) < int(tpos) else teammate_code

        rows.append({
            "Round": rnd,
            "Event": event_name(event),
            "Winner": winner,
        })

    if teammate_code is None:
        return HttpResponseBadRequest(f"Could not infer teammate for driver='{driver_code}' in {season_year} using session_type='{session_type}'.")

    if not rows:
        return HttpResponseBadRequest(f"No qualifying head-to-head data for driver='{driver_code}' in {season_year}.")

    df = pd.DataFrame(rows)
    counts = df["Winner"].value_counts().reset_index()
    counts.columns = ["Driver", "H2HWins"]

    fig = px.bar(
        counts,
        x="Driver",
        y="H2HWins",
        title=f"{season_year} — qualifying head-to-head wins: {driver_code} vs {teammate_code}",
        labels={"Driver": "Driver", "H2HWins": "Sessions won"},
        hover_data=["Driver", "H2HWins"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40))

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t36",
        "title": "Qualifying head-to-head vs teammate",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "driver": driver_code, "teammate": teammate_code, "session_type": session_type, "source": "fastf1"},
    }
    return JsonResponse(payload)


def vr_dvt_3(season_year: int, driver_code: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    exclude_pit = bool(inputs.get("exclude_pit_laps", True))
    exclude_sc = bool(inputs.get("exclude_sc_vsc", True))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"No schedule found for {season_year}.")

    rows = []
    teammate_code = None

    for _, event in schedule.iterrows():
        rnd = int(event["RoundNumber"])
        if rnd <= 0:
            continue

        try:
            session = load_session(season_year, rnd, session_type, laps=True)
        except Exception:
            continue

        # get teammate from results for this event
        results = session.results
        if teammate_code is None and results is not None and not results.empty:
            teammate_code = find_teammate_code(results, driver_code)

        if teammate_code is None:
            continue

        laps = session.laps
        if laps is None or laps.empty:
            continue

        laps = clean_laps(laps, exclude_pit=exclude_pit, exclude_sc=exclude_sc)
        if laps.empty:
            continue

        if "Driver" not in laps.columns:
            continue

        d_laps = laps[laps["Driver"] == driver_code].copy()
        t_laps = laps[laps["Driver"] == teammate_code].copy()
        if d_laps.empty or t_laps.empty:
            continue

        d_laps["LapTimeSeconds"] = timedelta_to_seconds(d_laps["LapTime"])
        t_laps["LapTimeSeconds"] = timedelta_to_seconds(t_laps["LapTime"])
        d_laps = d_laps[d_laps["LapTimeSeconds"].notna()]
        t_laps = t_laps[t_laps["LapTimeSeconds"].notna()]
        if d_laps.empty or t_laps.empty:
            continue

        # median pace per race
        d_med = float(d_laps["LapTimeSeconds"].median())
        t_med = float(t_laps["LapTimeSeconds"].median())
        delta = d_med - t_med  # positive means that driver slower than teammate

        rows.append({
            "Round": rnd,
            "Event": event_name(event),
            "DeltaToTeammateMedian": delta,
        })

    if teammate_code is None:
        return HttpResponseBadRequest(f"Could not infer teammate for driver='{driver_code}' in {season_year}.")

    if not rows:
        return HttpResponseBadRequest(f"No pace delta data found for {driver_code} vs teammate in {season_year}.")

    df = pd.DataFrame(rows)

    fig = px.box(
        df,
        y="DeltaToTeammateMedian",
        points="all",
        title=f"{season_year} — {driver_code} median race pace delta vs {teammate_code}",
        labels={"DeltaToTeammateMedian": "Median lap delta to teammate (s)"},
        hover_data=["Round", "Event", "DeltaToTeammateMedian"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40))

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t37",
        "title": "Race pace delta vs teammate (boxplot)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {
            "season": season_year,
            "driver": driver_code,
            "teammate": teammate_code,
            "session_type": session_type,
            "exclude_pit_laps": exclude_pit,
            "exclude_sc_vsc": exclude_sc,
            "source": "fastf1",
        },
    }
    return JsonResponse(payload)

def vr_dc_1(season_year: int, driver_code: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    min_stint_laps = int(inputs.get("min_stint_laps", 6))
    exclude_pit = bool(inputs.get("exclude_pit_laps", True))
    exclude_sc = bool(inputs.get("exclude_sc_vsc", True))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"No schedule found for {season_year}.")

    all_chunks = []

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

        required = {"Driver", "LapNumber", "LapTime", "Compound", "Stint"}
        if not required.issubset(set(laps.columns)):
            continue

        d_laps = laps[laps["Driver"] == driver_code].copy()
        if d_laps.empty:
            continue

        d_laps["LapTimeSeconds"] = timedelta_to_seconds(d_laps["LapTime"])
        d_laps = d_laps[d_laps["LapTimeSeconds"].notna()]
        if d_laps.empty:
            continue

        d_laps = d_laps.sort_values(["Stint", "LapNumber"])
        d_laps["LapInStint"] = d_laps.groupby(["Stint"]).cumcount() + 1

        # filter short stints
        stint_sizes = d_laps.groupby("Stint").size().rename("StintSize").reset_index()
        d_laps = d_laps.merge(stint_sizes, on="Stint", how="left")
        d_laps = d_laps[d_laps["StintSize"] >= min_stint_laps]
        if d_laps.empty:
            continue

        all_chunks.append(d_laps[["Compound", "LapInStint", "LapTimeSeconds"]])

    if not all_chunks:
        return HttpResponseBadRequest(f"No stint/compound lap data found for driver='{driver_code}' in {season_year}.")

    df = pd.concat(all_chunks, ignore_index=True)

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
        title=f"{season_year} — {driver_code} tyre degradation profile (season aggregate)",
        labels={"LapInStint": "Lap in stint", "MedianLapTime": "Median lap time (s)"},
        hover_data=["Compound", "LapInStint", "MedianLapTime", "N"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40), legend_title_text="Compound")

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t38",
        "title": "Tyre degradation profile (season aggregate)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {
            "season": season_year,
            "driver": driver_code,
            "session_type": session_type,
            "min_stint_laps": min_stint_laps,
            "exclude_pit_laps": exclude_pit,
            "exclude_sc_vsc": exclude_sc,
            "source": "fastf1",
        },
    }
    return JsonResponse(payload)


def vr_dc_2(season_year: int, driver_code: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    exclude_pit = bool(inputs.get("exclude_pit_laps", True))
    exclude_sc = bool(inputs.get("exclude_sc_vsc", True))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"No schedule found for {season_year}.")

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
        if laps.empty or "Driver" not in laps.columns:
            continue

        d_laps = laps[laps["Driver"] == driver_code].copy()
        if d_laps.empty:
            continue

        d_laps["LapTimeSeconds"] = timedelta_to_seconds(d_laps["LapTime"])
        d_laps = d_laps[d_laps["LapTimeSeconds"].notna()]
        if d_laps.empty:
            continue

        for v in d_laps["LapTimeSeconds"].values:
            rows.append({"Round": rnd, "Event": event_name(event), "LapTimeSeconds": float(v)})

    if not rows:
        return HttpResponseBadRequest(f"No clean lap times found for driver='{driver_code}' in {season_year}.")

    df = pd.DataFrame(rows)

    fig = px.box(
        df,
        y="LapTimeSeconds",
        points="outliers",
        title=f"{season_year} — {driver_code} lap-time consistency distribution (clean laps)",
        labels={"LapTimeSeconds": "Lap time (s)"},
        hover_data=["Round", "Event", "LapTimeSeconds"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40))

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t39",
        "title": "Lap-time consistency distribution (season)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "driver": driver_code, "session_type": session_type, "exclude_pit_laps": exclude_pit, "exclude_sc_vsc": exclude_sc, "source": "fastf1"},
    }
    return JsonResponse(payload)


def vr_dc_3(season_year: int, driver_code: str, inputs: dict):
    session_type = (inputs.get("session_type") or "R").upper()
    exclude_nc = bool(inputs.get("exclude_non_classified", True))

    schedule = get_schedule(season_year)
    if schedule is None:
        return HttpResponseBadRequest(f"No schedule found for {season_year}.")

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

        drow = find_driver_row(results, driver_code)
        if drow is None:
            continue

        if exclude_nc and "Status" in results.columns:
            status = str(drow.get("Status", ""))
            if any(x in status.upper() for x in ["DNF", "DNS", "DSQ", "NC"]):
                continue

        grid_col = "GridPosition" if "GridPosition" in results.columns else ("Grid" if "Grid" in results.columns else None)
        pos_col = "Position" if "Position" in results.columns else ("ClassifiedPosition" if "ClassifiedPosition" in results.columns else None)
        if grid_col is None or pos_col is None:
            continue

        grid = pd.to_numeric(drow.get(grid_col), errors="coerce")
        pos = pd.to_numeric(drow.get(pos_col), errors="coerce")
        if pd.isna(grid) or pd.isna(pos):
            continue

        gained = int(grid) - int(pos)

        rows.append({"Round": rnd, "Event": event_name(event), "PositionsGained": gained})

    if not rows:
        return HttpResponseBadRequest(f"No positions gained per round found for driver='{driver_code}' in {season_year}.")

    df = pd.DataFrame(rows).sort_values("Round")

    fig = px.bar(
        df,
        x="Round",
        y="PositionsGained",
        title=f"{season_year} — {driver_code} positions gained per race",
        labels={"Round": "Round", "PositionsGained": "Positions gained (grid - finish)"},
        hover_data=["Event", "PositionsGained"],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=60, b=40))

    figure_dict = json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))
    payload = {
        "id": "t40",
        "title": "Race start and recovery (positions gained analysis)",
        "result": {"type": "plotly", "figure": figure_dict},
        "meta": {"season": season_year, "driver": driver_code, "session_type": session_type, "exclude_non_classified": exclude_nc, "source": "fastf1"},
    }
    return JsonResponse(payload)