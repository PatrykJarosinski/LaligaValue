from django.urls import path

from .views import (
    MatchDetailAPIView,
    MatchListAPIView,
    MatchOddsListAPIView,
    MatchStatisticsDetailAPIView,
    SeasonListAPIView,
    TeamListAPIView,
)

urlpatterns = [
    path("seasons/", SeasonListAPIView.as_view(), name="season-list"),
    path("teams/", TeamListAPIView.as_view(), name="team-list"),
    path("matches/", MatchListAPIView.as_view(), name="match-list"),
    path("matches/<int:pk>/", MatchDetailAPIView.as_view(), name="match-detail"),
    path("matches/<int:pk>/statistics/", MatchStatisticsDetailAPIView.as_view(), name="match-statistics"),
    path("matches/<int:pk>/odds/", MatchOddsListAPIView.as_view(), name="match-odds"),
]
