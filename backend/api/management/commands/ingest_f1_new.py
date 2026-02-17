from __future__ import annotations

from datetime import date
import time
from typing import Any

import pandas as pd
from fastf1.ergast import Ergast

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Season, Circuit, Event, Session, Team, Driver


class Command(BaseCommand):
    help = (
        "Populate F1 DB from 1950 to current season (Ergast/Jolpica via FastF1 Ergast wrapper), "
        "filling ONLY Season, Circuit, Event, Session, Team, Driver."
    )

    def add_arguments(self, parser):
        parser.add_argument("--start", type=int, default=1950)
        parser.add_argument("--end", type=int, default=date.today().year)
        parser.add_argument("--seasons", nargs="*", type=int, help="Optional list of specific seasons to ingest")

        # Optional safety switches (helpful if you hit rate limits)
        parser.add_argument("--sleep", type=float, default=1.0, help="Sleep between HTTP calls (seconds)")
        parser.add_argument("--retries", type=int, default=4, help="Retries for Ergast calls on failure")
        parser.add_argument("--backoff", type=float, default=2.0, help="Backoff multiplier for retries")

    def handle(self, *args, **opts):
        self.sleep_s = float(opts["sleep"])
        self.retries = int(opts["retries"])
        self.backoff = float(opts["backoff"])

        # Ergast wrapper (FastF1 routes to Ergast-compatible sources; you can point it to Jolpica via env/config if needed)
        self.ergast = Ergast(result_type="pandas", auto_cast=True, limit=1000)

        if opts.get("seasons"):
            years = list(opts["seasons"])
        else:
            years = list(range(int(opts["start"]), int(opts["end"]) + 1))

        if not years:
            self.stdout.write("No seasons selected.")
            return

        self.stdout.write(f"Ingesting seasons: {years[0]} -> {years[-1]} ({len(years)} seasons)")
        for year in years:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n=== {year} ==="))
            self.ingest_season(year)

        self.stdout.write(self.style.SUCCESS("\nDone."))

    # ----------------------------
    # Core season ingestion
    # ----------------------------
    @transaction.atomic
    def ingest_season(self, year: int):
        season_obj, _ = Season.objects.get_or_create(year=year)

        # 1) Create circuits + events + sessions from schedule (1 request)
        schedule_df = self._df0(self._ergast_call(self.ergast.get_race_schedule, season=year))
        if schedule_df is None or len(schedule_df) == 0:
            self.stdout.write(f"  No schedule found for {year} (skipping).")
            return

        for _, race_row in schedule_df.iterrows():
            rnd = int(race_row["round"])
            country = (race_row.get("country") or "").strip()

            circuit_obj = self._upsert_circuit_from_ergast_row(race_row)

            event_obj, _ = Event.objects.update_or_create(
                season=season_obj,
                round=rnd,
                defaults={
                    "country": country[:100],
                    "circuit": circuit_obj,
                },
            )

            self.ensure_sessions(event_obj)

        # 2) Create teams + drivers seen in race results (season-wide; 1 request)
        #    This is just for discovering entities; we do NOT store per-race results.
        try:
            race_resp = self._ergast_call(self.ergast.get_race_results, season=year)
            self.ingest_teams_and_drivers_from_race_results(race_resp)
        except Exception as e:
            self.stdout.write(f"  Could not ingest teams/drivers for {year}: {e}")

    # ----------------------------
    # Session helper
    # ----------------------------
    def ensure_sessions(self, event_obj: Event):
        """
        Your models.Session.session_type is max_length=5, so store short codes.
        You can map these codes to display names in the frontend.
        """
        # Keep a consistent superset; not all weekends will have all sessions historically.
        session_codes = ["Practice 1",
    "Practice 2",
    "Practice 3",
    "Qualifying",
    "Sprint",
    "Sprint Shootout",
    "Sprint Qualifying",
    "Race"]
        for code in session_codes:
            Session.objects.get_or_create(event=event_obj, session_type=code)

    # ----------------------------
    # Teams/Drivers ingestion (no Results table needed)
    # ----------------------------
    def ingest_teams_and_drivers_from_race_results(self, race_resp: Any):
        """
        race_resp may be a MultiResponse (one dataframe per round) or a single dataframe.
        We scan all rows and upsert Team + Driver from constructor/driver fields.
        """
        # MultiResponse case: race_resp.description + race_resp.content (list of dfs)
        if hasattr(race_resp, "description") and hasattr(race_resp, "content"):
            for df in race_resp.content:
                self._ingest_entities_from_results_df(df)
            return

        # Single DF case
        df = self._df0(race_resp)
        self._ingest_entities_from_results_df(df)

    def _ingest_entities_from_results_df(self, df: pd.DataFrame | None):
        if df is None or len(df) == 0:
            return

        # Expected Ergast columns commonly include:
        # driverId, givenName, familyName, driverNationality
        # constructorId, constructorName, constructorNationality
        for _, r in df.iterrows():
            constructor_id = r.get("constructorId")
            driver_id = r.get("driverId")

            if pd.isna(constructor_id) or not constructor_id:
                constructor_id = None
            if pd.isna(driver_id) or not driver_id:
                driver_id = None

            if constructor_id:
                Team.objects.update_or_create(
                    ergast_id=str(constructor_id)[:64],
                    defaults={
                        "name": str(r.get("constructorName") or "")[:100] or str(constructor_id)[:100],
                        "nationality": str(r.get("constructorNationality") or "")[:100],
                    },
                )

            if driver_id:
                Driver.objects.update_or_create(
                    ergast_id=str(driver_id)[:64],
                    defaults={
                        "given_name": str(r.get("givenName") or "")[:100],
                        "family_name": str(r.get("familyName") or "")[:100],
                        "nationality": str(r.get("driverNationality") or "")[:100],
                    },
                )

    # ----------------------------
    # Circuit upsert
    # ----------------------------
    def _upsert_circuit_from_ergast_row(self, race_row) -> Circuit:
        """
        Given one Ergast schedule row, create/update Circuit from circuitId + circuitName.
        """
        circuit_id = (race_row.get("circuitId") or "").strip()
        circuit_name = (race_row.get("circuitName") or "").strip()
        country = (race_row.get("country") or "").strip()

        if not circuit_id:
            # Fallback: derive a stable-ish id from the name
            circuit_id = (circuit_name.lower().strip().replace(" ", "_")[:64] or "unknown")

        circuit_obj, _ = Circuit.objects.update_or_create(
            ergast_id=circuit_id[:64],
            defaults={
                "name": (circuit_name[:100] if circuit_name else circuit_id[:100]),
                "country": country[:100],
            },
        )
        return circuit_obj

    # ----------------------------
    # Ergast helpers (retry/backoff + dataframe extraction)
    # ----------------------------
    def _maybe_sleep(self):
        if self.sleep_s and self.sleep_s > 0:
            time.sleep(self.sleep_s)

    def _ergast_call(self, fn, *args, **kwargs):
        """
        Call an Ergast method with retry/backoff (handles 429 and transient issues).
        """
        delay = 1.0
        last_exc = None
        for attempt in range(self.retries):
            try:
                self._maybe_sleep()
                return fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if attempt < self.retries - 1:
                    time.sleep(delay)
                    delay *= self.backoff
        raise last_exc

    @staticmethod
    def _df0(resp):
        """
        FastF1 Ergast responses often have .content as a list of DFs
        """
        if hasattr(resp, "content"):
            if not resp.content:
                return None
            return resp.content[0]
        return resp
