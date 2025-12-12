from django.urls import path
from . import views

urlpatterns = [
    path('seasons_years/', views.season_years, name='season-years'),
    path("seasons/<int:year>/countries/", views.season_countries, name="season-countries"),
    path("seasons/<int:year>/<str:country>/sessions/", views.season_sessions, name="season-sessions"),
    path("session/<int:year>/<str:country>/<str:session>/result/", views.results_view, name="session-result"),
    path("session/<int:year>/<str:country>/circuit/", views.session_circuit, name="session-circuit"),
    path("session/<int:year>/<str:country>/<str:session>/playback/", views.session_playback_view, name="session-playback"),
    path("session/<int:year>/<str:country>/<str:session>/weather/", views.session_weather_view, name="session-weather"),
    path("session/<int:year>/<str:country>/<str:session>/leaderboard/", views.session_leaderboard_view, name="session-leaderboard")

]
