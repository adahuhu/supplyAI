"""TaskRunner Protocol — 任务调度抽象层."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol


class TaskRunner(Protocol):
    """统一任务调度接口.

    本地实现:`LocalTaskRunner`(FastAPI BackgroundTasks)
    生产实现:`CeleryTaskRunner`(Celery + Redis,Phase 4 启用)

    业务代码只依赖此接口,本地 / 生产差异在 runner 层。
    """

    async def submit(
        self,
        task_fn: Callable[..., Awaitable[None]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """提交一个异步任务."""
        ...
