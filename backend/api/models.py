from django.db import models

class Season(models.Model):
    year = models.IntegerField(primary_key=True)

    def __str__(self):
        return str(self.year)


class Circuit(models.Model):
    ergast_id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    round = models.IntegerField()
    country = models.CharField(max_length=100)
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["season", "round"], name="uniq_event_season_round")
        ]

    def __str__(self):
        return f"{self.season_id} R{self.round} ({self.country})"


class Session(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "session_type"], name="uniq_session_event_type")
        ]

    def __str__(self):
        return f"{self.event_id} - {self.session_type}"


class Team(models.Model):
    ergast_id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Driver(models.Model):
    ergast_id = models.CharField(max_length=64, primary_key=True)
    given_name = models.CharField(max_length=100)
    family_name = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.given_name} {self.family_name}"