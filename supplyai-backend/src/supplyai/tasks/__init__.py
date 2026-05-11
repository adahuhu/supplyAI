"""任务调度抽象 — 本地 BackgroundTasks / 生产 Celery."""
from supplyai.tasks.runner import TaskRunner

__all__ = ["TaskRunner"]
