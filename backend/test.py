import os
import django
import fastf1
import pandas as pd

# Load Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Season, Event, Session

session = fastf1.get_session(2025, 'Australia', 'Practice 2')
session.load()  # loads data into `session` in-place

laps = session.laps   # <-- this is what you want

# keep only laps with a valid, accurate LapTime
valid_laps = laps.pick_accurate().dropna(subset=['LapTime'])

# group by driver and take the minimum LapTime
best_laps = (
    valid_laps
    .groupby('DriverNumber')['LapTime']
    .min()
)

# df_simple = results[['Abbreviation', 'Q1', 'Q2', 'Q3']].copy()

# # Convert times to strings (avoid NaT)
# for col in ['Q1', 'Q2', 'Q3']:
#     df_simple[col] = df_simple[col].apply(lambda x: None if pd.isna(x) else str(x))

# # Add “best time” column
# df_simple['BestTime'] = results[['Q1','Q2','Q3']].min(axis=1)

print(best_laps)