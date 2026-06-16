"""Retrieval API endpoints that query the database via stored procedures."""

import json
import uuid
import asyncpg
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from ingest.base import APIProvider
from ingest.espn.client import ESPNClient

router = APIRouter(tags=["Retrieval"])

def get_pool(request: Request) -> asyncpg.Pool:
    """Dependency to access the global asyncpg pool."""
    return request.app.state.pool

@router.get("/api/stats/teams")
async def get_teams(pool: asyncpg.Pool = Depends(get_pool)):
    """Get all teams."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, espn_id, abbr, full_name FROM teams ORDER BY abbr")
        return [{"id": str(r["id"]), "espn_id": r["espn_id"], "abbr": r["abbr"], "full_name": r["full_name"]} for r in rows]

@router.get("/api/stats/games")
async def get_games(
    date_start: str = None,
    date_end: str = None,
    season: int = None,
    week: int = None,
    pool: asyncpg.Pool = Depends(get_pool),
):
    """Get filtered list of games."""
    where = []
    params = []
    param_idx = 1

    from datetime import date

    if date_start:
        where.append(f"game_date::date >= ${param_idx}")
        params.append(date.fromisoformat(date_start))
        param_idx += 1

    if date_end:
        where.append(f"game_date::date <= ${param_idx}")
        params.append(date.fromisoformat(date_end))
        param_idx += 1

    if season:
        where.append(f"season_year = ${param_idx}")
        params.append(season)
        param_idx += 1

    if week is not None:
        where.append(f"g.week = ${param_idx}")
        params.append(week)
        param_idx += 1
    where_clause = " WHERE " + " AND ".join(where) if where else ""
    
    query = (
        f"SELECT g.id, g.espn_id, g.game_date, g.status_code, g.week, g.season_year, "
        f"g.home_score, g.away_score, "
        f"h.abbr as home_team_abbr, h.full_name as home_name, "
        f"a.abbr as away_team_abbr, a.full_name as away_name "
        f"FROM games g "
        f"JOIN teams h ON g.home_team_id = h.id "
        f"JOIN teams a ON g.away_team_id = a.id "
        f"{where_clause} ORDER BY g.game_date DESC"
    )
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        return [dict(r) for r in rows]

@router.get("/api/stats/game/{game_id}")
async def get_game_stats(
    game_id: str,
    pool: asyncpg.Pool = Depends(get_pool)
):
    """Get full game summary with both teams' stats."""
    try:
        game_uuid = uuid.UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid game_id format (expected UUID)")

    query = (
        "SELECT g.id, g.espn_id, g.game_date, g.status_code, "
        "g.week, g.season_year, g.home_score, g.away_score, "
        "ht.espn_id as home_espn_id, ht.abbr as home_abbr, ht.full_name as home_name, "
        "ht.abbr as home_team_abbr, "
        "at.espn_id as away_espn_id, at.abbr as away_abbr, at.full_name as away_name, "
        "at.abbr as away_team_abbr "
        "FROM games g "
        "JOIN teams ht ON g.home_team_id = ht.id "
        "JOIN teams at ON g.away_team_id = at.id "
        "LEFT JOIN team_game_stats ts_h ON ts_h.game_id = g.id AND ts_h.team_id = g.home_team_id "
        "LEFT JOIN team_game_stats ts_a ON ts_a.game_id = g.id AND ts_a.team_id = g.away_team_id "
        "WHERE g.id = $1"
    )
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, game_uuid)
        if not rows:
            raise HTTPException(status_code=404, detail=f"Game not found: {game_id}")
        result = dict(rows[0])
        # Parse JSON metadata if present
        if result.get("metadata"):
            result["metadata"] = json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"]
        return result

@router.get("/api/stats/player/{player_id}")
async def get_player_stats(player_id: str, pool: asyncpg.Pool = Depends(get_pool)):
    """Get all stats for a player across all games."""
    query = (
        "SELECT pgs.*, p.name as player_name, p.position_code, p.espn_id as player_espn_id, "
        "t.full_name as team_name, g.game_date, g.week, g.season_year "
        "FROM player_game_stats pgs "
        "JOIN players p ON pgs.player_id = p.id "
        "JOIN games g ON pgs.game_id = g.id "
        "JOIN teams t ON p.team_id = t.id "
        "WHERE pgs.player_id = $1 "
        "ORDER BY g.game_date DESC"
    )
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, player_id)
        return [dict(r) for r in rows]

@router.get("/api/stats/team/{team_id}")
async def get_team_stats(team_id: str, pool: asyncpg.Pool = Depends(get_pool)):
    """Get all stats for a team."""
    query = (
        "SELECT ts.*, g.game_date, g.week, g.season_year, "
        "t.abbr as team_abbr, t.full_name as team_name "
        "FROM team_game_stats ts "
        "JOIN games g ON ts.game_id = g.id "
        "JOIN teams t ON ts.team_id = t.id "
        "WHERE ts.team_id = $1 "
        "ORDER BY g.game_date DESC"
    )
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, team_id)
        return [dict(r) for r in rows]

@router.get("/api/stats/leaderboard/{game_id}")
async def get_leaderboard(game_id: str, category: str = "passing", pool: asyncpg.Pool = Depends(get_pool)):
    """Get top players in a game for a given category (passing/rushing/receiving)."""
    try:
        game_uuid = uuid.UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid game_id format (expected UUID)")

    if category == "passing":
        query = (
            "SELECT pgs.*, p.name as player_name, p.espn_id as player_espn_id, "
            "t.abbr as team_nm "
            "FROM player_game_stats pgs "
            "JOIN players p ON pgs.player_id = p.id "
            "JOIN teams t ON t.id = p.team_id "
            "WHERE pgs.game_id = $1 AND pgs.pass_att > 0 "
            "ORDER BY pgs.pass_yds DESC LIMIT 20"
        )
        params = [game_uuid]
    elif category == "rushing":
        query = (
            "SELECT pgs.*, p.name as player_name, p.espn_id as player_espn_id, "
            "t.abbr as team_nm "
            "FROM player_game_stats pgs "
            "JOIN players p ON pgs.player_id = p.id "
            "JOIN teams t ON t.id = p.team_id "
            "WHERE pgs.game_id = $1 AND pgs.rush_att > 0 "
            "ORDER BY pgs.rush_yds DESC LIMIT 20"
        )
        params = [game_uuid]
    elif category == "receiving":
        query = (
            "SELECT pgs.*, p.name as player_name, p.espn_id as player_espn_id, "
            "t.abbr as team_nm "
            "FROM player_game_stats pgs "
            "JOIN players p ON pgs.player_id = p.id "
            "JOIN teams t ON t.id = p.team_id "
            "WHERE pgs.game_id = $1 AND pgs.rec_receptions > 0 "
            "ORDER BY pgs.rec_yds DESC LIMIT 20"
        )
        params = [game_uuid]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category}")
        
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(query, *params)
        except Exception as e:
            print(f"[ERROR] get_leaderboard query failed for {game_uuid}: {e}")
            raise
        # Debug - check if any data exists for this game
        if not rows:
            print(f"[DEBUG] No rows returned for game {game_uuid} in category {category}")
            # Check if player_game_stats has data
            count_query_str = f"SELECT COUNT(*) FROM player_game_stats WHERE game_id = $1"
            count_results = await conn.fetch(count_query_str, game_uuid)
            # Debug - see actual column name and structure
            if count_results:
                print(f"[DEBUG] Count results: {count_results}")
                count_value = count_results[0].get("COUNT(*)", count_results[0].get("COUNT", 0))
                if count_value:
                    print(f"[DEBUG] Total player_game_stats records for game {game_uuid}: {count_value}")
        else:
            print(f"[DEBUG] Returned {len(rows)} rows for game {game_uuid} - {category}")
        return [dict(r) for r in rows]

@router.get("/fantasy/{player_id}")
async def get_fantasy_stats(player_id: str, pool: asyncpg.Pool = Depends(get_pool)):
    """Get fantasy-ready stats for a player."""
    query = (
        "SELECT pgs.*, p.name as player_name, p.position_code, p.espn_id as player_espn_id, "
        "t.full_name as team_name, g.game_date, g.week, g.season_year "
        "FROM player_game_stats pgs "
        "JOIN players p ON pgs.player_id = p.id "
        "JOIN games g ON pgs.game_id = g.id "
        "JOIN teams t ON p.team_id = t.id "
        "WHERE pgs.player_id = $1 "
        "ORDER BY g.game_date DESC"
    )
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, player_id)
        results = []
        for r in rows:
            row = dict(r)
            # Calculate fantasy points
            row["total_yards"] = (row.get("pass_yds") or 0) + (row.get("rush_yds") or 0) + (row.get("rec_yds") or 0)
            row["total_td"] = (row.get("pass_td") or 0) + (row.get("rush_td") or 0) + (row.get("rec_td") or 0)
            row["fantasy_points"] = (
                (row.get("pass_yds") or 0) / 10 + (row.get("rush_yds") or 0) / 10 + (row.get("rec_yds") or 0) / 10 +
                (row.get("pass_td") or 0) * 4 + (row.get("rush_td") or 0) * 4 + (row.get("rec_td") or 0) * 4 +
                (row.get("rec_receptions") or 0) * 0.5
            )
            results.append(row)
        return results