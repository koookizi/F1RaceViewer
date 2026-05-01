from datetime import datetime, timezone
from urllib.parse import urlencode

import pandas as pd
from django.core.management.base import BaseCommand, CommandError

from api.helpers.openf1 import is_rate_limited, openf1_json


DEMO_CACHE_TIMEOUT = 60 * 60 * 24 * 30
DEMO_RETRIES = 8
DEMO_RETRY_DELAY = 2.0


class Command(BaseCommand):
    help = "Warm persistent OpenF1 cache entries needed for the demo flows."

    def handle(self, *args, **options):
        warmed = 0
        warmed += self._warm_race_viewer_demo()
        warmed += self._warm_current_season_team_demo("Mercedes")
        warmed += self._warm_current_season_driver_demo("Lando Norris")

        self.stdout.write(
            self.style.SUCCESS(f"Warmed {warmed} demo-specific OpenF1 requests.")
        )

    def _fetch(self, url: str):
        payload = openf1_json(
            url,
            timeout=DEMO_CACHE_TIMEOUT,
            retries=DEMO_RETRIES,
            retry_delay=DEMO_RETRY_DELAY,
        )

        if is_rate_limited(payload):
            raise CommandError(f"OpenF1 rate-limited while warming: {url}")

        if isinstance(payload, dict):
            detail = payload.get("detail")
            status = payload.get("status")
            if detail == "No results found.":
                self.stdout.write(f"Checked {url} -> no results yet")
                return payload
            if status and int(status) >= 400:
                raise CommandError(f"OpenF1 returned {status} for {url}: {detail}")

        self.stdout.write(f"Warmed {url}")
        return payload

    def _warm_race_viewer_demo(self) -> int:
        year = 2024
        country = "United Kingdom"
        session_name = "Race"

        session_query = urlencode(
            {
                "country_name": country,
                "session_name": session_name,
                "year": year,
            }
        )
        session_url = f"https://api.openf1.org/v1/sessions?{session_query}"
        sessions_payload = self._fetch(session_url)
        if not isinstance(sessions_payload, list) or not sessions_payload:
            raise CommandError("Could not resolve OpenF1 session metadata for the demo race.")

        session_row = sessions_payload[0]
        session_key = session_row["session_key"]
        meeting_key = session_row["meeting_key"]
        date_start = session_row["date_start"]

        urls = [
            f"https://api.openf1.org/v1/team_radio?session_key={session_key}&date>{date_start}",
            f"https://api.openf1.org/v1/race_control?session_key={session_key}&date>{date_start}",
            f"https://api.openf1.org/v1/position?meeting_key={meeting_key}&date>={date_start}",
            f"https://api.openf1.org/v1/laps?session_key={session_key}&date_start>={date_start}",
            f"https://api.openf1.org/v1/stints?session_key={session_key}",
            f"https://api.openf1.org/v1/pit?session_key={session_key}&date>={date_start}",
            f"https://api.openf1.org/v1/intervals?meeting_key={meeting_key}",
            f"https://api.openf1.org/v1/drivers?session_key={session_key}",
        ]

        for url in urls:
            self._fetch(url)

        return 1 + len(urls)

    def _warm_current_season_team_demo(self, team_name: str) -> int:
        context = self._build_current_season_context()
        championship_df, standings_session_key, championship_warmed = self._resolve_championship_context(
            candidate_races=context["candidate_races"],
            endpoint="championship_teams",
        )
        warmed = context["warmed"] + championship_warmed

        matching_team = championship_df[championship_df["team_name"] == team_name]
        if matching_team.empty:
            raise CommandError(f"Team '{team_name}' was not found in warmed championship data.")

        drivers_url = (
            "https://api.openf1.org/v1/drivers?"
            + urlencode(
                {
                    "team_name": team_name,
                    "session_key": standings_session_key,
                }
            )
        )
        drivers_payload = self._fetch(drivers_url)
        drivers_df = pd.DataFrame(drivers_payload if isinstance(drivers_payload, list) else [])
        if drivers_df.empty:
            raise CommandError(f"No drivers were returned for team '{team_name}'.")

        driver_numbers = (
            drivers_df["driver_number"].dropna().astype(int).drop_duplicates().tolist()
        )
        warmed += 1
        warmed += self._warm_shared_season_result_urls(context, driver_numbers)
        return warmed

    def _warm_current_season_driver_demo(self, driver_name: str) -> int:
        context = self._build_current_season_context()
        championship_df, standings_session_key, championship_warmed = self._resolve_championship_context(
            candidate_races=context["candidate_races"],
            endpoint="championship_drivers",
        )
        warmed = context["warmed"] + championship_warmed

        parts = driver_name.split(" ", 1)
        if len(parts) != 2:
            raise CommandError("Driver demo name must be in 'First Last' format.")

        first_name, last_name = parts
        drivers_url = (
            "https://api.openf1.org/v1/drivers?"
            + urlencode(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "session_key": standings_session_key,
                }
            )
        )
        drivers_payload = self._fetch(drivers_url)
        drivers_df = pd.DataFrame(drivers_payload if isinstance(drivers_payload, list) else [])
        if drivers_df.empty:
            raise CommandError(f"Driver '{driver_name}' was not found in warmed driver data.")

        driver_numbers = (
            drivers_df["driver_number"].dropna().astype(int).drop_duplicates().tolist()
        )
        if not driver_numbers:
            raise CommandError(f"No driver number was returned for '{driver_name}'.")

        matching_driver = championship_df[
            championship_df["driver_number"] == driver_numbers[0]
        ]
        if matching_driver.empty:
            raise CommandError(
                f"Driver '{driver_name}' was not found in warmed championship standings."
            )

        warmed += 1
        warmed += self._warm_shared_season_result_urls(context, driver_numbers)
        return warmed

    def _build_current_season_context(self):
        now = datetime.now(timezone.utc)
        warmed = 0
        sessions = []

        for year in (now.year - 1, now.year):
            url = f"https://api.openf1.org/v1/sessions?year={year}"
            payload = self._fetch(url)
            warmed += 1
            if isinstance(payload, list):
                sessions.extend(payload)

        if not sessions:
            raise CommandError("No OpenF1 sessions were returned for the current-season warm-up.")

        session_df = pd.DataFrame(sessions)
        session_df["date_start"] = pd.to_datetime(session_df["date_start"], utc=True)
        session_df["date_end"] = pd.to_datetime(session_df["date_end"], utc=True)

        session_df = session_df[
            session_df["session_name"].isin(["Qualifying", "Sprint", "Race"])
        ].copy()
        started_races = session_df[
            (session_df["session_name"] == "Race") & (session_df["date_start"] <= now)
        ].copy()
        if started_races.empty:
            raise CommandError("No started race sessions were found for the current-season warm-up.")

        latest_year = int(started_races["year"].max())
        season_df = session_df[session_df["year"] == latest_year].copy()
        season_df = season_df.sort_values("date_start").reset_index(drop=True)

        candidate_races = (
            season_df[(season_df["session_name"] == "Race") & (season_df["date_end"] <= now)]
            .sort_values("date_start", ascending=False)
            .reset_index(drop=True)
        )
        if candidate_races.empty:
            raise CommandError("No completed race sessions were found for the current-season warm-up.")

        return {
            "warmed": warmed,
            "season_df": season_df,
            "candidate_races": candidate_races,
            "race_session_keys": season_df.loc[
                season_df["session_name"] == "Race", "session_key"
            ].astype(int).tolist(),
            "sprint_session_keys": season_df.loc[
                season_df["session_name"] == "Sprint", "session_key"
            ].astype(int).tolist(),
            "qualifying_session_keys": season_df.loc[
                season_df["session_name"] == "Qualifying", "session_key"
            ].astype(int).tolist(),
        }

    def _resolve_championship_context(self, *, candidate_races, endpoint: str):
        warmed = 0

        for _, race_row in candidate_races.iterrows():
            session_key = int(race_row["session_key"])
            url = f"https://api.openf1.org/v1/{endpoint}?session_key={session_key}"
            payload = self._fetch(url)
            warmed += 1

            if isinstance(payload, dict) and payload.get("detail") == "No results found.":
                continue

            if not isinstance(payload, list) or not payload:
                continue

            championship_df = pd.DataFrame(payload)
            if not championship_df.empty:
                return championship_df, session_key, warmed

        raise CommandError(f"No usable data was returned from OpenF1 endpoint '{endpoint}'.")

    def _warm_shared_season_result_urls(self, context, driver_numbers) -> int:
        warmed = 0

        session_number_pairs = [("session_key", key) for key in context["sprint_session_keys"]]
        session_number_pairs += [("session_key", key) for key in context["race_session_keys"]]
        driver_number_pairs = [("driver_number", number) for number in driver_numbers]

        if session_number_pairs:
            results_query = urlencode(session_number_pairs + driver_number_pairs)
            self._fetch(f"https://api.openf1.org/v1/session_result?{results_query}")
            warmed += 1

        qualifying_pairs = [
            ("session_key", key) for key in context["qualifying_session_keys"]
        ]
        if qualifying_pairs:
            grid_query = urlencode(qualifying_pairs + driver_number_pairs)
            self._fetch(f"https://api.openf1.org/v1/starting_grid?{grid_query}")
            warmed += 1

        return warmed
