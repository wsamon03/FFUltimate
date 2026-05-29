"""Abstract interfaces for the NFL ingestion system."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class APIProvider(ABC):
    """Interface for any sports data API provider."""

    @abstractmethod
    async def fetch_scoreboard(self, date: str) -> dict:
        """Fetch scoreboard for a given date (YYYY-MM-DD). Returns raw provider JSON."""

    @abstractmethod
    async def fetch_scoreboard_by_week(self, year: str, week: int, type_id: int) -> dict:
        """Fetch scoreboard for a specific season week. Returns raw provider JSON."""

    @abstractmethod
    async def fetch_game_summary(self, event_id: str) -> dict:
        """Fetch full game boxscore summary. Returns raw provider JSON."""

    @abstractmethod
    async def discover_season_games(self, year: str, include_playoffs: bool = False) -> list[str]:
        """Discover all game IDs for a season. Returns sorted list of event IDs."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'espn')."""

    @property
    def rate_limit_delay(self) -> float:
        """Seconds to wait between API requests."""
        return 0.5


class BaseModel(ABC):
    """Base model for normalized data from any provider."""


class Transformer(ABC):
    """Transform normalized BaseModel into DB-ready stat dictionaries."""

    @abstractmethod
    def transform_team_stats(self, team_model: BaseModel) -> dict:
        """Return dict of stat name -> parsed value."""

    @abstractmethod
    def transform_player_stats(self, player_model: BaseModel) -> dict:
        """Return dict of stat name -> parsed value."""


class DBWriter(ABC):
    """Write ingested data to database via stored procedures."""

    @abstractmethod
    def upsert_team(self, espn_id: str, abbr: str, full_name: str) -> UUID:
        ...

    @abstractmethod
    def upsert_player(self, espn_id: str, name: str, position_code: str, team_id: UUID) -> UUID:
        ...

    @abstractmethod
    def upsert_game(self, espn_id: str, status_code: str, game_date: datetime,
                    home_espn_id: str, away_espn_id: str, week: int, season_year: int) -> UUID:
        ...

    @abstractmethod
    def upsert_team_game_stats(self, game_id: UUID, team_id: UUID, stats: dict) -> None:
        ...

    @abstractmethod
    def upsert_player_game_stats(self, player_id: UUID, game_id: UUID, stats: dict) -> None:
        ...
