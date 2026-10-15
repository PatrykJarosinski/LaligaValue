from datetime import datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from .models import Bookmaker, Match, MatchStatistics, OddsSnapshot, Prediction, Season, Team


class ModelConstraintTests(TestCase):
    def setUp(self):
        self.season = Season.objects.create(name="2026/27")
        self.home_team = Team.objects.create(name="Athletic Club")
        self.away_team = Team.objects.create(name="Real Madrid")
        self.third_team = Team.objects.create(name="FC Barcelona")
        self.match = self.create_match(self.home_team, self.away_team, 21)

    def create_match(self, home_team, away_team, day):
        return Match.objects.create(
            season=self.season,
            home_team=home_team,
            away_team=away_team,
            kickoff_at=timezone.make_aware(datetime(2026, 8, day, 20, 0)),
        )

    def assert_database_rejects(self, create_object):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create_object()

    def test_season_format_and_unique_names_are_enforced(self):
        with self.assertRaises(ValidationError):
            Season(name="2026-27").full_clean()

        self.assert_database_rejects(lambda: Season.objects.create(name="2026/27"))
        self.assert_database_rejects(lambda: Team.objects.create(name="Athletic Club"))

    def test_match_constraints_reject_same_team_and_duplicate_fixture(self):
        self.assert_database_rejects(lambda: self.create_match(self.home_team, self.home_team, 22))
        self.assert_database_rejects(lambda: self.create_match(self.home_team, self.away_team, 23))

    def test_match_statistics_constraints_are_enforced(self):
        MatchStatistics.objects.create(match=self.match)
        second_match = self.create_match(self.away_team, self.third_team, 22)
        third_match = self.create_match(self.third_team, self.home_team, 23)

        self.assert_database_rejects(lambda: MatchStatistics.objects.create(match=self.match))
        self.assert_database_rejects(
            lambda: MatchStatistics.objects.create(match=second_match, home_xg=Decimal("-0.01"))
        )
        self.assert_database_rejects(
            lambda: MatchStatistics.objects.create(match=third_match, away_possession=Decimal("100.01"))
        )

    def test_odds_constraints_are_enforced(self):
        bookmaker = Bookmaker.objects.create(name="Example Bookmaker")
        captured_at = timezone.now()
        OddsSnapshot.objects.create(
            match=self.match,
            bookmaker=bookmaker,
            market="match_winner",
            selection="home",
            odds=Decimal("2.100"),
            captured_at=captured_at,
        )
        OddsSnapshot.objects.create(
            match=self.match,
            bookmaker=bookmaker,
            market="match_winner",
            selection="home",
            odds=Decimal("2.100"),
            captured_at=captured_at + timedelta(minutes=5),
        )

        self.assertEqual(OddsSnapshot.objects.filter(match=self.match).count(), 2)

        self.assert_database_rejects(
            lambda: OddsSnapshot.objects.create(
                match=self.match,
                bookmaker=bookmaker,
                market="match_winner",
                selection="draw",
                odds=Decimal("1.000"),
            )
        )
        self.assert_database_rejects(
            lambda: OddsSnapshot.objects.create(
                match=self.match,
                bookmaker=bookmaker,
                market="match_winner",
                selection="home",
                odds=Decimal("2.100"),
                captured_at=captured_at,
            )
        )

    def test_prediction_constraints_are_enforced(self):
        generated_at = timezone.now()
        Prediction.objects.create(
            match=self.match,
            market="match_winner",
            selection="home",
            probability=Decimal("0.5500"),
            model_version="test-v1",
            generated_at=generated_at,
        )

        self.assert_database_rejects(
            lambda: Prediction.objects.create(
                match=self.match,
                market="match_winner",
                selection="away",
                probability=Decimal("1.0001"),
                model_version="test-v1",
            )
        )
        self.assert_database_rejects(
            lambda: Prediction.objects.create(
                match=self.match,
                market="match_winner",
                selection="home",
                probability=Decimal("0.5500"),
                model_version="test-v1",
                generated_at=generated_at,
            )
        )
