"""FastAPI 应用入口."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from supplyai import __version__
from supplyai.api.v1 import api_v1_router
from supplyai.config import settings
from supplyai.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期 — 启动 / 关闭钩子."""
    configure_logging(level=settings.log_level, fmt=settings.log_format)
    logger.info(
        "supplyai_starting",
        version=__version__,
        env=settings.app_env,
        db=("sqlite" if settings.is_sqlite else "mysql"),
        ai_provider=settings.ai_provider,
        cache_backend=settings.cache_backend,
        task_runner=settings.task_runner,
    )
    yield
    logger.info("supplyai_shutting_down")


app = FastAPI(
    title="SupplyAI Backend",
    description="供应链分析工作台 — Python 单服务（API + Calc + AI + 后台任务）",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS — 本地开发允许所有来源；生产应锁定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_local else [],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 v1 路由
app.include_router(api_v1_router, prefix="/api/supplyai")


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {
        "name": "SupplyAI Backend",
        "version": __version__,
        "env": settings.app_env,
        "docs": "/docs",
    }
