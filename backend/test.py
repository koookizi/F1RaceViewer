import fastf1 as ff1
import pandas as pd
import numpy as np

def to_float_or_none(value):
        if pd.isna(value):
            return None
        return float(value)

def session_weather_view(year: int, country: str, session: str):
    session_obj = ff1.get_session(year, country, session)

    session_obj.load(telemetry=False)

    weather_df = session_obj.laps.get_weather_data()


    # convert Time (timedelta) to seconds from session start and adds a column to the df
    weather_df = weather_df.copy()
    weather_df["TimeSec"] = weather_df["Time"].dt.total_seconds()

    rangeAirTemp = weather_df["AirTemp"].max().item(),weather_df["AirTemp"].min().item()
    rangeHumidity = weather_df["Humidity"].max().item(),weather_df["Humidity"].min().item()
    rangePressure = weather_df["Pressure"].max().item(),weather_df["Pressure"].min().item()
    rangeTrackTemp = weather_df["TrackTemp"].max().item(),weather_df["TrackTemp"].min().item()
    rangeWindSpeed = weather_df["WindSpeed"].max().item(),weather_df["WindSpeed"].min().item()


    samples = []
    for _, row in weather_df.iterrows():
        samples.append({
            "time_sec": float(row["TimeSec"]),         
            "air_temp": to_float_or_none(row["AirTemp"]),
            "track_temp": to_float_or_none(row["TrackTemp"]),
            "humidity": to_float_or_none(row["Humidity"]),
            "pressure": to_float_or_none(row["Pressure"]),
            "rainfall": to_float_or_none(row["Rainfall"]),
            "wind_dir": to_float_or_none(row["WindDirection"]),
            "wind_speed": to_float_or_none(row["WindSpeed"]),

        })

    return ({
         "weather": samples,
         "rangeAirTemp": {rangeAirTemp},
         "rangeHumidity": {rangeHumidity},
         "rangePressure": {rangePressure},
         "rangeTrackTemp": {rangeTrackTemp},
         "rangeWindSpeed": {rangeWindSpeed}
         })

print(session_weather_view(2025,"Australia","Practice 1"))