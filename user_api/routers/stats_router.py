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
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM fn_get_game_both_teams($1)", game_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"game_id": game_id, "teams": [dict(r) for r in rows]}


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
    fn_map = {
        "passing": "fn_get_game_passing_leaders",
        "rushing": "fn_get_game_rushing_leaders",
        "receiving": "fn_get_game_receiving_leaders",
    }
    fn_name = fn_map.get(category)
    if not fn_name:
        raise HTTPException(status_code=400, detail="category must be passing, rushing, or receiving")
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"SELECT * FROM {fn_name}($1)", game_id)
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
