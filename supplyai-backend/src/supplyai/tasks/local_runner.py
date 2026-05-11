"""本地任务调度器 — FastAPI BackgroundTasks 实现."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import BackgroundTasks


class LocalTaskRunner:
    """同进程异步任务调度.

    在 API 响应后执行任务(不阻塞客户端);
    适合单实例部署 / 演示场景。
    """

    def __init__(self, bg: BackgroundTasks) -> None:
        self._bg = bg

    async def submit(
        self,
        task_fn: Callable[..., Awaitable[None]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # FastAPI BackgroundTasks 接受 sync / async callable;
        # async callable 会在响应返回后被 await 执行
        self._bg.add_task(task_fn, *args, **kwargs)
