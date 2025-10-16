# app/background/__init__.py
from .tasks import process_batch_task

__all__ = ["process_batch_task"]