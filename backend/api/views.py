from django.shortcuts import render
from django.http import JsonResponse
from api.models import Season, Event, Session
import fastf1
import pandas as pd 


def season_years(request):
    years = (
        Season.objects
        .order_by('-year')
        .values_list('year', flat=True)
    )
    return JsonResponse({"years":list(years)})

def season_countries(request, year):
    countries = (
        Event.objects
        .filter(season__year=year)
        .values_list('country', flat=True)
        .distinct()
        .order_by('country')
    )
    return JsonResponse({"countries": list(countries)})

def season_sessions(request, year, country):
    sessions = (
        Session.objects
        .filter(event__country=country)
        .filter(event__season__year=year)
        .values_list('session_type', flat=True)
        .distinct()
        .order_by('session_type')
    )
    return JsonResponse({"sessions": list(sessions)})

def session_circuit(request, year: int, country: str):
    event = Event.objects.filter(
        season__year=year,
        country=country
    ).first()
    if not event:
        return JsonResponse({"error": "Event not found"}, status=404)

    return JsonResponse({"circuit": event.circuit})


def results_view(request, year: int, country: str, session: str):
    session = fastf1.get_session(year, country, session)
    session.load()

    df = session.results  # pandas DataFrame-like

    # Safety: some columns might not exist for every session, so use df.get
    def to_str_or_none(value):
        if pd.isna(value):
            return None
        return str(value)
    
    def to_int_or_none(value):
        if pd.isna(value):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    results = []
    for _, row in df.iterrows():
        pos = row.get("Position", None)

        results.append({
            "position": to_int_or_none(pos),  
            "driverNumber": row.get("DriverNumber", ""),
            "abbreviation": row.get("Abbreviation", ""),
            "name": row.get("FullName", ""),
            "team": row.get("TeamName", ""),
            "team_color": row.get("TeamColor", ""),
            "headshot_url": row.get("HeadshotUrl", ""),
            "country_code": row.get("CountryCode", ""),
            "q1": to_str_or_none(row.get("Q1")),
            "q2": to_str_or_none(row.get("Q2")),
            "q3": to_str_or_none(row.get("Q3")),
            "bestLapTime": to_str_or_none(row.get("BestLapTime")),
            "status": row.get("Status", ""),
        })

    return JsonResponse({"results": results})