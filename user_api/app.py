import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from user_api.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("Initializing PostgreSQL connection pool for user_api...")
    pool = await asyncpg.create_pool(
        dsn=settings.db_dsn,
        min_size=2,
        max_size=10,
    )
    application.state.pool = pool
    logger.info("user_api PostgreSQL pool ready.")
    yield
    logger.info("Closing user_api PostgreSQL pool.")
    await pool.close()


from user_api.routers.auth_router import router as auth_router
from user_api.routers.config_router import router as config_router
from user_api.routers.stats_router import router as stats_router
from user_api.routers.players_router import router as players_router
from user_api.routers.leagues_router import router as leagues_router
from user_api.routers.favorites_router import router as favorites_router

app = FastAPI(
    title="NFL Fantasy Football — User API",
    description="End-user API: OAuth login, fantasy leagues, player stats, and favorites.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(config_router)
app.include_router(stats_router)
app.include_router(players_router)
app.include_router(leagues_router)
app.include_router(favorites_router)
