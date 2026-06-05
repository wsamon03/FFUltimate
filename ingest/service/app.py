"""FastAPI application for the NFL ingestion system."""

import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

import asyncpg
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from ingest.service.ingestion_router import router as ingestion_router
from ingest.service.retrieval_router import router as retrieval_router

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)
POOL = None


# ========== APP CREATION ==========
app = FastAPI(
    title="NFL Data Ingestion API",
    description="API for ingesting and retrieving NFL game data from sports APIs",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router)
app.include_router(retrieval_router)


@asynccontextmanager
async def lifespan(application):
    global POOL
    try:
        logger.info("Initializing PostgreSQL Connection Pool...")
        
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "nfl_fantasy")
        
        # Construct DSN
        dsn = f"postgres://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        
        POOL = await asyncpg.create_pool(
            dsn=dsn,
            min_size=5,
            max_size=20
        )
        # Expose pool to request state for dependency injection
        application.state.pool = POOL
        logger.info("PostgreSQL Connection Pool ready.")
    except Exception as e:
        logger.error(f"Failed to create pool: {e}")
        raise
    yield
    logger.info("Closing PostgreSQL Connection Pool.")
    await POOL.close()


# =================== DELETION ROUTES ===================
@app.delete("/api/delete/season", response_model=dict)
async def delete_season(year: int = Query(...)):
    """Delete all data for a given season."""
    global POOL
    try:
        async with POOL.transaction() as conn:
            # Delete from all associated tables in proper order
            # Games are deleted first (they're the most specific)
            # Then player_game_stats, team_game_stats
            query = """
            DELETE FROM games WHERE year = $1
            RETURNING id, date
            
            UNION
            
            DELETE FROM player_game_stats 
            WHERE game_id IN (SELECT id FROM games WHERE year = $1)
            
            UNION
            
            DELETE FROM team_game_stats 
            WHERE game_id IN (SELECT id FROM games WHERE year = $1)
            """
            results = await conn.fetch(query, year)
            
        logger.info(f"\n[INFO] Deleted {len(results)} records for season {year}")
        return {"status": "success", "message": "Season deleted"}
    except Exception as e:
        logger.error(f"Failed to delete season {year}: {e}")
        return {"status": "error", "message": "Delete failed", "error": str(e)}


@app.delete("/api/delete/week", response_model=dict)
async def delete_week(year: int = Query(...), week: int = Query(...)):
    """Delete all data for a given year-week.

Note: Week should be 1-18 (no 19 or higher)."""
    global POOL
    try:
        if year > 2026 or week < 1 or week > 18:
            return {"status": "error", "message": "Invalid year or week parameters"}

        async with POOL.transaction() as conn:
            # Create date for the week (Wed to Tue)
            from datetime import datetime, timedelta
            # Get games for this specific week
            query = """
            DELETE FROM game_dates 
            WHERE date::date >= $1::date::date AND date::date < $2::date::date
            RETURNING id, game_id
            
            UNION
            
            DELETE FROM games 
            WHERE date::date >= $1::date::date AND date::date < $2::date::date
            
            UNION
            
            DELETE FROM player_game_stats 
            WHERE game_id IN (SELECT id FROM games WHERE date::date >= $1::date::date AND date::date < $2::date::date)
            
            UNION
            
            DELETE FROM team_game_stats 
            WHERE game_id IN (SELECT id FROM games WHERE date::date >= $1::date::date AND date::date < $2::date::date)
            """
            results = await conn.fetch(query, 
                datetime(year, 12, 30) - timedelta(days=(week - 1) * 7,
                   hours=23, minutes=59, seconds=59),
                datetime(year, 1, 1)
            )
            
        logger.info(f"\n[INFO] Deleted {len(results)} records for week {year}-{week}")
        return {"status": "success", "message": "Week deleted"}
    except Exception as e:
        logger.error(f"Failed to delete week {year}-{week}: {e}")
        return {"status": "error", "message": "Delete failed", "error": str(e)}


@app.delete("/api/delete/game", response_model=dict)
async def delete_game(event_id: str = Query(...)):
    """Delete all data for a specific ESPN event ID."""
    global POOL
    try:
        # Validate ESPN event ID format
        parts = event_id.split('-')
        if len(parts) != 4:
            return {"status": "error", "message": "Invalid ESPN event ID format"}
        
        async with POOL.transaction() as conn:
            # Get the game details first
            game_query = """
            SELECT g.id, g.event_id, g.date,
                   COUNT(pg.id) as player_count,
                   COUNT(tg.id) as team_count
            FROM games g
            LEFT JOIN player_game_stats pg ON pg.game_id = g.id
            LEFT JOIN team_game_stats tg ON tg.game_id = g.id
            WHERE g.event_id = $1
            GROUP BY g.id, g.event_id, g.date
            """
            game = await conn.fetch_one(game_query, event_id)
            
            if not game:
                return {"status": "error", "message": "Game not found"}
            
            # Delete game_dates and games
            delete_game_query = """
            DELETE FROM game_dates WHERE game_id = $1
            
            UNION
            
            DELETE FROM games WHERE id = $1
            """
            game_id = game['id']
            await conn.fetch(delete_game_query, game_id)
            
            # Delete player and team stats
            # (The UNION statement already returned counts, but if no rows from games,
            # we still need to delete the related stats)
            
            player_query = """
            DELETE FROM player_game_stats WHERE game_id = $1
            """
            await conn.fetch(player_query, game_id)
            
            return {"status": "success", "message": f"Game {event_id} deleted along with {game['player_count']} player record(s) and {game['team_count']} team record(s)"}
    except Exception as e:
        logger.error(f"Failed to delete game {event_id}: {e}")
        return {"status": "error", "message": "Delete failed", "error": str(e)}
