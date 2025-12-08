import os
import django
import fastf1

# Load Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Season, Event, Session


print(fastf1.get_session(2025,"UK","Qualifying"))






# # # Example: create one event per season
# for season in Season.objects.all():
#     event, created = Event.objects.get_or_create(
#         season=season,
#         country="ExampleCountry",
#         circuit="ExampleCircuit",
#     )
#     Session.objects.get_or_create(event=event, session_type="P1")
#     Session.objects.get_or_create(event=event, session_type="P2")
#     Session.objects.get_or_create(event=event, session_type="Q")
#     Session.objects.get_or_create(event=event, session_type="R")

# print("Events + Sessions added!")
