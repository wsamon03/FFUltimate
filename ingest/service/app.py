"""FastAPI application for the NFL ingestion system."""

import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

import asyncpg
#
# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)
POOL = None


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


from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from ingest.service.ingestion_router import router as ingestion_router
from ingest.service.retrieval_router import router as retrieval_router

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
@app.delete("/api/delete/season", response_model=dict)
async def delete_season(year: int = Query(...)):
    """Delete all data for a given season."""
    global POOL
    try:
        async with POOL.acquire() as conn:
            await conn.execute(
                "DELETE FROM player_game_stats WHERE game_id IN (SELECT id FROM games WHERE season_year = $1)", year
            )
            await conn.execute(
                "DELETE FROM team_game_stats WHERE game_id IN (SELECT id FROM games WHERE season_year = $1)", year
            )
            await conn.execute("DELETE FROM games WHERE season_year = $1", year)
            
        logger.info(f"\n[INFO] Deleted records for season {year}")
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
        if week < 0 or week > 22:
            return {"status": "error", "message": "Week must be between 0 and 22"}

        async with POOL.acquire() as conn:
            # 1. Check exactly what rows match before deleting
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM games WHERE season_year = $1 AND week = $2",
                year, week
            )
            if count == 0:
                return {"status": "warning", "message": "No data found for deletion", "details": {"year": year, "week": week, "games_matching": 0}}

            # 2. Delete player stats
            await conn.execute(
                "DELETE FROM player_game_stats WHERE game_id IN (SELECT id FROM games WHERE season_year = $1 AND week = $2)",
                year, week
            )
            # 3. Delete team stats
            await conn.execute(
                "DELETE FROM team_game_stats WHERE game_id IN (SELECT id FROM games WHERE season_year = $1 AND week = $2)",
                year, week
            )
            # 4. Delete games
            await conn.execute(
                "DELETE FROM games WHERE season_year = $1 AND week = $2",
                year, week
            )
            
        logger.info(f"[INFO] Deleted {count} games for season {year} week {week}")
        return {"status": "success", "message": f"Week deleted ({count} games removed)"}
    except Exception as e:
        logger.error(f"Failed to delete week {year}-{week}: {e}")
        return {"status": "error", "message": "Delete failed", "error": str(e)}



@app.delete("/api/delete/game", response_model=dict)
async def delete_game(event_id: str = Query(...)):
    """Delete all data for a specific internal game ID (UUID)."""
    global POOL
    async with POOL.acquire() as conn:
        try:
            game = await conn.fetchrow("SELECT id FROM games WHERE id = $1", event_id)
            game_id = game["id"]
            
            await conn.execute("DELETE FROM player_game_stats WHERE game_id = $1", game_id)
            await conn.execute("DELETE FROM team_game_stats WHERE game_id = $1", game_id)
            await conn.execute("DELETE FROM games WHERE id = $1", game_id)
            return {"status": "success", "message": f"Game {game_id.hex} deleted"}
        except Exception:
            return {"status": "warning", "message": "Game not found"}




