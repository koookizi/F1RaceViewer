import fastf1 
from fastf1.ergast import Ergast

import pandas as pd

from api.models import Season

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Season, Circuit, Event, Session, Team, Driver

import time
import requests
from fastf1.ergast.interface import ErgastInvalidRequestError

def call_with_retry(fn, *, retries=8, wait_seconds=30):
    """
    Calls `fn()` and retries on 429 / Too Many Requests.

    Raises:
        - fastf1.ergast.interface.ErgastInvalidRequestError
        - requests.exceptions.HTTPError (raised by requests_cache/requests)
    """
    last_exc = None

    for attempt in range(1, retries + 1):
        try:
            return fn()

        except requests.exceptions.HTTPError as e:
            last_exc = e
            status = getattr(e.response, "status_code", None)
            msg = str(e).lower()

            if status == 429 or "too many requests" in msg or "429" in msg:
                if attempt == retries:
                    raise
                print(f"429 Too Many Requests. Waiting {wait_seconds}s... (attempt {attempt}/{retries})")
                time.sleep(wait_seconds)
                continue
            raise  # not a rate limit

        except ErgastInvalidRequestError as e:
            last_exc = e
            msg = str(e).lower()
            if "too many requests" in msg or "429" in msg:
                if attempt == retries:
                    raise
                print(f"Too Many Requests. Waiting {wait_seconds}s... (attempt {attempt}/{retries})")
                time.sleep(wait_seconds)
                continue
            raise  # not a rate limit

    # Shouldn't reach here, but just in case:
    raise last_exc



class Command(BaseCommand):
    """
    Populate F1 DB from 1950 to current season (FastF1 sessions 2018+, FastF1 Ergast pre-2018)
    """
    help = "Populate F1 DB from 1950 to current season (FastF1 sessions 2018+, FastF1 Ergast pre-2018)"

    def handle(self, *args, **opts):
        self.ergast = Ergast(result_type="pandas", auto_cast=True)

        seasons = self.ergast.get_seasons(limit=1000)
        seasons = list(seasons["season"])

        for year in seasons:
            self.stdout.write(f"-- YEAR {year} --")
            season_obj, _ = Season.objects.get_or_create(year=year)
            self.ingest_schedule(season_obj, year)
            self.stdout.write(f"Schedule ingested for season {year}")
            time.sleep(1.0)

        # for year in range(2026,2027):
        #     self.stdout.write(f"-- YEAR {year} --")
        #     season_obj, _ = Season.objects.get_or_create(year=year)
        #     self.ingest_schedule(season_obj, year)
        #     self.stdout.write(f"Schedule ingested for season {year}")
        #     time.sleep(1.0)

        drivers_created = self.ingest_drivers()
        teams_created = self.ingest_teams()

        self.stdout.write(self.style.SUCCESS(f"Schedule ingested for seasons {seasons[0]}-{seasons[-1]}"))
        self.stdout.write(self.style.SUCCESS(f"Drivers ingested: {drivers_created}"))
        self.stdout.write(self.style.SUCCESS(f"Teams ingested: {teams_created}"))


    # -- Main ingestion functions --
    @transaction.atomic
    def ingest_schedule(self, season_obj, year: int):
        session_names = ["Session1", "Session2", "Session3", "Session4","Session5"]

        schedule_df_fastf1 = pd.DataFrame(fastf1.get_event_schedule(year, include_testing=False))
        schedule_df_ergast = call_with_retry(
            lambda: self.ergast.get_race_schedule(season=year, limit=1000)
        )
        
        # get circuitId from ergast by matching round numbers
        schedule_df_fastf1["RoundNumber"] = schedule_df_fastf1["RoundNumber"].astype(int)
        schedule_df_ergast["round"] = schedule_df_ergast["round"].astype(int)
        ergast_necessary_columns = schedule_df_ergast[["round", "circuitId","circuitName"]]

        merged_df = schedule_df_fastf1.merge(
            ergast_necessary_columns,
            left_on="RoundNumber",
            right_on="round",
            how="left"
        )

        merged_df = merged_df.drop(columns=["round"])

        for _, row in merged_df.iterrows():
            rnd = row["RoundNumber"]
            country = row["Country"]
            circuit_obj = self._create_circuit_row(row)

            event_obj, _ = Event.objects.update_or_create(
                        season=season_obj,
                        round=rnd,
                        defaults={"country": country, "circuit": circuit_obj},
                    )
            
            for session in session_names:
                if pd.notna(row[session]):
                    Session.objects.update_or_create(
                        event=event_obj,
                        session_type=row[session],
                    )

    @transaction.atomic
    def ingest_drivers(self):
        response = call_with_retry(lambda: Ergast().get_driver_info(limit=5000))

        temp_df = []
        while True:
            temp_df.append(response)
            try:
                response = response.get_next_result_page()
            except ValueError:
                break
        drivers_df = pd.concat(temp_df, ignore_index=True)

        created = 0

        for _, driver in drivers_df.iterrows():
            ergast_id = driver["driverId"]

            _, was_created = Driver.objects.update_or_create(
                ergast_id=ergast_id,
                defaults={
                    "given_name": driver.get("givenName", ""),
                    "family_name": driver.get("familyName", ""),
                    "nationality": driver.get("driverNationality", ""),
                },
            )

            if was_created:
                created += 1

        return created

    @transaction.atomic
    def ingest_teams(self):
        response = call_with_retry(lambda: Ergast().get_constructor_info(limit=1000))
        
        temp_df = []
        while True:
            temp_df.append(response)
            try:
                response = response.get_next_result_page()
            except ValueError:
                break
        teams_dfs = pd.concat(temp_df, ignore_index=True)
        
        created = 0

        for _, row in teams_dfs.iterrows():
            ergast_id = row["constructorId"]

            _, was_created = Team.objects.update_or_create(
                ergast_id=ergast_id,
                defaults={
                    "name": row.get("constructorName", "") or "",
                    "nationality": row.get("constructorNationality", "") or "",
                },
            )

            if was_created:
                created += 1

        return created    

    # -- Helper functions for schedule ingestion --
    def _create_circuit_row(self, race_row) -> Circuit:
        circuit_id = (race_row["circuitId"] or "").strip()
        circuit_name = (race_row["circuitName"] or "").strip()
        country = (race_row["Country"] or "").strip()

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