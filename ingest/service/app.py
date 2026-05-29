"""FastAPI application for the NFL ingestion system."""

import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

import asyncpg

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
