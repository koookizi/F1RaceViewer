import os
import django
import fastf1
import pandas as pd

# Load Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Season, Event, Session

session = fastf1.get_session(2024, 'United Kingdom', 'Qualifying')
session.load()  # loads data into `session` in-place

results = session.results   # <-- this is what you want

df_simple = results[['Abbreviation', 'Q1', 'Q2', 'Q3']].copy()

# Convert times to strings (avoid NaT)
for col in ['Q1', 'Q2', 'Q3']:
    df_simple[col] = df_simple[col].apply(lambda x: None if pd.isna(x) else str(x))

# Add “best time” column
df_simple['BestTime'] = results[['Q1','Q2','Q3']].min(axis=1)

print(df_simple[['Abbreviation', 'BestTime']])