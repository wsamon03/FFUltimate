"""Ingestion API endpoints for the NFL ingestion system."""

import asyncio
import uuid
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from ingest.db_writer import PgDBWriter
from ingest.engine import IngestionEngine
from ingest.espn.client import ESPNClient
from ingest.espn.transformer import ESPNTransformer
from ingest.service.app import POOL
from ingest.service.status_store import IngestionStatusStore, TaskStatus

logger = logging.getLogger(__name__)

status_store = IngestionStatusStore()
router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])


def get_ingestion_engine() -> IngestionEngine:
    """Dependency injector for the ingestion engine."""
    if not POOL:
        raise RuntimeError("Database pool not initialized. Ensure app is running.")
    
    api_provider = ESPNClient()
    transformer = ESPNTransformer()
    db_writer = PgDBWriter(POOL)
    
    return IngestionEngine(
        api_provider=api_provider,
        transformer=transformer,
        db_writer=db_writer,
        pool=POOL
    )


@router.post("/game")
async def ingest_single_game(
    event_id: str = Query(..., description="ESPN event ID for the game"),
):
    """Ingest a single game by ESPN event ID. Returns immediately."""
    task_id = uuid.uuid4()
    status_store.create_task(task_id)
    
    async def run_ingestion():
        engine = get_ingestion_engine()
        try:
            game_id = await engine.process_game(event_id)
            if game_id:
                status_store.complete_task(task_id)
            else:
                status_store.fail_task(task_id, "No data found for game")
        except Exception as e:
            status_store.fail_task(task_id, str(e))

    # Run in background
    asyncio.create_task(run_ingestion())
    
    return {"task_id": task_id, "status": "queued"}


@router.post("/week")
async def ingest_week(
    year: int = Query(..., description="Season year"),
    week: int = Query(..., ge=1, le=22, description="Week number (1-22)"),
    include_playoffs: bool = Query(False),
):
    """Ingest all games for a specific week. Returns immediately."""
    task_id = uuid.uuid4()
    status_store.create_task(task_id)

    async def run_ingestion():
        engine = get_ingestion_engine()
        try:
            status_store.tasks[task_id]["status"] = TaskStatus.RUNNING
            status_store.tasks[task_id]["progress"] = {"ingested": 0, "failed": 0}
            
            # We need to access the stored engine task result
            # For simplicity in this refactoring, we just rely on the loop in the engine
            processed, failed = await engine.process_week(str(year), week)
            
            status_store.update_progress(task_id, processed, failed)
            status_store.complete_task(task_id)
        except Exception as e:
            status_store.fail_task(task_id, str(e))

    asyncio.create_task(run_ingestion())
    
    return {"task_id": task_id, "status": "queued"}


@router.post("/season")
async def ingest_season(
    year: int = Query(..., description="Season year"),
    include_playoffs: bool = Query(False),
):
    """Ingest an entire season. Returns immediately."""
    task_id = uuid.uuid4()
    status_store.create_task(task_id)

    async def run_ingestion():
        engine = get_ingestion_engine()
        try:
            status_store.tasks[task_id]["status"] = TaskStatus.RUNNING
            status_store.tasks[task_id]["progress"] = {"ingested": 0, "failed": 0}
            
            processed, failed = await engine.process_season(str(year), include_playoffs)
            
            status_store.update_progress(task_id, processed, failed)
            status_store.complete_task(task_id)
        except Exception as e:
            status_store.fail_task(task_id, str(e))

    asyncio.create_task(run_ingestion())
    
    return {"task_id": task_id, "status": "queued"}


@router.get("/status/{task_id}")
async def get_ingestion_status(task_id: uuid.UUID):
    """Check the progress and final status of a background ingestion task."""
    task = status_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task
