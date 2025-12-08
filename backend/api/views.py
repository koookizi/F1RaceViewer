from django.shortcuts import render
from django.http import JsonResponse
from api.models import Season, Event, Session


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
