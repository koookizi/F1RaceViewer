from __future__ import annotations

from datetime import date
import time

import pandas as pd
import fastf1
from fastf1.ergast import Ergast

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from api.models import Season, Circuit, Event, Session, Team, Driver, Result, TeamStanding, DriverStanding

fastf1.Cache.enable_cache("api/fastf1_cache")


class Command(BaseCommand):
    help = "Populate F1 DB from 1950 to current season (FastF1 sessions 2018+, FastF1 Ergast pre-2018)"

    def add_arguments(self, parser):
        parser.add_argument("--start", type=int, default=1950)
        parser.add_argument("--end", type=int, default=date.today().year)
        parser.add_argument("--seasons", nargs="*", type=int, help="Optional list of specific seasons to ingest")

        # Optional safety switches (helpful if you still hit rate limits)
        parser.add_argument("--sleep", type=float, default=0.0, help="Sleep between HTTP calls (seconds)")
        parser.add_argument("--retries", type=int, default=4, help="Retries for Ergast calls on failure")
        parser.add_argument("--backoff", type=float, default=2.0, help="Backoff multiplier for retries")

    def handle(self, *args, **opts):
        self.sleep_s = float(opts["sleep"])
        self.retries = int(opts["retries"])
        self.backoff = float(opts["backoff"])

        # Ergast via FastF1 wrapper (used for 1950-2017 and constructor standings fallback)
        self.ergast = Ergast(result_type="pandas", auto_cast=True, limit=1000)

        if opts["seasons"]:
            years = opts["seasons"]
        else:
            years = list(range(opts["start"], opts["end"] + 1))

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

        if year >= 2018:
            self.ingest_season_fastf1_sessions(season_obj, year)
        else:
            self.ingest_season_ergast_bulk(season_obj, year)

        # standings at end (official if clean, else computed fallback)
        self.ingest_constructor_standings(self.ergast, season_obj, year)
        self.ingest_driver_standings(self.ergast, season_obj, year)

    # ----------------------------
    # Shared helpers
    # ----------------------------
    def ensure_sessions(self, event_obj: Event):
        for st in ["Practice 1", "Practice 2", "Practice 3", "Qualifying", "Race"]:
            Session.objects.get_or_create(event=event_obj, session_type=st)

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
                # Backoff and retry
                if attempt < self.retries - 1:
                    time.sleep(delay)
                    delay *= self.backoff
        raise last_exc

    @staticmethod
    def _df0(resp):
        # FastF1 Ergast responses often have .content as a list of DFs
        if hasattr(resp, "content"):
            if not resp.content:
                return None
            return resp.content[0]
        return resp

    @staticmethod
    def _group_by_round(df: pd.DataFrame | None) -> dict[int, pd.DataFrame]:
        if df is None or len(df) == 0 or "round" not in df.columns:
            return {}
        out: dict[int, pd.DataFrame] = {}
        for rnd, grp in df.groupby("round"):
            out[int(rnd)] = grp
        return out

    # ----------------------------
    # 2018+ path: FastF1 session results (no Ergast per-round spam)
    # ----------------------------
    def ingest_season_fastf1_sessions(self, season_obj: Season, year: int):
        schedule = fastf1.get_event_schedule(year)
        ergast_round_map = self._ergast_round_to_race_row(year)


        # Some schedule rows can be "testing"/non-race; filter to actual race events
        # RoundNumber should exist for real events.
        schedule = schedule[schedule["RoundNumber"].notna()]

        for _, row in schedule.iterrows():
            rnd = int(row["RoundNumber"])
            event_name = row["EventName"]
            country = row.get("Country") or ""
            
            # Get Ergast schedule row for this round (1 Ergast schedule call per season)
            ergast_race_row = ergast_round_map.get(rnd)

            if ergast_race_row is not None:
                circuit_obj = self._upsert_circuit_from_ergast_row(ergast_race_row)
            else:
                # Fallback if Ergast schedule missing for some reason
                fallback_name = (row.get("Location") or row.get("EventName") or "").strip()
                fallback_id = fallback_name.lower().strip().replace(" ", "_")[:64] or f"unknown_{year}_{rnd}"
                circuit_obj, _ = Circuit.objects.update_or_create(
                    ergast_id=fallback_id,
                    defaults={"name": fallback_name[:100] or fallback_id[:100], "country": country[:100]},
                )

            event_obj, _ = Event.objects.update_or_create(
                season=season_obj,
                round=rnd,
                defaults={"country": country, "circuit": circuit_obj},
            )


            self.ensure_sessions(event_obj)

            # Qualifying
            try:
                q = fastf1.get_session(year, event_name, "Q")
                q.load(
                    laps=False,
                    telemetry=False,
                    weather=False,
                    messages=False
                )
                self._ingest_fastf1_results_df(q.results, event_obj, session_type="Q")
            except Exception as e:
                self.stdout.write(f"    {year} R{rnd} {event_name}: no qualifying ({e})")

            # Race
            try:
                r = fastf1.get_session(year, event_name, "R")
                r.load(
                    laps=False,
                    telemetry=False,
                    weather=False,
                    messages=False
                )
                self._ingest_fastf1_results_df(r.results, event_obj, session_type="R")
            except Exception as e:
                self.stdout.write(f"    {year} R{rnd} {event_name}: no race results ({e})")

    def _ingest_fastf1_results_df(self, df: pd.DataFrame, event_obj: Event, session_type: str):
        """
        Ingest FastF1 session.results dataframe into Team/Driver/Result.
        session_type: "R" or "Q"
        """
        if df is None or len(df) == 0:
            return

        # Expected columns include: DriverId, FirstName, LastName, Nationality, TeamName, GridPosition, Position, Points
        for _, row in df.iterrows():
            driver_id = row.get("DriverId")
            if pd.isna(driver_id) or driver_id is None:
                continue

            team_name = row.get("TeamName") or ""
            # Create a stable-ish id for team if you don't have Ergast constructorId from this path
            team_slug = team_name.lower().strip().replace(" ", "_").replace("-", "_")[:64] or "unknown"

            team_obj, _ = Team.objects.update_or_create(
                ergast_id=team_slug,
                defaults={
                    "name": team_name[:100] if team_name else "Unknown",
                    "nationality": "",  # FastF1 doesn't consistently provide nationality here
                },
            )

            driver_obj, _ = Driver.objects.update_or_create(
                ergast_id=str(driver_id),
                defaults={
                    "given_name": str(row.get("FirstName") or "")[:100],
                    "family_name": str(row.get("LastName") or "")[:100],
                    "nationality": str(row.get("Nationality") or "")[:100],
                },
            )

            # FastF1 uses NaN sometimes
            grid_raw = row.get("GridPosition")
            pos_raw = row.get("Position")
            pts_raw = row.get("Points")

            grid = int(grid_raw) if grid_raw is not None and not pd.isna(grid_raw) else None
            pos = int(pos_raw) if pos_raw is not None and not pd.isna(pos_raw) else None

            # Points only meaningful for race; keep 0 for qualifying
            points = float(pts_raw) if (session_type == "R" and pts_raw is not None and not pd.isna(pts_raw)) else 0.0

            Result.objects.update_or_create(
                event=event_obj,
                session_type=session_type,
                driver=driver_obj,
                defaults={
                    "team": team_obj,
                    "grid": grid if session_type == "R" else None,
                    "position": pos,
                    "points": points,
                },
            )

    # ----------------------------
    # 1950-2017 path: Ergast bulk (season-wide requests)
    # ----------------------------
    def ingest_season_ergast_bulk(self, season_obj: Season, year: int):
        # Schedule (1 request)
        schedule = self._ergast_call(self.ergast.get_race_schedule, season=year)
        if schedule is None or len(schedule) == 0:
            self.stdout.write(f"No schedule found for {year} (skipping).")
            return

        # Race results for whole season (1 request)
        race_resp = self._ergast_call(self.ergast.get_race_results, season=year)

        race_by_round = {}
        if hasattr(race_resp, "description") and hasattr(race_resp, "content"):
            # MultiResponse: one df per round
            for i, desc in race_resp.description.iterrows():
                rnd = int(desc["round"])
                race_by_round[rnd] = race_resp.content[i]
        else:
            # Fallback (older/simple response shape)
            race_df = self._df0(race_resp)
            race_by_round = self._group_by_round(race_df)

        # Qualifying for whole season (1 request) - may be missing in early eras
        try:
            quali_resp = self._ergast_call(self.ergast.get_qualifying_results, season=year)
            quali_by_round = {}
            if hasattr(quali_resp, "description") and hasattr(quali_resp, "content"):
                for i, desc in quali_resp.description.iterrows():
                    rnd = int(desc["round"])
                    quali_by_round[rnd] = quali_resp.content[i]
            else:
                quali_df = self._df0(quali_resp)
                quali_by_round = self._group_by_round(quali_df)
        except Exception:
            quali_by_round = {}


        for _, race in schedule.iterrows():
            rnd = int(race["round"])
            country = race.get("country") or ""
            circuit_obj = self._upsert_circuit_from_ergast_row(race)

            event_obj, _ = Event.objects.update_or_create(
                season=season_obj,
                round=rnd,
                defaults={"country": country, "circuit": circuit_obj},
            )
            self.ensure_sessions(event_obj)

            # Race results for this round from pre-fetched DF
            if rnd in race_by_round:
                self.ingest_race_results_df(race_by_round[rnd], event_obj)

            # Quali results for this round from pre-fetched DF
            if rnd in quali_by_round:
                self.ingest_quali_results_df(quali_by_round[rnd], event_obj)
            else:
                # Keep your earlier “no quali” log behaviour
                # (Only print if there is no quali data at all for this round)
                pass

    def ingest_race_results_df(self, results_df: pd.DataFrame, event_obj: Event):
        if results_df is None or len(results_df) == 0:
            return

        for _, r in results_df.iterrows():
            team_obj, _ = Team.objects.update_or_create(
                ergast_id=r["constructorId"],
                defaults={
                    "name": r["constructorName"],
                    "nationality": r.get("constructorNationality") or "",
                },
            )

            driver_obj, _ = Driver.objects.update_or_create(
                ergast_id=r["driverId"],
                defaults={
                    "given_name": r["givenName"],
                    "family_name": r["familyName"],
                    "nationality": r.get("driverNationality") or "",
                },
            )

            grid = int(r["grid"]) if int(r["grid"]) >= 0 else None
            pos = int(r["position"]) if int(r["position"]) >= 0 else None
            points = float(r["points"]) if r.get("points") is not None else 0.0

            Result.objects.update_or_create(
                event=event_obj,
                session_type="R",
                driver=driver_obj,
                defaults={"team": team_obj, "grid": grid, "position": pos, "points": points},
            )

    def ingest_quali_results_df(self, quali_df: pd.DataFrame, event_obj: Event):
        if quali_df is None or len(quali_df) == 0:
            return

        for _, q in quali_df.iterrows():
            team_obj, _ = Team.objects.update_or_create(
                ergast_id=q["constructorId"],
                defaults={
                    "name": q["constructorName"],
                    "nationality": q.get("constructorNationality") or "",
                },
            )

            driver_obj, _ = Driver.objects.update_or_create(
                ergast_id=q["driverId"],
                defaults={
                    "given_name": q["givenName"],
                    "family_name": q["familyName"],
                    "nationality": q.get("driverNationality") or "",
                },
            )

            pos = int(q["position"]) if q.get("position") is not None else None
            if pos is not None and pos < 0:
                pos = None

            Result.objects.update_or_create(
                event=event_obj,
                session_type="Q",
                driver=driver_obj,
                defaults={"team": team_obj, "grid": None, "position": pos, "points": 0.0},
            )

    def _upsert_circuit_from_ergast_row(self, race_row) -> Circuit:
        """
        Given one Ergast schedule row, create/update Circuit from circuitId + circuitName.
        """
        circuit_id = (race_row.get("circuitId") or "").strip()
        circuit_name = (race_row.get("circuitName") or "").strip()
        country = (race_row.get("country") or "").strip()

        if not circuit_id:
            # Fallback: derive a stable-ish id from the name
            circuit_id = circuit_name.lower().strip().replace(" ", "_")[:64] or "unknown"

        circuit_obj, _ = Circuit.objects.update_or_create(
            ergast_id=circuit_id,
            defaults={
                "name": circuit_name[:100] if circuit_name else circuit_id[:100],
                "country": country[:100],
            },
        )
        return circuit_obj

    def _ergast_round_to_race_row(self, year: int) -> dict[int, object]:
        """
        Fetch Ergast schedule ONCE and return mapping: round -> row (so we can grab circuitId/name).
        """
        schedule = self._ergast_call(self.ergast.get_race_schedule, season=year)
        out = {}
        if schedule is None or len(schedule) == 0:
            return out
        for _, r in schedule.iterrows():
            out[int(r["round"])] = r
        return out


    # ----------------------------
    # Standings (same as your current approach, with fallback)
    # ----------------------------
    def ingest_driver_standings(self, ergast: Ergast, season_obj: Season, year: int):
        DriverStanding.objects.filter(season=season_obj).delete()

        standings_df = None
        try:
            resp = self._ergast_call(ergast.get_driver_standings, season=year)
            standings_df = self._df0(resp)
        except Exception:
            standings_df = None

        # 1) Prefer official Ergast driver standings if present and clean
        if standings_df is not None and len(standings_df) > 0:
            if "position" in standings_df.columns and not standings_df["position"].isna().any():
                for _, s in standings_df.iterrows():
                    driver_obj, _ = Driver.objects.update_or_create(
                        ergast_id=s["driverId"],
                        defaults={
                            "given_name": s.get("givenName") or "",
                            "family_name": s.get("familyName") or "",
                            "nationality": s.get("driverNationality") or "",
                        },
                    )

                    DriverStanding.objects.create(
                        season=season_obj,
                        driver=driver_obj,
                        position=int(s["position"]),
                        points=float(s["points"]) if s.get("points") is not None and not pd.isna(s.get("points")) else 0.0,
                    )

                self.stdout.write(f"  Driver standings: used Ergast standings for {year}")
                return

        # 2) Fallback: compute from race points in Result
        computed = (
            Result.objects.filter(event__season=season_obj, session_type="R")
            .values("driver_id")
            .annotate(total_points=Sum("points"))
            .order_by("-total_points")
        )

        if not computed:
            self.stdout.write(f"  Driver standings: no race results to compute for {year}")
            return

        for pos, row in enumerate(computed, start=1):
            DriverStanding.objects.create(
                season=season_obj,
                driver_id=row["driver_id"],
                position=pos,
                points=float(row["total_points"] or 0.0),
            )

        self.stdout.write(f"  Driver standings: computed from race points for {year}")

    def ingest_constructor_standings(self, ergast: Ergast, season_obj: Season, year: int):
        TeamStanding.objects.filter(season=season_obj).delete()

        if year < 1958:
            self.stdout.write(f"  Standings: skipping {year} (no constructors championship)")
            return

        standings_df = None
        try:
            resp = self._ergast_call(ergast.get_constructor_standings, season=year)
            standings_df = self._df0(resp)
        except Exception:
            standings_df = None

        if standings_df is not None and len(standings_df) > 0:
            if "position" in standings_df.columns and not standings_df["position"].isna().any():
                for _, s in standings_df.iterrows():
                    team_obj, _ = Team.objects.update_or_create(
                        ergast_id=s["constructorId"],
                        defaults={
                            "name": s.get("constructorName") or "",
                            "nationality": s.get("constructorNationality") or "",
                        },
                    )

                    TeamStanding.objects.create(
                        season=season_obj,
                        team=team_obj,
                        position=int(s["position"]),
                        points=float(s["points"]) if s.get("points") is not None and not pd.isna(s.get("points")) else 0.0,
                    )

                self.stdout.write(f"  Standings: used Ergast standings for {year}")
                return

        computed = (
            Result.objects.filter(event__season=season_obj, session_type="R")
            .values("team_id")
            .annotate(total_points=Sum("points"))
            .order_by("-total_points")
        )

        if not computed:
            self.stdout.write(f"  Standings: no race results to compute for {year}")
            return

        for pos, row in enumerate(computed, start=1):
            TeamStanding.objects.create(
                season=season_obj,
                team_id=row["team_id"],
                position=pos,
                points=float(row["total_points"] or 0.0),
            )

        self.stdout.write(f"  Standings: computed from race points for {year}")
