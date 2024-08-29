from django.db import models
from users.models import TINETUser, AppAPIKey


class Leaderboard(models.Model):
    title = models.CharField(max_length=20, default="No title")
    description = models.CharField(max_length=100, default="No description")
    app = models.ForeignKey(AppAPIKey, on_delete=models.CASCADE, null=True)


class LeaderboardEntry(models.Model):
    user = models.ForeignKey(TINETUser, on_delete=models.CASCADE)
    score = models.BigIntegerField(default=0)
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE)
