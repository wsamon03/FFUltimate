"""Async DB writer that calls stored procedures via asyncpg."""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)


class PgDBWriter:
    """PostgreSQL DB writer using asyncpg."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def seed_lookup_tables(self) -> None:
        """Seed the game_status and player_position lookup tables."""
        async with self.pool.acquire() as conn:
            await conn.execute("CALL usp_seed_game_status()")
            await conn.execute("CALL usp_seed_player_position()")
            await conn.commit()  # explicit commit for CALL if needed

    async def upsert_team(self, espn_id: str, abbr: str, full_name: str) -> uuid.UUID:
        """Upsert team keyed by stable abbr; add espn_id to game_team_espn_ids[]."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "CALL usp_upsert_team($1, $2, $3, $4)",
                espn_id, abbr, full_name, espn_id
            )
            
            # Retrieve the UUID
            row = await conn.fetchval(
                "SELECT id FROM teams WHERE abbr = $1", 
                abbr
            )
            if not row:
                raise RuntimeError(f"Team {abbr} was upserted but not found")
            return row # asyncpg returns UUID directly

    async def upsert_player(self, espn_id: str, name: str, position_code: str, team_id: uuid.UUID) -> uuid.UUID:
        """Upsert player and return its internal UUID."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "CALL usp_upsert_player($1, $2, $3, $4)",
                espn_id, name, position_code, team_id
            )
            row = await conn.fetchval(
                "SELECT id FROM players WHERE espn_id = $1",
                espn_id
            )
            if not row:
                raise RuntimeError(f"Player {espn_id} was upserted but not found")
            return row

    async def upsert_game(
        self, 
        espn_id: str, 
        status_code: str, 
        game_date: datetime,
        home_espn_id: str, 
        away_espn_id: str, 
        week: int, 
        season_year: int
    ) -> uuid.UUID:
        """Upsert game via stored procedure (procedure resolves team UUIDs internally)."""
        # Strip timezone info so psycopg2 passes TIMESTAMP not TIMESTAMPTZ
        if game_date and game_date.tzinfo is not None:
            game_date = game_date.replace(tzinfo=None)
            
        async with self.pool.acquire() as conn:
            await conn.execute(
                "CALL usp_upsert_game($1, $2, $3, $4, $5, $6, $7)",
                espn_id, status_code, game_date,
                home_espn_id, away_espn_id, week, season_year
            )
            row = await conn.fetchval(
                "SELECT id FROM games WHERE espn_id = $1",
                espn_id
            )
            if not row:
                raise RuntimeError(f"Game {espn_id} was upserted but not found")
            return row

    async def upsert_team_game_stats(self, game_id: uuid.UUID, team_id: uuid.UUID, stats: dict) -> None:
        """Upsert team game stats via stored procedure."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "CALL usp_upsert_team_game_stats($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28)",
                game_id, team_id,
                stats.get("pts_total"), stats.get("pts_q1"), stats.get("pts_q2"),
                stats.get("pts_q3"), stats.get("pts_q4"), stats.get("pts_ot"),
                stats.get("td_pass"), stats.get("td_rush"), stats.get("td_ret"), stats.get("td_def"),
                stats.get("off_first_downs"), stats.get("off_total_yds"), stats.get("off_plays"),
                stats.get("off_3rd_att"), stats.get("off_3rd_make"),
                stats.get("off_redzone_att"), stats.get("off_redzone_td"),
                stats.get("off_possession_secs"),
                stats.get("def_sacks"), stats.get("def_int"),
                stats.get("total_turnovers"),
                stats.get("penalties_count"), stats.get("penalties_yds"),
                json.dumps(stats.get("metadata", {})) if stats.get("metadata") else None
            )

    async def upsert_player_game_stats(self, player_id: uuid.UUID, game_id: uuid.UUID, stats: dict) -> None:
        """Upsert player game stats via stored procedure."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "CALL usp_upsert_player_game_stats($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36, $37, $38, $39)",
                player_id, game_id,
                stats.get("pass_comp"), stats.get("pass_att"), stats.get("pass_yds"),
                stats.get("pass_td"), stats.get("pass_int"), stats.get("pass_sacked"),
                stats.get("rush_att"), stats.get("rush_yds"), stats.get("rush_td"),
                stats.get("rec_receptions"), stats.get("rec_targets"), stats.get("rec_yds"),
                stats.get("rec_td"),
                stats.get("def_solo"), stats.get("def_ast"), stats.get("def_sacks"),
                stats.get("def_tfl"), stats.get("def_pd"), stats.get("def_qb_hits"),
                stats.get("def_td"), stats.get("def_int"),
                stats.get("ret_kick_no"), stats.get("ret_kick_yds"), stats.get("ret_kick_td"),
                stats.get("ret_punt_no"), stats.get("ret_punt_yds"), stats.get("ret_punt_td"),
                stats.get("k_fg_make"), stats.get("k_fg_att"),
                stats.get("k_xp_make"), stats.get("k_xp_att"),
                stats.get("p_no"), stats.get("p_yds"), stats.get("p_in20"),
                stats.get("p_tb"), stats.get("p_fc"), stats.get("p_blk"), stats.get("p_long"),
                json.dumps(stats.get("metadata", {})) if stats.get("metadata") else None
            )
