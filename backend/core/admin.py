from django.contrib import admin

from .models import Bookmaker, Match, MatchStatistics, OddsSnapshot, Prediction, Season, Team


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("id", "season", "home_team", "away_team", "kickoff_at", "status", "home_score", "away_score")
    list_filter = ("season", "status", "kickoff_at")
    search_fields = ("home_team__name", "away_team__name")
    autocomplete_fields = ("season", "home_team", "away_team")
    date_hierarchy = "kickoff_at"
    list_select_related = ("season", "home_team", "away_team")


@admin.register(MatchStatistics)
class MatchStatisticsAdmin(admin.ModelAdmin):
    list_display = ("match", "home_xg", "away_xg", "home_shots", "away_shots", "home_possession", "away_possession")
    search_fields = ("match__home_team__name", "match__away_team__name")
    autocomplete_fields = ("match",)
    list_select_related = ("match", "match__home_team", "match__away_team")


@admin.register(Bookmaker)
class BookmakerAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(OddsSnapshot)
class OddsSnapshotAdmin(admin.ModelAdmin):
    list_display = ("match", "bookmaker", "market", "selection", "odds", "captured_at")
    list_filter = ("bookmaker", "market", "captured_at")
    search_fields = ("match__home_team__name", "match__away_team__name", "bookmaker__name", "market", "selection")
    autocomplete_fields = ("match", "bookmaker")
    date_hierarchy = "captured_at"
    list_select_related = ("match", "match__home_team", "match__away_team", "bookmaker")


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("match", "market", "selection", "probability", "model_version", "generated_at")
    list_filter = ("model_version", "market", "generated_at")
    search_fields = ("match__home_team__name", "match__away_team__name", "market", "selection", "model_version")
    autocomplete_fields = ("match",)
    date_hierarchy = "generated_at"
    list_select_related = ("match", "match__home_team", "match__away_team")
