from django.urls import path
from . import views

urlpatterns = [
    path('seasons_years/', views.season_years, name='season-years'),
    path("seasons/<int:year>/countries/", views.season_countries, name="season-countries"),
    path("seasons/<int:year>/<str:country>/sessions", views.season_sessions, name="season-sessions"),

]
