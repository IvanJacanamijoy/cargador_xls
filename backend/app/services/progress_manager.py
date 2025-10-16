import time
import asyncio
from typing import Dict, Optional

class ProgressManager:
    def __init__(self):
        self.batches: Dict[str, Dict] = {}

    async def init_batch(self, batch_id: str, total: int):
        self.batches[batch_id] = {
            "batch_id": batch_id,
            "processed": 0,
            "total": total,
            "successful": 0,
            "failed": 0,
            "percentage": 0.0,
            "status": "processing",
            "current_record": None,
            "start_time": time.time(),
            "speed": 0.0,
            "estimated_time_remaining": None,
            "errors": []
        }

    async def update_progress(
        self,
        batch_id: str,
        successful: int = 0,
        failed: int = 0,
        current_record: Optional[str] = None,
        error: Optional[dict] = None
    ):
        batch = self.batches.get(batch_id)
        if not batch or batch["status"] != "processing":
            return

        batch["processed"] += successful + failed
        batch["successful"] += successful
        batch["failed"] += failed
        batch["current_record"] = current_record

        elapsed = time.time() - batch["start_time"]
        batch["speed"] = round(batch["processed"] / elapsed, 2) if elapsed > 0 else 0.0
        batch["percentage"] = round((batch["processed"] / batch["total"]) * 100, 2)

        if batch["speed"] > 0:
            remaining = batch["total"] - batch["processed"]
            batch["estimated_time_remaining"] = round(remaining / batch["speed"], 2)

        if error:
            batch["errors"].append(error)

    async def complete_batch(self, batch_id: str, status: str, error_message: Optional[str] = None):
        batch = self.batches.get(batch_id)
        if not batch:
            return
        batch["status"] = status
        batch["completed_at"] = time.time()
        if error_message:
            batch["error_message"] = error_message

    def get_progress(self, batch_id: str):
        return self.batches.get(batch_id)
