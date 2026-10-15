from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework import generics

from .models import Match, MatchStatistics, OddsSnapshot, Season, Team
from .pagination import StandardPagination
from .serializers import (
    MatchListQuerySerializer,
    MatchSerializer,
    MatchStatisticsSerializer,
    OddsSnapshotSerializer,
    PaginationQuerySerializer,
    SeasonSerializer,
    TeamSerializer,
)


class ValidatedQueryParametersMixin:
    query_serializer_class = PaginationQuerySerializer

    def get_validated_query_params(self):
        serializer = self.query_serializer_class(data=self.request.query_params)
        unknown_parameters = set(self.request.query_params) - set(serializer.fields)
        if unknown_parameters:
            names = ", ".join(sorted(unknown_parameters))
            raise ValidationError({"query_params": [f"Unsupported parameter(s): {names}"]})
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


class SeasonListAPIView(ValidatedQueryParametersMixin, generics.ListAPIView):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        self.get_validated_query_params()
        return super().get_queryset()


class TeamListAPIView(ValidatedQueryParametersMixin, generics.ListAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        self.get_validated_query_params()
        return super().get_queryset()


class MatchListAPIView(ValidatedQueryParametersMixin, generics.ListAPIView):
    serializer_class = MatchSerializer
    pagination_class = StandardPagination
    query_serializer_class = MatchListQuerySerializer

    def get_queryset(self):
        params = self.get_validated_query_params()
        queryset = Match.objects.select_related("season", "home_team", "away_team")

        if season := params.get("season"):
            queryset = queryset.filter(season=season)
        if date := params.get("date"):
            queryset = queryset.filter(kickoff_at__date=date)
        if team := params.get("team"):
            queryset = queryset.filter(Q(home_team=team) | Q(away_team=team))

        return queryset


class MatchDetailAPIView(generics.RetrieveAPIView):
    queryset = Match.objects.select_related("season", "home_team", "away_team")
    serializer_class = MatchSerializer


class MatchStatisticsDetailAPIView(generics.RetrieveAPIView):
    serializer_class = MatchStatisticsSerializer

    def get_object(self):
        return get_object_or_404(
            MatchStatistics.objects.select_related("match"),
            match_id=self.kwargs["pk"],
        )


class MatchOddsListAPIView(ValidatedQueryParametersMixin, generics.ListAPIView):
    serializer_class = OddsSnapshotSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        self.get_validated_query_params()
        get_object_or_404(Match, pk=self.kwargs["pk"])
        return OddsSnapshot.objects.filter(match_id=self.kwargs["pk"]).select_related("bookmaker")
