from datetime import datetime
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Bookmaker, Match, MatchStatistics, OddsSnapshot, Season, Team


class ReadApiTests(APITestCase):
    def setUp(self):
        self.season = Season.objects.create(name="2026/27")
        self.home_team = Team.objects.create(name="Athletic Club")
        self.away_team = Team.objects.create(name="Real Madrid")
        self.other_team = Team.objects.create(name="FC Barcelona")
        self.match = Match.objects.create(
            season=self.season,
            home_team=self.home_team,
            away_team=self.away_team,
            kickoff_at=timezone.make_aware(datetime(2026, 8, 21, 20, 0)),
            status=Match.Status.FINISHED,
            home_score=1,
            away_score=2,
        )
        self.other_match = Match.objects.create(
            season=self.season,
            home_team=self.away_team,
            away_team=self.other_team,
            kickoff_at=timezone.make_aware(datetime(2026, 8, 22, 20, 0)),
        )
        MatchStatistics.objects.create(
            match=self.match,
            home_xg=Decimal("1.20"),
            away_xg=Decimal("1.75"),
            home_shots=9,
            away_shots=12,
            home_possession=Decimal("45.50"),
            away_possession=Decimal("54.50"),
        )
        bookmaker = Bookmaker.objects.create(name="Example Bookmaker")
        OddsSnapshot.objects.create(
            match=self.match,
            bookmaker=bookmaker,
            market="match_winner",
            selection="away",
            odds=Decimal("2.150"),
        )

    def test_lists_seasons_and_teams_with_pagination(self):
        seasons = self.client.get(reverse("season-list"))
        teams = self.client.get(reverse("team-list"), {"page_size": 1})

        self.assertEqual(seasons.status_code, 200)
        self.assertEqual(seasons.data["count"], 1)
        self.assertEqual(teams.status_code, 200)
        self.assertEqual(teams.data["count"], 3)
        self.assertEqual(len(teams.data["results"]), 1)

    def test_lists_matches_with_filters(self):
        by_season = self.client.get(reverse("match-list"), {"season": self.season.pk})
        by_date = self.client.get(reverse("match-list"), {"date": "2026-08-21"})
        by_team = self.client.get(reverse("match-list"), {"team": self.home_team.pk})

        self.assertEqual(by_season.data["count"], 2)
        self.assertEqual(by_date.data["count"], 1)
        self.assertEqual(by_team.data["count"], 1)
        self.assertEqual(by_team.data["results"][0]["id"], self.match.pk)

    def test_returns_match_detail_statistics_and_odds(self):
        detail = self.client.get(reverse("match-detail", kwargs={"pk": self.match.pk}))
        statistics = self.client.get(reverse("match-statistics", kwargs={"pk": self.match.pk}))
        odds = self.client.get(reverse("match-odds", kwargs={"pk": self.match.pk}))

        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["home_team"]["name"], "Athletic Club")
        self.assertEqual(statistics.status_code, 200)
        self.assertEqual(statistics.data["home_xg"], "1.20")
        self.assertEqual(odds.status_code, 200)
        self.assertEqual(odds.data["results"][0]["odds"], "2.150")

    def test_rejects_invalid_query_parameters(self):
        invalid_date = self.client.get(reverse("match-list"), {"date": "21-08-2026"})
        invalid_season = self.client.get(reverse("match-list"), {"season": 9999})
        invalid_page = self.client.get(reverse("team-list"), {"page": 0})
        unknown_parameter = self.client.get(reverse("season-list"), {"sort": "name"})

        self.assertEqual(invalid_date.status_code, 400)
        self.assertEqual(invalid_season.status_code, 400)
        self.assertEqual(invalid_page.status_code, 400)
        self.assertEqual(unknown_parameter.status_code, 400)

    def test_health_endpoint(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "ok"})

    def test_returns_not_found_for_missing_match_data(self):
        statistics = self.client.get(reverse("match-statistics", kwargs={"pk": self.other_match.pk}))
        odds = self.client.get(reverse("match-odds", kwargs={"pk": 9999}))

        self.assertEqual(statistics.status_code, 404)
        self.assertEqual(odds.status_code, 404)
