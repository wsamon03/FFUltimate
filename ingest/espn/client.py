"""ESPN HTTP API client."""

import asyncio
import logging
from typing import Optional

import requests

from ingest.base import APIProvider
from ingest.utils.constants import (
    ESPN_SCOREBOARD_URL,
    ESPN_SUMMARY_URL,
    ESPN_HEADERS,
    SEASON_TYPES,
    WEEKS_REGULAR,
    WEEKS_PLAYOFFS,
)

logger = logging.getLogger(__name__)


class ESPNClient(APIProvider):
    """ESPN NFL API client with async and rate-limiting support."""

    @property
    def name(self) -> str:
        return "espn"

    @property
    def rate_limit_delay(self) -> float:
        return 0.5

    async def fetch_scoreboard(self, date: str) -> dict:
        """Fetch scoreboard for a given date (YYYY-MM-DD)."""
        logger.info(f"Fetching scoreboard for date={date}")
        params = {"date": date}
        resp = await asyncio.to_thread(requests.get, ESPN_SCOREBOARD_URL, headers=ESPN_HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    async def fetch_scoreboard_by_week(self, year: str, week: int, type_id: int) -> dict:
        """Fetch scoreboard for a specific season week (dates=year&week=N&type=T)."""
        logger.info(f"Fetching scoreboard for year={year}, week={week}, type={type_id}")
        params = {"dates": year, "week": str(week), "type": str(type_id)}
        resp = await asyncio.to_thread(requests.get, ESPN_SCOREBOARD_URL, headers=ESPN_HEADERS, params=params, timeout=30)
        if resp.status_code in (403, 404):
            logger.debug(f"  Week {week}: API returned {resp.status_code} - skipping")
            return None
        resp.raise_for_status()
        return resp.json()

    async def fetch_game_summary(self, event_id: str) -> Optional[dict]:
        """Fetch full game boxscore summary for a given event ID."""
        logger.debug(f"Fetching game summary for event={event_id}")
        resp = await asyncio.to_thread(requests.get, f"{ESPN_SUMMARY_URL}?event={event_id}", headers=ESPN_HEADERS, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, int):
                logger.debug(f"  Game {event_id}: API returned status code instead of data")
                return None
            return data
        logger.debug(f"  Game {event_id}: HTTP {resp.status_code} - skipping")
        return None

    async def discover_season_games(self, year: str, include_playoffs: bool = False) -> list[str]:
        """Discover all game IDs for a season using historical endpoint."""
        logger.info(f"Discovering games for year={year} (Regular Season)")
        game_ids = set()
        seasons = [(2, "Regular Season")]
        if include_playoffs:
            seasons.append((3, "Playoffs"))
        for type_id, _ in seasons:
            logger.info(f"  Fetching type={type_id} ({SEASON_TYPES[type_id]})")
            max_weeks = WEEKS_REGULAR if type_id == 2 else WEEKS_PLAYOFFS
            for week in range(1, max_weeks + 1):
                sb = await self.fetch_scoreboard_by_week(year, week, type_id)
                if sb:
                    ids = _extract_ids(sb)
                    if ids:
                        game_ids.update(ids)
        return sorted(game_ids)


def _extract_ids(scoreboard) -> list[str]:
    """Extract event IDs from scoreboard with fallback to top-level events."""
    if not scoreboard:
        return []
    ids = []
    if scoreboard.get("events"):
        for event in scoreboard["events"]:
            eid = event.get("id")
            if eid:
                ids.append(str(eid))
        return ids
    for league in scoreboard.get("leagues", []):
        for event in league.get("events", []):
            eid = event.get("id")
            if eid:
                ids.append(str(eid))
    return ids
