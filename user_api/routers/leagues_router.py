"""Leagues, teams, owners, rosters, and weekly lineups."""

import logging
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from user_api.dependencies import UserContext, get_current_user, get_pool
from user_api.models.leagues import (
    DraftPickCreate,
    DraftPickResponse,
    LeagueCreate,
    LeagueDraftSettings,
    LeagueKeeperSettings,
    LeaguePlayoffSettings,
    LeagueResponse,
    LeagueRosterConfig,
    LeagueScoringSettings,
    LeagueSettingsResponse,
    LeagueSettingsUpdate,
    LeagueTeamCreate,
    LeagueTeamRename,
    LeagueTeamResponse,
    LeagueTradeSettings,
    LeagueWaiverSettings,
    LineupPlayerResponse,
    LineupSlot,
    MatchupCreate,
    MatchupResponse,
    MatchupUpdate,
    OwnerAdd,
    OwnerResponse,
    OwnerUpdate,
    RosterPlayerAdd,
    RosterPlayerResponse,
    StandingsEntry,
    TeamBrandingUpdate,
    TeamSeasonStatsResponse,
    TeamSeasonStatsUpdate,
    TransactionCreate,
    TransactionResponse,
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
            "SELECT user_api.usp_create_league($1, $2, $3, $4, $5, $6, $7)",
            body.name,
            current_user.user_id,
            body.description,
            body.league_type_id,
            body.available_scope_id,
            body.season_year,
            body.max_teams,
        )
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_user_leagues($1)", current_user.user_id
        )
    match = next((r for r in rows if r["id"] == league_id), None)
    if not match:
        raise HTTPException(status_code=500, detail="League creation failed")
    return LeagueResponse(**dict(match))


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
    match = next((r for r in rows if r["id"] == league_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="League not found")
    return LeagueResponse(**dict(match))


# ---------------------------------------------------------------------------
# League Settings
# ---------------------------------------------------------------------------

@router.get("/{league_id}/settings", response_model=LeagueSettingsResponse)
async def get_league_settings(
    league_id: UUID,
    year: int | None = None,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        # Resolve year: use provided year, or fall back to the league's season_year
        if year is None:
            league_year = await conn.fetchval(
                "SELECT season_year FROM user_api.leagues WHERE id = $1", league_id
            )
            if league_year is None:
                raise HTTPException(status_code=404, detail="League not found")
            year = league_year

        scoring_row = await conn.fetchrow(
            "SELECT fractional_scoring, median_game FROM user_api.league_scoring WHERE league_id = $1 AND league_year = $2",
            league_id, year,
        )
        roster_row = await conn.fetchrow(
            "SELECT * FROM user_api.league_roster_config WHERE league_id = $1 AND league_year = $2",
            league_id, year,
        )
        draft_row = await conn.fetchrow(
            "SELECT draft_type_id, draft_date, seconds_per_pick, autopick_enabled, third_round_reversal FROM user_api.league_draft_settings WHERE league_id = $1 AND league_year = $2",
            league_id, year,
        )
        waiver_row = await conn.fetchrow(
            "SELECT waiver_type_id, faab_budget, waiver_days, waiver_process_day, max_acquisitions FROM user_api.league_waiver_settings WHERE league_id = $1 AND league_year = $2",
            league_id, year,
        )
        trade_row = await conn.fetchrow(
            "SELECT deadline_week, review_days, veto_votes_required, allow_future_picks FROM user_api.league_trade_settings WHERE league_id = $1 AND league_year = $2",
            league_id, year,
        )
        playoff_row = await conn.fetchrow(
            "SELECT playoff_teams, start_week, end_week, consolation_bracket, seeding_id FROM user_api.league_playoff_settings WHERE league_id = $1 AND league_year = $2",
            league_id, year,
        )
        keeper_row = await conn.fetchrow(
            "SELECT keeper_count, cost_type_id, taxi_squad_size FROM user_api.league_keeper_settings WHERE league_id = $1 AND league_year = $2",
            league_id, year,
        )

    return LeagueSettingsResponse(
        league_year=year,
        scoring=LeagueScoringSettings(**(dict(scoring_row) if scoring_row else {})),
        roster=LeagueRosterConfig(**(dict(roster_row) if roster_row else {})),
        draft=LeagueDraftSettings(**(dict(draft_row) if draft_row else {})),
        waivers=LeagueWaiverSettings(**(dict(waiver_row) if waiver_row else {})),
        trades=LeagueTradeSettings(**(dict(trade_row) if trade_row else {})),
        playoffs=LeaguePlayoffSettings(**(dict(playoff_row) if playoff_row else {})),
        keeper=LeagueKeeperSettings(**(dict(keeper_row) if keeper_row else {})),
    )


@router.patch("/{league_id}/settings", response_model=LeagueSettingsResponse)
async def update_league_settings(
    league_id: UUID,
    body: LeagueSettingsUpdate,
    year: int | None = None,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        # Verify current user is a commissioner of any team in this league
        is_commissioner = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM user_api.league_team_owners lto
                JOIN user_api.league_teams lt ON lt.id = lto.league_team_id
                WHERE lt.league_id = $1
                  AND lto.user_id = $2
                  AND lto.is_commissioner = TRUE
                  AND lto.is_active = TRUE
            )
            """,
            league_id, current_user.user_id,
        )
        if not is_commissioner:
            raise HTTPException(status_code=403, detail="Commissioner access required")

        if year is None:
            year = await conn.fetchval(
                "SELECT season_year FROM user_api.leagues WHERE id = $1", league_id
            )
            if year is None:
                raise HTTPException(status_code=404, detail="League not found")

        async with conn.transaction():
            if body.scoring is not None:
                await conn.execute(
                    """
                    INSERT INTO user_api.league_scoring (league_id, league_year, fractional_scoring, median_game)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (league_id, league_year) DO UPDATE
                        SET fractional_scoring = EXCLUDED.fractional_scoring,
                            median_game = EXCLUDED.median_game
                    """,
                    league_id, year, body.scoring.fractional_scoring, body.scoring.median_game,
                )

            if body.roster is not None:
                r = body.roster
                await conn.execute(
                    """
                    INSERT INTO user_api.league_roster_config
                        (league_id, league_year, qb, rb, wr, te, flex, superflex, k, dst, bench, ir,
                         idp_dl, idp_dt, idp_edge, idp_lb, idp_ilb, idp_db, idp_cb, idp_s)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20)
                    ON CONFLICT (league_id, league_year) DO UPDATE
                        SET qb=$3, rb=$4, wr=$5, te=$6, flex=$7, superflex=$8, k=$9, dst=$10,
                            bench=$11, ir=$12, idp_dl=$13, idp_dt=$14, idp_edge=$15, idp_lb=$16,
                            idp_ilb=$17, idp_db=$18, idp_cb=$19, idp_s=$20
                    """,
                    league_id, year, r.qb, r.rb, r.wr, r.te, r.flex, r.superflex,
                    r.k, r.dst, r.bench, r.ir,
                    r.idp_dl, r.idp_dt, r.idp_edge, r.idp_lb, r.idp_ilb, r.idp_db, r.idp_cb, r.idp_s,
                )

            if body.draft is not None:
                d = body.draft
                await conn.execute(
                    """
                    INSERT INTO user_api.league_draft_settings
                        (league_id, league_year, draft_type_id, draft_date, seconds_per_pick, autopick_enabled, third_round_reversal)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                    ON CONFLICT (league_id, league_year) DO UPDATE
                        SET draft_type_id=$3, draft_date=$4, seconds_per_pick=$5,
                            autopick_enabled=$6, third_round_reversal=$7
                    """,
                    league_id, year, d.draft_type_id, d.draft_date,
                    d.seconds_per_pick, d.autopick_enabled, d.third_round_reversal,
                )

            if body.waivers is not None:
                w = body.waivers
                await conn.execute(
                    """
                    INSERT INTO user_api.league_waiver_settings
                        (league_id, league_year, waiver_type_id, faab_budget, waiver_days, waiver_process_day, max_acquisitions)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                    ON CONFLICT (league_id, league_year) DO UPDATE
                        SET waiver_type_id=$3, faab_budget=$4, waiver_days=$5,
                            waiver_process_day=$6, max_acquisitions=$7
                    """,
                    league_id, year, w.waiver_type_id, w.faab_budget,
                    w.waiver_days, w.waiver_process_day, w.max_acquisitions,
                )

            if body.trades is not None:
                t = body.trades
                await conn.execute(
                    """
                    INSERT INTO user_api.league_trade_settings
                        (league_id, league_year, deadline_week, review_days, veto_votes_required, allow_future_picks)
                    VALUES ($1,$2,$3,$4,$5,$6)
                    ON CONFLICT (league_id, league_year) DO UPDATE
                        SET deadline_week=$3, review_days=$4,
                            veto_votes_required=$5, allow_future_picks=$6
                    """,
                    league_id, year, t.deadline_week, t.review_days,
                    t.veto_votes_required, t.allow_future_picks,
                )

            if body.playoffs is not None:
                p = body.playoffs
                await conn.execute(
                    """
                    INSERT INTO user_api.league_playoff_settings
                        (league_id, league_year, playoff_teams, start_week, end_week, consolation_bracket, seeding_id)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                    ON CONFLICT (league_id, league_year) DO UPDATE
                        SET playoff_teams=$3, start_week=$4, end_week=$5,
                            consolation_bracket=$6, seeding_id=$7
                    """,
                    league_id, year, p.playoff_teams, p.start_week,
                    p.end_week, p.consolation_bracket, p.seeding_id,
                )

            if body.keeper is not None:
                k = body.keeper
                await conn.execute(
                    """
                    INSERT INTO user_api.league_keeper_settings
                        (league_id, league_year, keeper_count, cost_type_id, taxi_squad_size)
                    VALUES ($1,$2,$3,$4,$5)
                    ON CONFLICT (league_id, league_year) DO UPDATE
                        SET keeper_count=$3, cost_type_id=$4, taxi_squad_size=$5
                    """,
                    league_id, year, k.keeper_count, k.cost_type_id, k.taxi_squad_size,
                )

    # Return the full updated settings
    return await get_league_settings(league_id, year, current_user, pool)


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
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_league_teams($1)", league_id
        )
    match = next((r for r in rows if r["id"] == team_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Team not found")
    return LeagueTeamResponse(**dict(match), league_id=league_id)


@router.patch("/{league_id}/teams/{team_id}", response_model=LeagueTeamResponse)
async def rename_team(
    league_id: UUID,
    team_id: UUID,
    body: LeagueTeamRename,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        await conn.execute(
            "CALL user_api.usp_rename_team($1, $2, $3)",
            body.name,
            team_id,
            league_id,
        )
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_league_teams($1)", league_id
        )
    match = next((r for r in rows if r["id"] == team_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Team not found")
    return LeagueTeamResponse(**dict(match), league_id=league_id)


@router.patch("/{league_id}/teams/{team_id}/branding", response_model=LeagueTeamResponse)
async def update_team_branding(
    league_id: UUID,
    team_id: UUID,
    body: TeamBrandingUpdate,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "CALL user_api.usp_update_team_branding($1,$2,$3,$4,$5,$6,$7,$8)",
                team_id, league_id,
                body.abbreviation, body.logo_url, body.slogan,
                body.primary_color, body.secondary_color_1, body.secondary_color_2,
            )
        except asyncpg.RaiseError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_league_teams($1)", league_id
        )
    match = next((r for r in rows if r["id"] == team_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Team not found")
    return LeagueTeamResponse(**dict(match), league_id=league_id)


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
            await conn.fetchrow(
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
# Standings
# ---------------------------------------------------------------------------

@router.get("/{league_id}/standings", response_model=list[StandingsEntry])
async def get_standings(
    league_id: UUID,
    year: int | None = None,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        if year is None:
            year = await conn.fetchval(
                "SELECT season_year FROM user_api.leagues WHERE id = $1", league_id
            )
            if year is None:
                raise HTTPException(status_code=404, detail="League not found")
        rows = await conn.fetch(
            "SELECT * FROM user_api.fn_get_league_standings($1, $2)", league_id, year
        )
    return [StandingsEntry(**dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Matchups
# ---------------------------------------------------------------------------

@router.get("/{league_id}/matchups", response_model=list[MatchupResponse])
async def list_matchups(
    league_id: UUID,
    year: int | None = None,
    week: int | None = None,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        if year is None:
            year = await conn.fetchval(
                "SELECT season_year FROM user_api.leagues WHERE id = $1", league_id
            )
        rows = await conn.fetch(
            """
            SELECT * FROM user_api.league_weekly_matchups
            WHERE league_id = $1 AND season_year = $2
              AND ($3::INT IS NULL OR week = $3)
            ORDER BY week, created_at
            """,
            league_id, year, week,
        )
    return [MatchupResponse(**dict(r)) for r in rows]


@router.post("/{league_id}/matchups", response_model=MatchupResponse, status_code=status.HTTP_201_CREATED)
async def create_matchup(
    league_id: UUID,
    body: MatchupCreate,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        try:
            matchup_id = await conn.fetchval(
                "SELECT user_api.usp_create_matchup($1,$2,$3,$4,$5,$6)",
                league_id, body.season_year, body.week,
                body.home_team_id, body.away_team_id, body.is_playoff,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="Matchup already exists for that team/week")
        row = await conn.fetchrow(
            "SELECT * FROM user_api.league_weekly_matchups WHERE id = $1", matchup_id
        )
    return MatchupResponse(**dict(row))


@router.patch("/{league_id}/matchups/{matchup_id}", response_model=MatchupResponse)
async def update_matchup(
    league_id: UUID,
    matchup_id: UUID,
    body: MatchupUpdate,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "CALL user_api.usp_update_matchup_score($1,$2,$3,$4,$5,$6,$7)",
                matchup_id, league_id,
                body.home_score, body.away_score,
                body.home_projected, body.away_projected, body.status,
            )
        except asyncpg.RaiseError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        row = await conn.fetchrow(
            "SELECT * FROM user_api.league_weekly_matchups WHERE id = $1", matchup_id
        )
    return MatchupResponse(**dict(row))


# ---------------------------------------------------------------------------
# Team Season Stats
# ---------------------------------------------------------------------------

@router.get("/{league_id}/teams/{team_id}/season-stats", response_model=TeamSeasonStatsResponse)
async def get_team_season_stats(
    league_id: UUID,
    team_id: UUID,
    year: int | None = None,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        if year is None:
            year = await conn.fetchval(
                "SELECT season_year FROM user_api.leagues WHERE id = $1", league_id
            )
        row = await conn.fetchrow(
            "SELECT * FROM user_api.league_team_season_stats WHERE league_team_id = $1 AND season_year = $2",
            team_id, year,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Season stats not found")
    d = dict(row)
    budget_start = d.get("waiver_budget_start")
    budget_used = d.get("waiver_budget_used", 0)
    d["waiver_budget_remaining"] = (budget_start - budget_used) if budget_start is not None else None
    return TeamSeasonStatsResponse(**d)


@router.put("/{league_id}/teams/{team_id}/season-stats", response_model=TeamSeasonStatsResponse)
async def upsert_team_season_stats(
    league_id: UUID,
    team_id: UUID,
    body: TeamSeasonStatsUpdate,
    year: int | None = None,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        if year is None:
            year = await conn.fetchval(
                "SELECT season_year FROM user_api.leagues WHERE id = $1", league_id
            )
        await conn.execute(
            "CALL user_api.usp_upsert_team_season_stats($1,$2,$3,$4,$5,$6,$7,$8,$9)",
            team_id, year,
            body.waiver_position, body.waiver_budget_start,
            body.waiver_budget_used, body.total_moves,
            body.playoff_seed, body.is_eliminated, body.playoff_result,
        )
        row = await conn.fetchrow(
            "SELECT * FROM user_api.league_team_season_stats WHERE league_team_id = $1 AND season_year = $2",
            team_id, year,
        )
    d = dict(row)
    budget_start = d.get("waiver_budget_start")
    budget_used = d.get("waiver_budget_used", 0)
    d["waiver_budget_remaining"] = (budget_start - budget_used) if budget_start is not None else None
    return TeamSeasonStatsResponse(**d)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@router.get("/{league_id}/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    league_id: UUID,
    year: int | None = None,
    team_id: UUID | None = None,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        if year is None:
            year = await conn.fetchval(
                "SELECT season_year FROM user_api.leagues WHERE id = $1", league_id
            )
        rows = await conn.fetch(
            """
            SELECT * FROM user_api.league_transactions
            WHERE league_id = $1 AND season_year = $2
              AND ($3::UUID IS NULL OR league_team_id = $3)
            ORDER BY created_at DESC
            """,
            league_id, year, team_id,
        )
    return [TransactionResponse(**dict(r)) for r in rows]


@router.post("/{league_id}/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def log_transaction(
    league_id: UUID,
    body: TransactionCreate,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        tx_id = await conn.fetchval(
            "SELECT user_api.usp_log_transaction($1,$2,$3,$4,$5,$6,$7,$8,$9)",
            league_id, body.league_team_id, body.transaction_type,
            body.player_id, body.related_team_id, body.waiver_bid,
            body.week, body.season_year, body.status,
        )
        row = await conn.fetchrow(
            "SELECT * FROM user_api.league_transactions WHERE id = $1", tx_id
        )
    return TransactionResponse(**dict(row))


# ---------------------------------------------------------------------------
# Draft Picks
# ---------------------------------------------------------------------------

@router.get("/{league_id}/draft", response_model=list[DraftPickResponse])
async def list_draft_picks(
    league_id: UUID,
    draft_year: int | None = None,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        if draft_year is None:
            draft_year = await conn.fetchval(
                "SELECT season_year FROM user_api.leagues WHERE id = $1", league_id
            )
        rows = await conn.fetch(
            """
            SELECT * FROM user_api.league_draft_picks
            WHERE league_id = $1 AND draft_year = $2
            ORDER BY pick_number
            """,
            league_id, draft_year,
        )
    return [DraftPickResponse(**dict(r)) for r in rows]


@router.post("/{league_id}/draft", response_model=DraftPickResponse, status_code=status.HTTP_201_CREATED)
async def record_draft_pick(
    league_id: UUID,
    body: DraftPickCreate,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        pick_id = await conn.fetchval(
            "SELECT user_api.usp_record_draft_pick($1,$2,$3,$4,$5,$6,$7,$8,$9)",
            league_id, body.draft_year, body.pick_number,
            body.round_number, body.pick_in_round,
            body.league_team_id, body.player_id,
            body.bid_amount, body.nominated_by,
        )
        row = await conn.fetchrow(
            "SELECT * FROM user_api.league_draft_picks WHERE id = $1", pick_id
        )
    return DraftPickResponse(**dict(row))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _owner_count(pool: asyncpg.Pool, team_id: UUID) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM user_api.league_team_owners WHERE league_team_id = $1 AND is_active = TRUE",
            team_id,
        )
