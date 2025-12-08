from django.db import models

class Season(models.Model):
    year = models.IntegerField()

class Event(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    country = models.CharField(max_length=100)
    circuit = models.CharField(max_length=100)

class Session(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=5)
