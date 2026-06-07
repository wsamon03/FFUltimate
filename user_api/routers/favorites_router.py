"""Favorites — bookmark NFL players and teams per user."""

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from user_api.dependencies import UserContext, get_current_user, get_pool
from user_api.models.favorites import FavoritePlayerAdd, FavoriteResponse, FavoriteTeamAdd

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("", response_model=list[FavoriteResponse])
async def list_favorites(
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_user_favorites($1)", current_user.user_id
        )
    return [FavoriteResponse(**dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------

@router.post("/players", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_player_favorite(
    body: FavoritePlayerAdd,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO user_api.favorites (user_id, player_id) VALUES ($1, $2)",
                current_user.user_id,
                body.player_id,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Player already favorited")

        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_user_favorites($1)", current_user.user_id
        )
    match = next((r for r in rows if r["kind"] == "player" and r["target_id"] == body.player_id), None)
    if not match:
        raise HTTPException(status_code=500, detail="Favorite insert failed")
    return FavoriteResponse(**dict(match))


@router.delete("/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_player_favorite(
    player_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM user_api.favorites WHERE user_id = $1 AND player_id = $2",
            current_user.user_id,
            player_id,
        )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Favorite not found")


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

@router.post("/teams", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_team_favorite(
    body: FavoriteTeamAdd,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO user_api.favorites (user_id, team_id) VALUES ($1, $2)",
                current_user.user_id,
                body.team_id,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Team already favorited")

        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_user_favorites($1)", current_user.user_id
        )
    match = next((r for r in rows if r["kind"] == "team" and r["target_id"] == body.team_id), None)
    if not match:
        raise HTTPException(status_code=500, detail="Favorite insert failed")
    return FavoriteResponse(**dict(match))


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_favorite(
    team_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM user_api.favorites WHERE user_id = $1 AND team_id = $2",
            current_user.user_id,
            team_id,
        )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Favorite not found")
