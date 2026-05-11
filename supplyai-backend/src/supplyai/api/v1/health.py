"""健康检查端点 — DB / AI / Cache 可达性."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai import __version__
from supplyai.config import settings
from supplyai.db import get_db_session

router = APIRouter(tags=["health"])


class ComponentStatus(BaseModel):
    name: str
    status: Literal["ok", "degraded", "error"]
    message: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    version: str
    env: str
    timestamp: datetime
    components: list[ComponentStatus]


@router.get("/_health", response_model=HealthResponse)
async def health(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HealthResponse:
    """检查所有依赖组件状态."""
    components: list[ComponentStatus] = []

    # DB
    try:
        await session.execute(text("SELECT 1"))
        components.append(
            ComponentStatus(name="database", status="ok", message=settings.database_url.split("@")[-1])
        )
    except Exception as e:
        components.append(ComponentStatus(name="database", status="error", message=str(e)))

    # 缓存
    components.append(
        ComponentStatus(
            name="cache",
            status="ok",
            message=f"backend={settings.cache_backend}",
        )
    )

    # AI
    components.append(
        ComponentStatus(
            name="ai",
            status="ok",
            message=f"provider={settings.ai_provider}",
        )
    )

    # 任务调度
    components.append(
        ComponentStatus(
            name="tasks",
            status="ok",
            message=f"runner={settings.task_runner}",
        )
    )

    overall: Literal["ok", "degraded", "error"] = (
        "ok" if all(c.status == "ok" for c in components)
        else "degraded" if any(c.status == "ok" for c in components)
        else "error"
    )

    return HealthResponse(
        status=overall,
        version=__version__,
        env=settings.app_env,
        timestamp=datetime.now(UTC),
        components=components,
    )
