"""Leagues, teams, owners, rosters, and weekly lineups."""

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from user_api.dependencies import UserContext, get_current_user, get_pool
from user_api.models.leagues import (
    LeagueCreate,
    LeagueResponse,
    LeagueTeamCreate,
    LeagueTeamRename,
    LeagueTeamResponse,
    LineupPlayerResponse,
    LineupSlot,
    OwnerAdd,
    OwnerResponse,
    OwnerUpdate,
    RosterPlayerAdd,
    RosterPlayerResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/leagues", tags=["leagues"])


# ---------------------------------------------------------------------------
# Leagues
# ---------------------------------------------------------------------------

@router.get("", response_model=list[LeagueResponse])
async def list_leagues(
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_user_leagues($1)", current_user.user_id
        )
    return [LeagueResponse(**dict(r)) for r in rows]


@router.post("", response_model=LeagueResponse, status_code=status.HTTP_201_CREATED)
async def create_league(
    body: LeagueCreate,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        league_id = await conn.fetchval(
            "SELECT user_api.usp_create_league($1, $2)",
            body.name,
            current_user.user_id,
        )
        row = await conn.fetchrow(
            "SELECT id, name, created_by, created_at FROM user_api.leagues WHERE id = $1",
            league_id,
        )
    return LeagueResponse(**dict(row), team_count=0)


@router.get("/{league_id}", response_model=LeagueResponse)
async def get_league(
    league_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_user_leagues($1)", current_user.user_id
        )
    match = next((r for r in rows if r["league_id"] == league_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="League not found")
    return LeagueResponse(**dict(match))


# ---------------------------------------------------------------------------
# League Teams
# ---------------------------------------------------------------------------

@router.get("/{league_id}/teams", response_model=list[LeagueTeamResponse])
async def list_teams(
    league_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_league_teams($1)", league_id
        )
    return [
        LeagueTeamResponse(**dict(r), league_id=league_id)
        for r in rows
    ]


@router.post(
    "/{league_id}/teams",
    response_model=LeagueTeamResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_team(
    league_id: UUID,
    body: LeagueTeamCreate,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        team_id = await conn.fetchval(
            "SELECT user_api.usp_create_league_team($1, $2, $3)",
            league_id,
            current_user.user_id,
            body.name,
        )
        row = await conn.fetchrow(
            "SELECT id, league_id, created_by_id, name, created_at FROM user_api.league_teams WHERE id = $1",
            team_id,
        )
    return LeagueTeamResponse(**dict(row), owner_count=1)


@router.get("/{league_id}/teams/{team_id}", response_model=LeagueTeamResponse)
async def get_team(
    league_id: UUID,
    team_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, league_id, created_by_id, name, created_at FROM user_api.league_teams WHERE id = $1 AND league_id = $2",
            team_id,
            league_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Team not found")
    owner_count = await _owner_count(pool, team_id)
    return LeagueTeamResponse(**dict(row), owner_count=owner_count)


@router.patch("/{league_id}/teams/{team_id}", response_model=LeagueTeamResponse)
async def rename_team(
    league_id: UUID,
    team_id: UUID,
    body: LeagueTeamRename,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE user_api.league_teams
            SET name = $1, updated_at = NOW()
            WHERE id = $2 AND league_id = $3
            RETURNING id, league_id, created_by_id, name, created_at
            """,
            body.name,
            team_id,
            league_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Team not found")
    owner_count = await _owner_count(pool, team_id)
    return LeagueTeamResponse(**dict(row), owner_count=owner_count)


# ---------------------------------------------------------------------------
# Owners
# ---------------------------------------------------------------------------

@router.get("/{league_id}/teams/{team_id}/owners", response_model=list[OwnerResponse])
async def list_owners(
    league_id: UUID,
    team_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_team_owners($1)", team_id
        )
    return [OwnerResponse(**dict(r)) for r in rows]


@router.post(
    "/{league_id}/teams/{team_id}/owners",
    status_code=status.HTTP_201_CREATED,
)
async def add_owner(
    league_id: UUID,
    team_id: UUID,
    body: OwnerAdd,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        await conn.execute(
            "CALL user_api.usp_add_league_team_owner($1, $2, $3, $4, $5)",
            team_id,
            body.user_id,
            body.is_commissioner,
            body.user_display_name,
            body.is_email_displayed,
        )
    return {"status": "success"}


@router.patch("/{league_id}/teams/{team_id}/owners/{user_id}")
async def update_owner(
    league_id: UUID,
    team_id: UUID,
    user_id: UUID,
    body: OwnerUpdate,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT is_commissioner, user_display_name, is_email_displayed FROM user_api.league_team_owners WHERE league_team_id = $1 AND user_id = $2",
            team_id,
            user_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Owner not found")

        new_commissioner = body.is_commissioner if body.is_commissioner is not None else row["is_commissioner"]
        new_display = body.user_display_name if body.user_display_name is not None else row["user_display_name"]
        new_email = body.is_email_displayed if body.is_email_displayed is not None else row["is_email_displayed"]

        await conn.execute(
            """
            UPDATE user_api.league_team_owners
            SET is_commissioner = $1, user_display_name = $2, is_email_displayed = $3
            WHERE league_team_id = $4 AND user_id = $5
            """,
            new_commissioner,
            new_display,
            new_email,
            team_id,
            user_id,
        )
    return {"status": "success"}


@router.delete("/{league_id}/teams/{team_id}/owners/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_owner(
    league_id: UUID,
    team_id: UUID,
    user_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM user_api.league_team_owners WHERE league_team_id = $1 AND user_id = $2",
            team_id,
            user_id,
        )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Owner not found")


# ---------------------------------------------------------------------------
# Roster
# ---------------------------------------------------------------------------

@router.get("/{league_id}/teams/{team_id}/roster", response_model=list[RosterPlayerResponse])
async def get_roster(
    league_id: UUID,
    team_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_team_roster($1)", team_id
        )
    return [RosterPlayerResponse(**dict(r)) for r in rows]


@router.post(
    "/{league_id}/teams/{team_id}/roster",
    response_model=RosterPlayerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_roster_player(
    league_id: UUID,
    team_id: UUID,
    body: RosterPlayerAdd,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO user_api.roster_players (league_team_id, player_id, slot_position)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                team_id,
                body.player_id,
                body.slot_position,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Player already on roster")

        roster_rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_team_roster($1)", team_id
        )
    match = next((r for r in roster_rows if r["player_id"] == body.player_id), None)
    if not match:
        raise HTTPException(status_code=500, detail="Roster insert failed")
    return RosterPlayerResponse(**dict(match))


@router.delete("/{league_id}/teams/{team_id}/roster/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def drop_roster_player(
    league_id: UUID,
    team_id: UUID,
    player_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM user_api.roster_players WHERE league_team_id = $1 AND player_id = $2",
            team_id,
            player_id,
        )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Player not on roster")


# ---------------------------------------------------------------------------
# Weekly Lineup
# ---------------------------------------------------------------------------

@router.get(
    "/{league_id}/teams/{team_id}/lineup/{season}/{week}",
    response_model=list[LineupPlayerResponse],
)
async def get_lineup(
    league_id: UUID,
    team_id: UUID,
    season: int,
    week: int,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_team_lineup($1, $2, $3)",
            team_id,
            season,
            week,
        )
    return [LineupPlayerResponse(**dict(r)) for r in rows]


@router.put(
    "/{league_id}/teams/{team_id}/lineup/{season}/{week}",
    response_model=list[LineupPlayerResponse],
)
async def set_lineup(
    league_id: UUID,
    team_id: UUID,
    season: int,
    week: int,
    slots: list[LineupSlot],
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Replace the entire lineup for this week
            await conn.execute(
                "DELETE FROM user_api.weekly_lineups WHERE league_team_id = $1 AND season_year = $2 AND week = $3",
                team_id,
                season,
                week,
            )
            for slot in slots:
                await conn.execute(
                    """
                    INSERT INTO user_api.weekly_lineups (league_team_id, player_id, season_year, week, slot_position)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    team_id,
                    slot.player_id,
                    season,
                    week,
                    slot.slot_position,
                )
            rows = await conn.fetch(
                "SELECT * FROM user_api.fn_get_team_lineup($1, $2, $3)",
                team_id,
                season,
                week,
            )
    return [LineupPlayerResponse(**dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _owner_count(pool: asyncpg.Pool, team_id: UUID) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM user_api.league_team_owners WHERE league_team_id = $1 AND is_active = TRUE",
            team_id,
        )
