"""Persistent file-based task store for ingestion status."""

import json
import uuid
import os
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

TASK_STORE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'tasks.json')

class PersistentTaskStore:
    def __init__(self):
        self.path = TASK_STORE_PATH
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, 'w') as f:
                json.dump({}, f)

    def _load(self) -> Dict:
        with open(self.path, 'r') as f:
            return json.load(f)

    def _save(self, data: Dict):
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)

    def create_task(self, task_id: uuid.UUID, task_type: str = "unknown") -> dict:
        tasks = self._load()
        tasks[str(task_id)] = {
            "id": str(task_id),
            "type": task_type,
            "status": "queued",
            "progress": {"ingested": 0, "failed": 0},
            "error": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._save(tasks)
        return tasks[str(task_id)]

    def update_task(self, task_id: uuid.UUID, **kwargs) -> dict:
        tasks = self._load()
        if str(task_id) in tasks:
            tasks[str(task_id)].update(kwargs)
            tasks[str(task_id)]["updated_at"] = datetime.now().isoformat()
            self._save(tasks)
        return tasks[str(task_id)]

    def complete_task(self, task_id: uuid.UUID, total: int = 0) -> dict:
        return self.update_task(task_id, status="completed", progress={"ingested": total, "failed": 0, "total": total})

    def fail_task(self, task_id: uuid.UUID, error: str) -> dict:
        return self.update_task(task_id, status="failed", error=error, progress=None)

    def update_progress(self, task_id: uuid.UUID, ingested: int, failed: int, total: int = 0) -> dict:
        return self.update_task(task_id, progress={"ingested": ingested, "failed": failed, "total": total})

    def get(self, task_id: uuid.UUID) -> Optional[dict]:
        tasks = self._load()
        return tasks.get(str(task_id))

    def get_all(self) -> Dict:
        tasks = self._load()
        return {k: v for k, v in sorted(tasks.items(), key=lambda x: x[1].get('updated_at', ''), reverse=True)}

status_store = PersistentTaskStore()
