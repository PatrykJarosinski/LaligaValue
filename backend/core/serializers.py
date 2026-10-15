from rest_framework import serializers

from .models import Bookmaker, Match, MatchStatistics, OddsSnapshot, Season, Team


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ["id", "name"]


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name"]


class MatchSerializer(serializers.ModelSerializer):
    season = SeasonSerializer(read_only=True)
    home_team = TeamSerializer(read_only=True)
    away_team = TeamSerializer(read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "season",
            "home_team",
            "away_team",
            "kickoff_at",
            "status",
            "home_score",
            "away_score",
        ]


class MatchStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchStatistics
        fields = [
            "match",
            "home_xg",
            "away_xg",
            "home_shots",
            "away_shots",
            "home_possession",
            "away_possession",
        ]


class BookmakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmaker
        fields = ["id", "name"]


class OddsSnapshotSerializer(serializers.ModelSerializer):
    bookmaker = BookmakerSerializer(read_only=True)

    class Meta:
        model = OddsSnapshot
        fields = ["id", "bookmaker", "market", "selection", "odds", "captured_at"]


class PaginationQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)


class MatchListQuerySerializer(PaginationQuerySerializer):
    season = serializers.PrimaryKeyRelatedField(queryset=Season.objects.all(), required=False)
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), required=False)
    date = serializers.DateField(required=False, input_formats=["%Y-%m-%d"])
