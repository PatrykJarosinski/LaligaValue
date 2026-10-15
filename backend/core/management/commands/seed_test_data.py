from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Bookmaker, Match, MatchStatistics, OddsSnapshot, Season, Team


TEST_PREFIX = "[TEST]"
SEASON_NAME = "2026/27"


def aware_datetime(day, hour, minute=0):
    return timezone.make_aware(datetime(2026, 10, day, hour, minute))


class Command(BaseCommand):
    help = "Adds idempotent, clearly marked test data for the LaLiga Value interface."

    @transaction.atomic
    def handle(self, *args, **options):
        season, season_created = Season.objects.get_or_create(name=SEASON_NAME)

        teams = {}
        team_names = ["Athletic Bilbao", "Real Madrid", "FC Barcelona", "Villarreal CF"]
        for name in team_names:
            team, _ = Team.objects.get_or_create(name=f"{TEST_PREFIX} {name}")
            teams[name] = team

        match_definitions = [
            {
                "home": "Athletic Bilbao",
                "away": "Real Madrid",
                "kickoff_at": aware_datetime(5, 20),
                "status": Match.Status.FINISHED,
                "home_score": 1,
                "away_score": 2,
                "statistics": {
                    "home_xg": Decimal("1.15"),
                    "away_xg": Decimal("1.72"),
                    "home_shots": 10,
                    "away_shots": 13,
                    "home_possession": Decimal("46.20"),
                    "away_possession": Decimal("53.80"),
                },
            },
            {
                "home": "FC Barcelona",
                "away": "Villarreal CF",
                "kickoff_at": aware_datetime(12, 18, 30),
                "status": Match.Status.FINISHED,
                "home_score": 0,
                "away_score": 0,
                "statistics": {
                    "home_xg": Decimal("1.48"),
                    "away_xg": Decimal("0.91"),
                    "home_shots": 15,
                    "away_shots": 8,
                    "home_possession": Decimal("61.40"),
                    "away_possession": Decimal("38.60"),
                },
            },
            {
                "home": "Real Madrid",
                "away": "FC Barcelona",
                "kickoff_at": aware_datetime(18, 21),
                "status": Match.Status.SCHEDULED,
                "home_score": None,
                "away_score": None,
            },
            {
                "home": "Villarreal CF",
                "away": "Athletic Bilbao",
                "kickoff_at": aware_datetime(24, 16, 15),
                "status": Match.Status.SCHEDULED,
                "home_score": None,
                "away_score": None,
            },
        ]

        matches = []
        for definition in match_definitions:
            match, _ = Match.objects.get_or_create(
                season=season,
                home_team=teams[definition["home"]],
                away_team=teams[definition["away"]],
                defaults={
                    "kickoff_at": definition["kickoff_at"],
                    "status": definition["status"],
                    "home_score": definition["home_score"],
                    "away_score": definition["away_score"],
                },
            )
            matches.append(match)
            if statistics := definition.get("statistics"):
                MatchStatistics.objects.get_or_create(match=match, defaults=statistics)

        bookmakers = []
        for name in ("OddsLab", "ValueBook"):
            bookmaker, _ = Bookmaker.objects.get_or_create(name=f"{TEST_PREFIX} {name}")
            bookmakers.append(bookmaker)

        market_selections = [
            ("1x2", "home", Decimal("2.150")),
            ("1x2", "draw", Decimal("3.400")),
            ("1x2", "away", Decimal("3.050")),
            ("over_under_2_5", "over_2_5", Decimal("1.850")),
            ("over_under_2_5", "under_2_5", Decimal("2.000")),
        ]
        capture_times = [aware_datetime(14, 10), aware_datetime(15, 10)]

        for match in matches:
            for bookmaker_index, bookmaker in enumerate(bookmakers):
                bookmaker_adjustment = Decimal(bookmaker_index) * Decimal("0.040")
                for market, selection, initial_odds in market_selections:
                    for snapshot_index, captured_at in enumerate(capture_times):
                        odds = initial_odds + bookmaker_adjustment - Decimal(snapshot_index) * Decimal("0.020")
                        OddsSnapshot.objects.get_or_create(
                            match=match,
                            bookmaker=bookmaker,
                            market=market,
                            selection=selection,
                            captured_at=captured_at,
                            defaults={"odds": odds},
                        )

        self.stdout.write(
            self.style.SUCCESS(
                "Test data ready: "
                f"season {season.name} ({'created' if season_created else 'already present'}), "
                f"{len(teams)} test teams, {len(matches)} test matches, "
                f"{len(bookmakers)} test bookmakers and {OddsSnapshot.objects.filter(match__in=matches).count()} snapshots."
            )
        )
