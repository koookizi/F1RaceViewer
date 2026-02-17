# app/management/commands/ingest_fastf1_core.py
# Usage:
#   python manage.py ingest_fastf1_core
#   python manage.py ingest_fastf1_core --from-year 2018 --to-year 2025
#
# What it ingests (using FastF1):
#   - Seasons (years)
#   - Circuits (Ergast circuitId, name, country)
#   - Events (season+round, country, circuit)
#   - Sessions (event, session_type) from FastF1 event schedule
#   - Teams (Ergast constructorId, name, nationality)
#   - Drivers (Ergast driverId, given_name, family_name, nationality)

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

import fastf1
from fastf1.ergast import Ergast

from api.models import Season, Circuit, Event, Session, Team, Driver  # adjust "app" to your Django app name


def _safe_str(x: Any) -> str:
    return "" if x is None else str(x).strip()


def _extract_ergast_rows(resp: Any) -> List[Dict[str, Any]]:
    """
    FastF1 Ergast responses have changed shape across versions.
    This helper tries a few common attributes and falls back to parsing dicts.
    Returns a list[dict] of rows (already flattened-ish).
    """
    # 1) Newer-ish: response.content exists and is already a list of dicts
    if hasattr(resp, "content"):
        content = getattr(resp, "content")
        if isinstance(content, list):
            return content

    # 2) Some versions: response.data or response.results
    for attr in ("data", "results"):
        if hasattr(resp, attr):
            val = getattr(resp, attr)
            if isinstance(val, list):
                return val

    # 3) Some versions expose a pandas DF
    for attr in ("dataframe", "df"):
        if hasattr(resp, attr):
            df = getattr(resp, attr)
            if isinstance(df, pd.DataFrame):
                return df.to_dict(orient="records")

    # 4) Fallback: try to interpret response as dict-like JSON
    if isinstance(resp, dict):
        # Try common Ergast JSON nesting
        mr = resp.get("MRData") or {}
        race_table = mr.get("RaceTable") or {}
        races = race_table.get("Races")
        if isinstance(races, list):
            return races

    raise TypeError(f"Unrecognized Ergast response shape: {type(resp)!r}")


def _extract_sessions_from_schedule_row(row: pd.Series) -> List[str]:
    """
    FastF1 get_event_schedule() typically contains columns Session1..Session5 (+ Date columns).
    We collect any "Session*" columns that are not date columns.
    """
    session_names: List[str] = []
    for col in row.index:
        c = str(col).lower()
        if not c.startswith("session"):
            continue
        if c.endswith("date") or c.endswith("_date"):
            continue
        val = row[col]
        if pd.isna(val):
            continue
        name = _safe_str(val)
        if not name:
            continue
        session_names.append(name)

    # De-duplicate while preserving order
    seen: Set[str] = set()
    out: List[str] = []
    for s in session_names:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


@dataclass
class IngestStats:
    seasons: int = 0
    circuits: int = 0
    events: int = 0
    sessions: int = 0
    teams: int = 0
    drivers: int = 0


class Command(BaseCommand):
    help = "Ingest Seasons/Circuits/Events/Sessions/Teams/Drivers using FastF1 (Ergast + schedule)."

    def add_arguments(self, parser):
        parser.add_argument("--from-year", type=int, default=1950)
        parser.add_argument("--to-year", type=int, default=datetime.utcnow().year)
        parser.add_argument("--skip-sessions", action="store_true", help="Skip ingesting Session rows")

    def handle(self, *args, **opts):
        from_year: int = opts["from_year"]
        to_year: int = opts["to_year"]
        skip_sessions: bool = bool(opts["skip_sessions"])

        if from_year > to_year:
            from_year, to_year = to_year, from_year

        # Optional but recommended: enable FastF1 cache to avoid re-downloading schedules repeatedly
        # (cache folder can be anywhere)
        fastf1.Cache.enable_cache("api/fastf1_cache")

        ergast = Ergast()
        stats = IngestStats()

        with transaction.atomic():
            stats.teams += self._ingest_teams(ergast)
            stats.drivers += self._ingest_drivers(ergast)

            for year in range(from_year, to_year + 1):
                stats.seasons += self._ingest_season(year)

                # Events + Circuits from Ergast schedule (authoritative IDs)
                created_circuits, created_events, event_rounds = self._ingest_events_and_circuits_for_year(
                    ergast, year
                )
                stats.circuits += created_circuits
                stats.events += created_events

                if not skip_sessions:
                    stats.sessions += self._ingest_sessions_for_year(year, event_rounds)

        self.stdout.write(self.style.SUCCESS("Done."))
        self.stdout.write(
            f"Created: Seasons {stats.seasons}, Circuits {stats.circuits}, Events {stats.events}, "
            f"Sessions {stats.sessions}, Teams {stats.teams}, Drivers {stats.drivers}"
        )

    def _ingest_season(self, year: int) -> int:
        _, created = Season.objects.get_or_create(year=year)
        return 1 if created else 0

    def _ingest_teams(self, ergast: Ergast) -> int:
        # One call, all constructors
        resp = ergast.get_constructor_info(limit=1000)
        rows = _extract_ergast_rows(resp)

        created_count = 0
        for r in rows:
            # Typical keys: constructorId, name, nationality
            constructor_id = _safe_str(r.get("constructorId") or r.get("constructor_id"))
            if not constructor_id:
                continue

            defaults = {
                "name": _safe_str(r.get("name")),
                "nationality": _safe_str(r.get("nationality")),
            }
            _, created = Team.objects.update_or_create(
                ergast_id=constructor_id,
                defaults=defaults,
            )
            if created:
                created_count += 1

        return created_count

    def _ingest_drivers(self, ergast: Ergast) -> int:
        # One call, all drivers
        resp = ergast.get_drivers(limit=5000)
        rows = _extract_ergast_rows(resp)

        created_count = 0
        for r in rows:
            # Typical keys: driverId, givenName, familyName, nationality
            driver_id = _safe_str(r.get("driverId") or r.get("driver_id"))
            if not driver_id:
                continue

            defaults = {
                "given_name": _safe_str(r.get("givenName") or r.get("given_name")),
                "family_name": _safe_str(r.get("familyName") or r.get("family_name")),
                "nationality": _safe_str(r.get("nationality")),
            }
            _, created = Driver.objects.update_or_create(
                ergast_id=driver_id,
                defaults=defaults,
            )
            if created:
                created_count += 1

        return created_count

    def _ingest_events_and_circuits_for_year(
        self, ergast: Ergast, year: int
    ) -> Tuple[int, int, List[int]]:
        """
        Uses Ergast race schedule to create:
          - Circuit (circuitId, circuitName, country)
          - Event (season, round, country, circuit)
        Returns: (created_circuits, created_events, list_of_round_numbers)
        """
        season = Season.objects.get(year=year)

        # Ergast schedule: races with Circuit fields including circuitId
        resp = ergast.get_race_schedule(season=year, limit=1000)
        races = _extract_ergast_rows(resp)

        created_circuits = 0
        created_events = 0
        rounds: List[int] = []

        for race in races:
            # Typical nesting:
            # {
            #   "round": "1",
            #   "Circuit": {"circuitId": "...", "circuitName": "...", "Location": {"country": "..."}}
            #   "raceName": "...",
            #   ...
            # }
            round_raw = race.get("round")
            try:
                rnd = int(str(round_raw))
            except Exception:
                continue

            circuit = race.get("Circuit") or {}
            circuit_id = _safe_str(circuit.get("circuitId") or circuit.get("circuit_id"))
            circuit_name = _safe_str(circuit.get("circuitName") or circuit.get("name"))
            loc = circuit.get("Location") or {}
            circuit_country = _safe_str(loc.get("country"))

            if not circuit_id:
                continue

            circuit_obj, circuit_created = Circuit.objects.update_or_create(
                ergast_id=circuit_id,
                defaults={
                    "name": circuit_name or circuit_id,
                    "country": circuit_country,
                },
            )
            if circuit_created:
                created_circuits += 1

            # Event country: prefer circuit country, else try race Location
            event_country = circuit_country or _safe_str(race.get("country"))

            _, event_created = Event.objects.update_or_create(
                season=season,
                round=rnd,
                defaults={
                    "country": event_country,
                    "circuit": circuit_obj,
                },
            )
            if event_created:
                created_events += 1

            rounds.append(rnd)

        return created_circuits, created_events, sorted(set(rounds))

    def _ingest_sessions_for_year(self, year: int, rounds: List[int]) -> int:
        """
        Uses fastf1.get_event_schedule(year) to populate Session(event, session_type).
        We match schedule rows by RoundNumber.
        """
        created = 0
        season = Season.objects.get(year=year)

        try:
            schedule = fastf1.get_event_schedule(year, include_testing=False)
        except Exception:
            # Some very old seasons may not be supported in schedule
            return 0

        if schedule is None or len(schedule) == 0:
            return 0

        # RoundNumber column is common; fallback to "Round" if needed.
        round_col = "RoundNumber" if "RoundNumber" in schedule.columns else ("Round" if "Round" in schedule.columns else None)
        if round_col is None:
            return 0

        for rnd in rounds:
            ev = Event.objects.filter(season=season, round=rnd).first()
            if not ev:
                continue

            row_df = schedule.loc[schedule[round_col] == rnd]
            if row_df.empty:
                continue
            row = row_df.iloc[0]

            session_types = _extract_sessions_from_schedule_row(row)
            for st in session_types:
                _, was_created = Session.objects.get_or_create(
                    event=ev,
                    session_type=st,
                )
                if was_created:
                    created += 1

        return created
