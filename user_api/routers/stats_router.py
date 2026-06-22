"""Auth-gated NFL stats endpoints for the user frontend."""

import logging
import uuid
from datetime import date
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
        rows = await conn.fetch(
            "SELECT id, espn_id, abbr, full_name FROM teams ORDER BY abbr"
        )
    return [dict(r) for r in rows]


@router.get("/games")
async def get_games(
    date_start: str | None = Query(None),
    date_end: str | None = Query(None),
    season: int | None = Query(None),
    week: int | None = Query(None),
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    where = []
    params: list[Any] = []
    idx = 1

    if date_start:
        where.append(f"g.game_date::date >= ${idx}")
        params.append(date.fromisoformat(date_start))
        idx += 1
    if date_end:
        where.append(f"g.game_date::date <= ${idx}")
        params.append(date.fromisoformat(date_end))
        idx += 1
    if season:
        where.append(f"g.season_year = ${idx}")
        params.append(season)
        idx += 1
    if week is not None:
        where.append(f"g.week = ${idx}")
        params.append(week)
        idx += 1

    where_clause = ("WHERE " + " AND ".join(where)) if where else ""
    query = f"""
        SELECT g.id, g.espn_id, g.game_date, g.status_code, g.week, g.season_year,
               g.home_score, g.away_score,
               h.abbr AS home_team_abbr, h.full_name AS home_name,
               a.abbr AS away_team_abbr, a.full_name AS away_name
        FROM games g
        JOIN teams h ON g.home_team_id = h.id
        JOIN teams a ON g.away_team_id = a.id
        {where_clause}
        ORDER BY g.game_date DESC
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    return [dict(r) for r in rows]


@router.get("/game/{game_id}")
async def get_game(
    game_id: str,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> dict[str, Any]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT g.id, g.espn_id, g.game_date, g.status_code,
                   g.week, g.season_year, g.home_score, g.away_score,
                   g.home_team_id, g.away_team_id,
                   ht.abbr AS home_team_abbr, ht.full_name AS home_name,
                   at.abbr AS away_team_abbr, at.full_name AS away_name
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams at ON g.away_team_id = at.id
            WHERE g.id = $1::uuid
            """,
            game_id,
        )
    if not rows:
        raise HTTPException(status_code=404, detail="Game not found")
    return dict(rows[0])


@router.get("/leaderboard/{game_id}")
async def get_leaderboard(
    game_id: str,
    category: str = Query("passing"),
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    try:
        game_uuid = uuid.UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid game_id (expected UUID)")

    BASE = """
        SELECT pgs.*, p.name AS player_name, p.espn_id AS player_espn_id,
               t.abbr AS team_nm
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.id
        LEFT JOIN teams t ON t.id = COALESCE(pgs.team_id, p.team_id)
        WHERE pgs.game_id = $1
    """

    if category == "passing":
        query = BASE + " AND pgs.pass_att > 0 ORDER BY pgs.pass_yds DESC LIMIT 50"
    elif category == "rushing":
        query = BASE + " AND pgs.rush_att > 0 ORDER BY pgs.rush_yds DESC LIMIT 50"
    elif category == "receiving":
        query = BASE + " AND pgs.rec_receptions > 0 ORDER BY pgs.rec_yds DESC LIMIT 50"
    elif category == "defense":
        query = BASE + """
            AND (COALESCE(pgs.def_solo,0) + COALESCE(pgs.def_ast,0) + COALESCE(pgs.def_sacks,0)) > 0
            ORDER BY (COALESCE(pgs.def_solo,0) + COALESCE(pgs.def_ast,0)) DESC LIMIT 50
        """
    elif category == "fumbles":
        query = BASE + """
            AND (COALESCE(pgs.fum_total,0) + COALESCE(pgs.fum_lost,0) + COALESCE(pgs.fum_rec,0)) > 0
            ORDER BY pgs.fum_total DESC LIMIT 50
        """
    elif category == "kicking":
        query = BASE + """
            AND (COALESCE(pgs.k_fg_att,0) + COALESCE(pgs.p_no,0)) > 0
            ORDER BY pgs.k_fg_make DESC LIMIT 50
        """
    elif category == "returns":
        query = BASE + """
            AND (COALESCE(pgs.ret_kick_no,0) + COALESCE(pgs.ret_punt_no,0)) > 0
            ORDER BY (COALESCE(pgs.ret_kick_yds,0) + COALESCE(pgs.ret_punt_yds,0)) DESC LIMIT 50
        """
    else:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, game_uuid)
    return [dict(r) for r in rows]


@router.get("/player/{player_id}")
async def get_player_stats(
    player_id: str,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT pgs.*, p.name AS player_name, p.position_code, p.espn_id AS player_espn_id,
                   t.full_name AS team_name, t.abbr AS player_team_abbr,
                   g.game_date, g.week, g.season_year,
                   ht.abbr AS home_team_abbr, att.abbr AS away_team_abbr,
                   (g.home_team_id = p.team_id) AS is_home,
                   CASE WHEN g.home_team_id = p.team_id THEN att.abbr ELSE ht.abbr END AS opponent_abbr
            FROM player_game_stats pgs
            JOIN players p ON pgs.player_id = p.id
            JOIN games g ON pgs.game_id = g.id
            JOIN teams t ON p.team_id = t.id
            JOIN teams ht ON g.home_team_id = ht.id
            JOIN teams att ON g.away_team_id = att.id
            WHERE pgs.player_id = $1::uuid
            ORDER BY g.season_year DESC, g.week ASC
            """,
            player_id,
        )
    return [dict(r) for r in rows]


@router.get("/team/{team_id}")
async def get_team_stats(
    team_id: str,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT ts.*, g.game_date, g.week, g.season_year,
                   t.abbr AS team_abbr, t.full_name AS team_name
            FROM team_game_stats ts
            JOIN games g ON ts.game_id = g.id
            JOIN teams t ON ts.team_id = t.id
            WHERE ts.team_id = $1::uuid
            ORDER BY g.game_date DESC
            """,
            team_id,
        )
    return [dict(r) for r in rows]


@router.get("/player-season-stats")
async def get_player_season_stats(
    year: int = Query(2025),
    name: str | None = Query(None),
    position: str | None = Query(None),
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    query = """
        SELECT
            p.id::text AS player_id,
            p.name,
            COALESCE(p.position_code, '') AS position_code,
            ARRAY_AGG(DISTINCT t2.abbr ORDER BY t2.abbr) FILTER (WHERE t2.abbr IS NOT NULL) AS team_abbrs,
            COALESCE(SUM(pgs.pass_comp), 0)::int     AS pass_comp,
            COALESCE(SUM(pgs.pass_att), 0)::int      AS pass_att,
            COALESCE(SUM(pgs.pass_yds), 0)::int      AS pass_yds,
            COALESCE(SUM(pgs.pass_td), 0)::int       AS pass_td,
            COALESCE(SUM(pgs.pass_int), 0)::int      AS pass_int,
            COALESCE(SUM(pgs.pass_sacked), 0)::int   AS pass_sacked,
            CAST(COALESCE(ROUND(AVG(pgs.pass_qbr), 1), 0) AS NUMERIC(5,1))    AS pass_qbr,
            CAST(COALESCE(ROUND(AVG(pgs.pass_rating), 1), 0) AS NUMERIC(5,1)) AS pass_rating,
            COALESCE(SUM(pgs.rush_att), 0)::int      AS rush_att,
            COALESCE(SUM(pgs.rush_yds), 0)::int      AS rush_yds,
            COALESCE(SUM(pgs.rush_td), 0)::int       AS rush_td,
            COALESCE(MAX(pgs.rush_long), 0)::int     AS rush_long,
            COALESCE(SUM(pgs.rec_receptions), 0)::int AS rec_receptions,
            COALESCE(SUM(pgs.rec_targets), 0)::int   AS rec_targets,
            COALESCE(SUM(pgs.rec_yds), 0)::int       AS rec_yds,
            COALESCE(SUM(pgs.rec_td), 0)::int        AS rec_td,
            COALESCE(MAX(pgs.rec_long), 0)::int      AS rec_long,
            COALESCE(SUM(pgs.fum_total), 0)::int     AS fum_total,
            COALESCE(SUM(pgs.fum_lost), 0)::int      AS fum_lost,
            COALESCE(SUM(pgs.fum_rec), 0)::int       AS fum_rec,
            COALESCE(SUM(pgs.def_solo), 0)::int      AS def_solo,
            COALESCE(SUM(pgs.def_ast), 0)::int       AS def_ast,
            CAST(COALESCE(SUM(pgs.def_sacks), 0) AS NUMERIC(5,1)) AS def_sacks,
            COALESCE(SUM(pgs.def_tfl), 0)::int       AS def_tfl,
            COALESCE(SUM(pgs.def_pd), 0)::int        AS def_pd,
            COALESCE(SUM(pgs.def_qb_hits), 0)::int   AS def_qb_hits,
            COALESCE(SUM(pgs.def_int), 0)::int       AS def_int,
            COALESCE(SUM(pgs.def_int_yds), 0)::int   AS def_int_yds,
            COALESCE(SUM(pgs.def_td), 0)::int        AS def_td,
            COALESCE(SUM(pgs.k_fg_make), 0)::int     AS k_fg_make,
            COALESCE(SUM(pgs.k_fg_att), 0)::int      AS k_fg_att,
            COALESCE(MAX(pgs.k_fg_long), 0)::int     AS k_fg_long,
            COALESCE(SUM(pgs.k_xp_make), 0)::int     AS k_xp_make,
            COALESCE(SUM(pgs.k_xp_att), 0)::int      AS k_xp_att,
            COALESCE(SUM(pgs.p_no), 0)::int          AS p_no,
            COALESCE(SUM(pgs.p_yds), 0)::int         AS p_yds,
            COALESCE(SUM(pgs.p_in20), 0)::int        AS p_in20,
            COALESCE(SUM(pgs.p_tb), 0)::int          AS p_tb,
            COALESCE(SUM(pgs.p_blk), 0)::int         AS p_blk,
            COALESCE(SUM(pgs.p_long), 0)::int        AS p_long,
            COALESCE(SUM(pgs.ret_kick_no), 0)::int   AS ret_kick_no,
            COALESCE(SUM(pgs.ret_kick_yds), 0)::int  AS ret_kick_yds,
            COALESCE(SUM(pgs.ret_kick_td), 0)::int   AS ret_kick_td,
            COALESCE(MAX(pgs.ret_kick_long), 0)::int  AS ret_kick_long,
            COALESCE(SUM(pgs.ret_punt_no), 0)::int   AS ret_punt_no,
            COALESCE(SUM(pgs.ret_punt_yds), 0)::int  AS ret_punt_yds,
            COALESCE(SUM(pgs.ret_punt_td), 0)::int   AS ret_punt_td,
            COALESCE(MAX(pgs.ret_punt_long), 0)::int  AS ret_punt_long
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.id
        LEFT JOIN teams t2 ON pgs.team_id = t2.id
        JOIN games g ON pgs.game_id = g.id
        WHERE g.season_year = $1
          AND ($2::text IS NULL OR p.name ILIKE '%' || $2 || '%')
          AND ($3::text IS NULL OR p.position_code = $3)
        GROUP BY p.id, p.name, p.position_code
        ORDER BY
            (COALESCE(SUM(pgs.pass_yds), 0) + COALESCE(SUM(pgs.rush_yds), 0) + COALESCE(SUM(pgs.rec_yds), 0)) DESC,
            (COALESCE(SUM(pgs.def_solo), 0) + COALESCE(SUM(pgs.def_ast), 0)) DESC,
            COALESCE(SUM(pgs.k_fg_make), 0) DESC,
            COALESCE(SUM(pgs.p_no), 0) DESC
        LIMIT 2000
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, year, name or None, position or None)
    result = []
    for r in rows:
        row = dict(r)
        row["def_sacks"] = float(row["def_sacks"]) if row["def_sacks"] else 0.0
        row["pass_qbr"] = float(row["pass_qbr"]) if row["pass_qbr"] else 0.0
        row["pass_rating"] = float(row["pass_rating"]) if row["pass_rating"] else 0.0
        result.append(row)
    return result


@router.get("/player-positions")
async def get_player_positions(
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[str]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT p.position_code
            FROM players p
            JOIN player_game_stats pgs ON pgs.player_id = p.id
            WHERE p.position_code IS NOT NULL AND p.position_code != ''
            ORDER BY p.position_code
            """
        )
    return [r["position_code"] for r in rows]


@router.get("/fantasy/{player_id}")
async def get_fantasy_stats(
    player_id: str,
    current_user: UserContext = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_pool),
) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT pgs.*, p.name AS player_name, p.position_code, p.espn_id AS player_espn_id,
                   t.full_name AS team_name, g.game_date, g.week, g.season_year
            FROM player_game_stats pgs
            JOIN players p ON pgs.player_id = p.id
            JOIN games g ON pgs.game_id = g.id
            JOIN teams t ON p.team_id = t.id
            WHERE pgs.player_id = $1::uuid
            ORDER BY g.game_date DESC
            """,
            player_id,
        )
    results = []
    for r in rows:
        row = dict(r)
        row["total_yards"] = (row.get("pass_yds") or 0) + (row.get("rush_yds") or 0) + (row.get("rec_yds") or 0)
        row["total_td"] = (row.get("pass_td") or 0) + (row.get("rush_td") or 0) + (row.get("rec_td") or 0)
        row["fantasy_points"] = (
            (row.get("pass_yds") or 0) / 10 + (row.get("rush_yds") or 0) / 10 + (row.get("rec_yds") or 0) / 10
            + (row.get("pass_td") or 0) * 4 + (row.get("rush_td") or 0) * 4 + (row.get("rec_td") or 0) * 4
            + (row.get("rec_receptions") or 0) * 0.5
        )
        results.append(row)
    return results
