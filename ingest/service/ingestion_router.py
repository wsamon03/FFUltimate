"""Ingestion API endpoints for the NFL ingestion system."""

import asyncio
import os
import uuid
import logging
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from ingest.db_writer import PgDBWriter
from ingest.engine import IngestionEngine
from ingest.espn.client import ESPNClient
from ingest.espn.mock_client import MockESPNClient
from ingest.espn.transformer import ESPNTransformer
from ingest.service.task_store import status_store
from ingest.service.app import POOL as _POOL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])


def get_ingestion_engine() -> IngestionEngine:
    """Dependency injector for the ingestion engine."""
    from ingest.service.app import POOL
    
    if not POOL:
        raise RuntimeError("Database pool not initialized. Ensure app is running.")
    
    api_provider = MockESPNClient() if os.getenv("MOCK_ESPN") == "true" else ESPNClient()
    transformer = ESPNTransformer()
    db_writer = PgDBWriter(POOL)
    
    return IngestionEngine(
        api_provider=api_provider,
        transformer=transformer,
        db_writer=db_writer,
        pool=POOL
    )


@router.get("/tasks")
async def get_ingestion_tasks():
    """Fetch all tracked ingestion tasks."""
    tasks = status_store.get_all()
    return tasks

@router.post("/game")
async def ingest_single_game(
    event_id: str = Query(..., description="ESPN event ID for the game"),
    background_tasks: BackgroundTasks = None,
):
    """Ingest a single game by ESPN event ID. Returns immediately."""
    task_id = uuid.uuid4()
    status_store.create_task(task_id)
    status_store.update_task(task_id, status="running")
    
    async def run_ingestion():
        logger.info(f"[Worker] Starting task {task_id}")
        try:
            engine = get_ingestion_engine()
            game_id = await engine.process_game(event_id)
            if game_id:
                status_store.complete_task(task_id)
            else:
                status_store.fail_task(task_id, "No data found for game")
        except Exception as e:
            logger.error(f"[Worker] Task {task_id} failed: {e}")
            status_store.fail_task(task_id, str(e))

    background_tasks.add_task(run_ingestion)
    return {"task_id": str(task_id), "status": "queued"}


@router.post("/week", response_model=dict)
async def ingest_week(
    year: int = Query(..., description="Season year"),
    week: int = Query(..., ge=1, le=22, description="Week number (1-22)"),
    include_playoffs: bool = Query(False),
    background_tasks: BackgroundTasks = None,
):
    """Ingest all games for a specific week. Returns immediately."""
    task_id = uuid.uuid4()
    status_store.create_task(task_id)
    status_store.update_task(task_id, status="running", progress={"ingested": 0, "failed": 0})
    
    async def run_week_ingestion():
        engine = get_ingestion_engine()
        try:
            processed, failed = await engine.process_week(str(year), week)
            status_store.update_progress(task_id, processed, failed)
            status_store.complete_task(task_id)
        except Exception as e:
            status_store.fail_task(task_id, str(e))

    background_tasks.add_task(run_week_ingestion)
    return {"task_id": str(task_id), "status": "queued"}


@router.post("/season", response_model=dict)
async def ingest_season(
    year: int = Query(..., description="Season year"),
    include_playoffs: bool = Query(False),
    background_tasks: BackgroundTasks = None,
):
    """Ingest an entire season. Returns immediately."""
    task_id = uuid.uuid4()
    status_store.create_task(task_id)
    status_store.update_task(task_id, status="running", progress={"ingested": 0, "failed": 0})
    
    async def run_season_ingestion():
        engine = get_ingestion_engine()
        try:
            processed, failed = await engine.process_season(str(year), include_playoffs)
            status_store.update_progress(task_id, processed, failed)
            status_store.complete_task(task_id)
        except Exception as e:
            status_store.fail_task(task_id, str(e))

    background_tasks.add_task(run_season_ingestion)
    return {"task_id": str(task_id), "status": "queued"}


@router.get("/status/{task_id}")
async def get_ingestion_status(task_id: uuid.UUID):
    """Check the progress and final status of a background ingestion task."""
    task = status_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
