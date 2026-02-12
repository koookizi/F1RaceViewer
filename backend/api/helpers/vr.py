import fastf1
import pandas as pd 

def get_schedule(year: int):
    try:
        schedule = fastf1.get_event_schedule(year)
    except Exception:
        return None
    if schedule is None or schedule.empty or "RoundNumber" not in schedule.columns:
        return None
    return schedule


def event_name(event_row):
    return event_row.get("EventName", None) or event_row.get("OfficialEventName", None) or f"Round {int(event_row['RoundNumber'])}"


def load_session(year: int, round_number: int, session_type: str, laps: bool = False):
    session = fastf1.get_session(year, round_number, session_type)
    session.load(laps=laps, telemetry=False, weather=False, messages=False)
    return session


def timedelta_to_seconds(series: pd.Series) -> pd.Series:
    if pd.api.types.is_timedelta64_dtype(series):
        return series.dt.total_seconds()
    return pd.to_numeric(series, errors="coerce")


def clean_laps(laps: pd.DataFrame, exclude_pit: bool = True, exclude_sc: bool = True) -> pd.DataFrame:
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
        out = out[~out["TrackStatus"].astype(str).str.contains("4|5", regex=True)]
    return out


def find_driver_row(results: pd.DataFrame, driver_code: str):
    """Match by Abbreviation (e.g. HAM, VER). Returns Series or None."""
    if results is None or results.empty or "Abbreviation" not in results.columns:
        return None
    m = results["Abbreviation"] == driver_code
    if not m.any():
        return None
    return results.loc[m].iloc[0]


def find_teammate_code(results: pd.DataFrame, driver_code: str):
    """Teammate = other driver with same TeamName in results. Returns code or None."""
    if results is None or results.empty or "Abbreviation" not in results.columns or "TeamName" not in results.columns:
        return None
    drow = find_driver_row(results, driver_code)
    if drow is None:
        return None
    team = drow.get("TeamName")
    if pd.isna(team):
        return None
    same_team = results[results["TeamName"] == team]
    mates = same_team[same_team["Abbreviation"] != driver_code]["Abbreviation"].dropna().unique().tolist()
    return mates[0] if mates else None

def get_schedule(year: int):
    schedule = fastf1.get_event_schedule(year)
    if schedule is None or schedule.empty:
        return None
    if "RoundNumber" not in schedule.columns:
        return None
    return schedule


def safe_event_name(event_row):
    # EventName exists in recent FastF1, but keep defensive
    return event_row.get("EventName", None) or event_row.get("OfficialEventName", None) or f"Round {int(event_row['RoundNumber'])}"


def safe_circuit_label(event_row):
    # FastF1 schedule doesn't always expose circuit name directly.
    # Location is usually a good proxy (e.g., "Silverstone", "Monza").
    loc = event_row.get("Location", "") or ""
    country = event_row.get("Country", "") or ""
    if loc and country:
        return f"{loc} ({country})"
    return loc or country or safe_event_name(event_row)


def load_session(year: int, round_number: int, session_type: str, laps: bool = False):
    session = fastf1.get_session(year, round_number, session_type)
    session.load(laps=laps, telemetry=False, weather=False, messages=False)
    return session


def timedelta_to_seconds(series: pd.Series) -> pd.Series:
    if pd.api.types.is_timedelta64_dtype(series):
        return series.dt.total_seconds()
    return pd.to_numeric(series, errors="coerce")


def clean_laps(laps: pd.DataFrame, exclude_pit: bool = True, exclude_sc: bool = True) -> pd.DataFrame:
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

def parse_bool(s: str) -> bool:
    return str(s).lower() in ("1", "true", "yes", "on")

def parse_csv_param(request, name: str) -> list[str]:
    raw = request.GET.get(name, "")
    return [x.strip().upper() for x in raw.split(",") if x.strip()]