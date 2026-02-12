from django.http import HttpResponseBadRequest, JsonResponse
import fastf1
from fastf1.ergast import Ergast
import pandas as pd 
import json
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import plotly.graph_objects as go
from api.helpers.vr import (
    parse_bool
)

# -	Driver laptimes (scatterplot)
def vr_pace_1(year, country, session_name, inputs):
    drivers = inputs.get("drivers", [])
    exclude_sc = parse_bool(inputs.get("excludeSCVSC", False))

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
    exclude_sc = parse_bool(inputs.get("excludeSCVSC", False))
    show_points = parse_bool(inputs.get("showPoints", True))

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
    exclude_sc = parse_bool(inputs.get("excludeSCVSC", False))

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
    exclude_sc = parse_bool(inputs.get("excludeSCVSC", False))

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