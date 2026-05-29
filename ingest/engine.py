"""Pipeline orchestration for NFL data ingestion."""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

import asyncpg
from ingest.base import APIProvider, Transformer, DBWriter

logger = logging.getLogger(__name__)


class IngestionEngine:
    """Pipeline that orchestrates API -> parse -> transform -> write."""

    def __init__(
        self,
        api_provider: APIProvider,
        transformer: Transformer,
        db_writer: DBWriter,
        pool: asyncpg.Pool,
    ):
        self.api = api_provider
        self.transformer = transformer
        self.db_writer = db_writer
        self.pool = pool

    async def process_game(self, event_id: str) -> Optional[uuid.UUID]:
        """Ingest a single game: fetch, normalize, upsert."""
        logger.info(f"Processing game: {event_id}")
        raw = await self.api.fetch_game_summary(event_id)
        if not raw:
            logger.warning(f"No data for game {event_id}")
            return None

        parsed_game = self._normalize_boxscore(raw)
        if not parsed_game:
            return None

        # Transaction handling: Ensures data integrity for the entire game record
        game_id = None
        try:
            async with self.pool.transaction():
                # Upsert home team
                home_id = await self.db_writer.upsert_team(
                    parsed_game.home_team.espn_id,
                    parsed_game.home_team.abbr,
                    parsed_game.home_team.display_name,
                )
                # Upsert away team
                away_id = await self.db_writer.upsert_team(
                    parsed_game.away_team.espn_id,
                    parsed_game.away_team.abbr,
                    parsed_game.away_team.display_name,
                )

                # Upsert game (procedure resolves team UUIDs internally)
                game_id = await self.db_writer.upsert_game(
                    espn_id=parsed_game.espn_id,
                    status_code=parsed_game.status_code,
                    game_date=parsed_game.game_date,
                    home_espn_id=parsed_game.home_team.espn_id,
                    away_espn_id=parsed_game.away_team.espn_id,
                    week=parsed_game.week,
                    season_year=parsed_game.season_year,
                )

                # Upsert team stats
                home_stats = self.transformer.transform_team_stats(parsed_game.home_team)
                await self.db_writer.upsert_team_game_stats(game_id, home_id, home_stats)

                away_stats = self.transformer.transform_team_stats(parsed_game.away_team)
                await self.db_writer.upsert_team_game_stats(game_id, away_id, away_stats)

                # Upsert players and player stats
                for player in parsed_game.home_players + parsed_game.away_players:
                    if not player.espn_id or not player.display_name:
                        continue
                    player_id = await self.db_writer.upsert_player(
                        player.espn_id, player.display_name, player.position_code,
                        home_id if player.team_abbr == parsed_game.home_team.abbr else away_id,
                    )
                    player_stats = self.transformer.transform_player_stats(player)
                    # Only insert if player has any stats
                    non_null = {k: v for k, v in player_stats.items() if k != "metadata" and v is not None}
                    if non_null:
                        await self.db_writer.upsert_player_game_stats(player_id, game_id, player_stats)
                        
        except Exception as e:
            logger.error(f"Transaction failed for game {event_id}: {e}")
            raise

        logger.info(f"Completed game {event_id} -> DB game_id={game_id}")
        return game_id

    async def process_game_ids(self, event_ids: list[str]) -> tuple[int, int]:
        """Ingest multiple games with rate limiting."""
        processed, failed = 0, 0
        for event_id in event_ids:
            try:
                result = await self.process_game(event_id)
                if result:
                    processed += 1
                    logger.info(f"Success: {event_id}")
                else:
                    failed += 1
                    logger.warning(f"Failed to parse: {event_id}")
            except Exception as e:
                logger.error(f"Error processing game {event_id}: {e}")
                failed += 1
            await asyncio.sleep(self.api.rate_limit_delay)
        logger.info(f"Ingestion complete: {processed} succeeded, {failed} failed")
        return processed, failed

    async def process_week(self, year: str, week: int, type_id: int = 2) -> tuple[int, int]:
        """Ingest all games for a season week."""
        raw = await self.api.fetch_scoreboard_by_week(year, week, type_id)
        if not raw:
            logger.info(f"No games for week {week}, year {year}")
            return 0, 0
        event_ids = _extract_ids(raw)
        return await self.process_game_ids(event_ids)

    async def process_season(self, year: str, include_playoffs: bool = False) -> tuple[int, int]:
        """Ingest entire season."""
        event_ids = await self.api.discover_season_games(year, include_playoffs)
        return await self.process_game_ids(event_ids)

    def _normalize_boxscore(self, raw: dict):
        """Normalize raw ESPN API response to internal model."""
        from ingest.espn.parsers import parse_summary
        return parse_summary(raw)


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
