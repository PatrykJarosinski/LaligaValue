from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .models import Bookmaker, Match, MatchStatistics, OddsSnapshot, Season, Team


class SeedTestDataCommandTests(TestCase):
    def test_command_creates_idempotent_and_marked_test_data(self):
        call_command("seed_test_data", stdout=StringIO())
        initial_counts = {
            "seasons": Season.objects.count(),
            "teams": Team.objects.count(),
            "matches": Match.objects.count(),
            "statistics": MatchStatistics.objects.count(),
            "bookmakers": Bookmaker.objects.count(),
            "snapshots": OddsSnapshot.objects.count(),
        }

        call_command("seed_test_data", stdout=StringIO())

        self.assertEqual(Season.objects.get().name, "2026/27")
        self.assertEqual(initial_counts["teams"], 4)
        self.assertEqual(initial_counts["matches"], 4)
        self.assertEqual(initial_counts["statistics"], 2)
        self.assertEqual(initial_counts["bookmakers"], 2)
        self.assertEqual(initial_counts["snapshots"], 80)
        self.assertEqual(initial_counts["snapshots"], OddsSnapshot.objects.count())
        self.assertTrue(all(team.name.startswith("[TEST]") for team in Team.objects.all()))
        self.assertTrue(all(bookmaker.name.startswith("[TEST]") for bookmaker in Bookmaker.objects.all()))
