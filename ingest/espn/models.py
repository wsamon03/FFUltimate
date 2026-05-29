"""Normalized data models for the ESPN provider."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ingest.base import BaseModel


@dataclass
class NormalizedTeam(BaseModel):
    espn_id: str
    abbr: str
    display_name: str
    home_away: str
    score: int
    team_statistics: list = field(default_factory=list)  # raw ESPN team stat objects


@dataclass
class NormalizedPlayer(BaseModel):
    espn_id: str
    display_name: str
    position_code: str
    team_abbr: str
    category_name: str = ""  # e.g., "Passing", "Rushing"
    raw_category: dict = field(default_factory=dict)  # labels + stats for the specific category


@dataclass
class NormalizedGame(BaseModel):
    espn_id: str
    status_code: str
    game_date: datetime
    home_team: NormalizedTeam
    away_team: NormalizedTeam
    week: int
    season_year: int
    home_players: list[NormalizedPlayer]
    away_players: list[NormalizedPlayer]


@dataclass
class _BoxscoreTeam:
    """Internal model for ESPN boxscore.team data."""
    home_away: str
    team_abbr: str
    team_espn_id: str
    team_display_name: str
    score: int
    statistics: list = field(default_factory=list)


@dataclass
class _BoxscorePlayer:
    """Internal model for ESPN boxscore.player data."""
    espn_id: str
    display_name: str
    position_code: str
    team_abbr: str
    raw_categories: list = field(default_factory=list)
