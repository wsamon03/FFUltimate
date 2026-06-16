"""Auth-gated player and team search endpoints."""

import logging
from typing import Any
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query

from user_api.dependencies import UserContext, get_current_user, get_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["players"])


@router.get("/players")
async def search_players(
    name: str | None = Query(None),
    position: str | None = Query(None),
    team_id: UUID | None = Query(None),
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT player_id AS id, espn_id, name, name AS full_name,
                      position_code AS position, team_abbr AS team_code, team_name
               FROM user_api.fn_search_players($1, $2, $3)""",
            name or None,
            position or None,
            team_id,
        )
    return [dict(r) for r in rows]


@router.get("/players/{player_id}")
async def get_player(
    player_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT player_id AS id, espn_id, name, name AS full_name,
                      position_code AS position, team_abbr AS team_code, team_name
               FROM user_api.fn_get_player($1)""",
            player_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Player not found")
    return dict(row)
