from django.urls import path
from . import views

urlpatterns = [
    path('seasons_years/', views.season_years, name='season-years'),
    path("seasons/<int:year>/countries/", views.season_countries, name="season-countries"),
    path("seasons/<int:year>/<str:country>/sessions/", views.season_sessions, name="season-sessions"),
    path("session/<int:year>/<str:country>/<str:session>/result/", views.results_view, name="session-result"),
    path("session/<int:year>/<str:country>/circuit/", views.session_circuit, name="session-circuit"),
    path("session/<int:year>/<str:country>/<str:session_name>/playback/", views.session_playback_view, name="session-playback"),
    path("session/<int:year>/<str:country>/<str:session>/weather/", views.session_weather_view, name="session-weather"),
    path("session/<int:year>/<str:country>/<str:session>/laps/", views.session_laps_view, name="session-laps"),
    path("session/<int:year>/<str:country>/<str:session_name>/telemetry/", views.session_telemetry_view, name="session-telemetry"),
    path("session/<int:year>/<str:country>/<str:session_name>/leaderboard/", views.session_leaderboard_view, name="session-leaderboard"),
    path("session/<int:year>/<str:country>/<str:session_name>/racecontrol/", views.session_racecontrol_view, name="session-racecontrol"),
    path("session/<int:year>/<str:country>/<str:session_name>/teamradio/", views.session_teamradio_view, name="session-teamradio"),
    path("session/vr/create/", views.vr_create_view, name="session-vr-create"),
    path("session/<int:year>/<str:country>/<str:session_name>/vr/", views.session_vrdetails_view, name="session-vr"),
    path("teams/", views.teams_getTeams, name="teams-getteams"),
    path("teams/<str:team_ergast_id>/summary/", views.teams_getTeamSummary, name="teams-getteamsummary"),
    path("teams/<str:team>/currentseason/", views.teams_getCurrentSeason, name="teams-getcurrentseason"),
    path("drivers/", views.drivers_getDrivers, name="drivers-getdrivers"),





]
