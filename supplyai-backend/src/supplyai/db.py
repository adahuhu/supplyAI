"""SQLAlchemy 数据库连接 — async session factory。"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from supplyai.config import settings


def make_engine(url: str | None = None) -> AsyncEngine:
    """创建 async 数据库引擎.

    SQLite 与 MySQL 共用同一份 SQLAlchemy 抽象;driver 由 URL scheme 决定。
    """
    db_url = url or settings.database_url

    # SQLite 特殊配置
    if db_url.startswith("sqlite"):
        return create_async_engine(
            db_url,
            echo=settings.log_level == "DEBUG",
            future=True,
            connect_args={"check_same_thread": False},
        )

    # MySQL / 其它
    return create_async_engine(
        db_url,
        echo=settings.log_level == "DEBUG",
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )


# 全局 engine + session factory（应用启动时创建）
engine: AsyncEngine = make_engine()
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖 — 每请求一个 session."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
