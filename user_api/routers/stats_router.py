"""Auth-gated NFL stats endpoints — mirrors the ingest service retrieval router."""

import logging
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query

from user_api.dependencies import UserContext, get_current_user, get_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/teams")
async def get_teams(
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM fn_get_all_teams()")
    return [dict(r) for r in rows]


@router.get("/games")
async def get_games(
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    season: int | None = Query(None),
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        if date_start and date_end:
            rows = await conn.fetch(
                "SELECT * FROM fn_get_games_by_date_range($1::date, $2::date)",
                date_start,
                date_end,
            )
        elif season:
            rows = await conn.fetch(
                "SELECT * FROM fn_get_games_by_season($1)", season
            )
        else:
            rows = await conn.fetch("SELECT * FROM fn_get_all_games()")
    return [dict(r) for r in rows]


@router.get("/game/{game_id}")
async def get_game(
    game_id: str,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT g.id, g.status_code, g.game_date, g.season_year, g.week,
                       g.home_score, g.away_score, g.home_team_id, g.away_team_id,
                       t_home.abbr AS home_team_abbr, t_away.abbr AS away_team_abbr
                FROM games g
                JOIN teams t_home ON g.home_team_id = t_home.id
                JOIN teams t_away ON g.away_team_id = t_away.id
                WHERE g.id = $1::uuid
                """,
                game_id
            )
        if not rows:
            raise HTTPException(status_code=404, detail="Game not found")
        return dict(rows[0])
    except Exception as e:
        logger.error(f"Error fetching game {game_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/player/{player_id}")
async def get_player_stats(
    player_id: str,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM fn_get_player_career_complete($1)", player_id)
    return [dict(r) for r in rows]


@router.get("/team/{team_id}")
async def get_team_stats(
    team_id: str,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM fn_get_team_season_complete($1)", team_id)
    return [dict(r) for r in rows]


@router.get("/leaderboard/{game_id}")
async def get_leaderboard(
    game_id: str,
    category: str = Query("passing", description="passing | rushing | receiving"),
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    # Exact column mapping — these names MUST match what fn_get_game_*_leaders returns!
    alias_map = {
        "passing": ["player_id", "player_espn_id", "player_name", "position_code",
                     "team_name AS team_nm", "game_espn_id", "game_date",
                     "pass_comp", "pass_att", "pass_yds AS pass_yards",
                     "pass_td AS pass_tds", "pass_int AS interceptions", "pass_sacked",
                     "ypc", "pct", "btr"],
        "rushing": ["player_id", "player_espn_id", "player_name", "position_code",
                     "team_name AS team_nm", "game_espn_id", "game_date",
                     "rush_att AS rush_attempts", "rush_yds AS rush_yards",
                     "rush_td AS rush_tds", "ypc"],
        "receiving": ["player_id", "player_espn_id", "player_name", "position_code",
                       "team_name AS team_nm", "game_espn_id", "game_date",
                       "rec_receptions AS receptions", "rec_targets",
                       "rec_yds AS rec_yards", "rec_td AS rec_tds",
                       "ypr", "rtc"]
    }

    fn_map = {
        "passing": "fn_get_game_passing_leaders",
        "rushing": "fn_get_game_rushing_leaders",
        "receiving": "fn_get_game_receiving_leaders",
    }

    fn_name = fn_map.get(category)
    if not fn_name:
        raise HTTPException(status_code=400, detail="category must be passing, rushing, or receiving")

    columns_str = ",".join(alias_map[category])
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"SELECT {columns_str} FROM {fn_name}($1::uuid)", game_id)

    return [dict(r) for r in rows]


@router.get("/fantasy/{player_id}")
async def get_fantasy_stats(
    player_id: str,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM fn_get_player_fantasy_stats($1)", player_id)
    return [dict(r) for r in rows]
