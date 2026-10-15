from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


class Season(models.Model):
    name = models.CharField(
        max_length=7,
        unique=True,
        validators=[RegexValidator(r"^\d{4}/\d{2}$", "Use the format YYYY/YY.")],
    )

    class Meta:
        ordering = ["-name"]

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Match(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        LIVE = "live", "Live"
        FINISHED = "finished", "Finished"
        POSTPONED = "postponed", "Postponed"
        CANCELLED = "cancelled", "Cancelled"

    season = models.ForeignKey(Season, on_delete=models.PROTECT, related_name="matches")
    home_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="home_matches")
    away_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="away_matches")
    kickoff_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SCHEDULED)
    home_score = models.PositiveSmallIntegerField(null=True, blank=True)
    away_score = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["kickoff_at"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(home_team=models.F("away_team")),
                name="match_different_teams",
            ),
            models.UniqueConstraint(
                fields=["season", "home_team", "away_team"],
                name="unique_season_home_away_match",
            ),
        ]
        indexes = [
            models.Index(fields=["season", "status", "kickoff_at"], name="match_season_status_kick_idx"),
            models.Index(fields=["home_team", "kickoff_at"], name="match_home_kickoff_idx"),
            models.Index(fields=["away_team", "kickoff_at"], name="match_away_kickoff_idx"),
        ]

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.kickoff_at:%Y-%m-%d})"


class MatchStatistics(models.Model):
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name="statistics")
    home_xg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    away_xg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    home_shots = models.PositiveSmallIntegerField(null=True, blank=True)
    away_shots = models.PositiveSmallIntegerField(null=True, blank=True)
    home_possession = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    away_possession = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(home_xg__isnull=True) | models.Q(home_xg__gte=Decimal("0")),
                name="statistics_home_xg_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(away_xg__isnull=True) | models.Q(away_xg__gte=Decimal("0")),
                name="statistics_away_xg_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(home_possession__isnull=True)
                | (models.Q(home_possession__gte=Decimal("0")) & models.Q(home_possession__lte=Decimal("100"))),
                name="statistics_home_possession_range",
            ),
            models.CheckConstraint(
                condition=models.Q(away_possession__isnull=True)
                | (models.Q(away_possession__gte=Decimal("0")) & models.Q(away_possession__lte=Decimal("100"))),
                name="statistics_away_possession_range",
            ),
        ]

    def __str__(self):
        return f"Statistics for match {self.match_id}"


class Bookmaker(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class OddsSnapshot(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="odds_snapshots")
    bookmaker = models.ForeignKey(Bookmaker, on_delete=models.PROTECT, related_name="odds_snapshots")
    market = models.CharField(max_length=64)
    selection = models.CharField(max_length=64)
    odds = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("1.001"))],
    )
    captured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-captured_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(odds__gt=Decimal("1.000")), name="odds_snapshot_odds_gt_one"),
            models.UniqueConstraint(
                fields=["match", "bookmaker", "market", "selection", "captured_at"],
                name="unique_odds_snapshot",
            ),
        ]
        indexes = [
            models.Index(
                fields=["match", "market", "selection", "captured_at"],
                name="odds_match_market_time_idx",
            ),
            models.Index(fields=["bookmaker", "captured_at"], name="odds_bookmaker_time_idx"),
        ]

    def __str__(self):
        return f"{self.bookmaker}: {self.market} / {self.selection} ({self.odds})"


class Prediction(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="predictions")
    market = models.CharField(max_length=64)
    selection = models.CharField(max_length=64)
    probability = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
    )
    model_version = models.CharField(max_length=64)
    generated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-generated_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(probability__gte=Decimal("0")) & models.Q(probability__lte=Decimal("1")),
                name="prediction_probability_range",
            ),
            models.UniqueConstraint(
                fields=["match", "market", "selection", "model_version", "generated_at"],
                name="unique_prediction_snapshot",
            ),
        ]
        indexes = [
            models.Index(
                fields=["match", "market", "selection", "generated_at"],
                name="prediction_match_time_idx",
            ),
            models.Index(fields=["model_version", "generated_at"], name="prediction_model_time_idx"),
        ]

    def __str__(self):
        return f"{self.model_version}: {self.market} / {self.selection} ({self.probability})"
