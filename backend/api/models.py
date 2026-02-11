from django.db import models

class Season(models.Model):
    year = models.IntegerField()

class Circuit(models.Model):
    ergast_id = models.CharField(max_length=64, unique=True)   # e.g. "silverstone"
    name = models.CharField(max_length=100)                    # canonical display name
    country = models.CharField(max_length=100, blank=True)

class Event(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    round = models.IntegerField()
    country = models.CharField(max_length=100)
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("season", "round")

class Session(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=5)

class Team(models.Model):
    ergast_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100, blank=True)

class Driver(models.Model):
    ergast_id = models.CharField(max_length=64, unique=True)
    given_name = models.CharField(max_length=100)
    family_name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100, blank=True)

class Result(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=20)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    grid = models.IntegerField(null=True, blank=True)
    position = models.IntegerField(null=True, blank=True)
    points = models.FloatField(default=0)

class TeamStanding(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    position = models.IntegerField()
    points = models.FloatField(default=0)

class DriverStanding(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    position = models.IntegerField()
    points = models.FloatField(default=0)

    class Meta:
        unique_together = ("season", "driver")
