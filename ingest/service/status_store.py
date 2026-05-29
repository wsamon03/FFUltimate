"""In-memory task status tracking for the ingestion API."""

import uuid
from enum import Enum
from typing import Dict, Optional


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionStatusStore:
    def __init__(self):
        self.tasks: Dict[uuid.UUID, dict] = {}

    def create_task(self, task_id: uuid.UUID) -> None:
        self.tasks[task_id] = {
            "status": TaskStatus.QUEUED,
            "progress": {"ingested": 0, "failed": 0},
            "error": None
        }

    def update_progress(self, task_id: uuid.UUID, ingested: int, failed: int) -> None:
        if task_id in self.tasks:
            self.tasks[task_id]["progress"] = {"ingested": ingested, "failed": failed}

    def complete_task(self, task_id: uuid.UUID) -> None:
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = TaskStatus.COMPLETED

    def fail_task(self, task_id: uuid.UUID, error: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = TaskStatus.FAILED
            self.tasks[task_id]["error"] = error

    def get(self, task_id: uuid.UUID) -> Optional[dict]:
        return self.tasks.get(task_id)
