"""mk_export_task — 异步导出任务表（数据表设计 §4.12）.

超过 5000 条进入异步导出;Phase 1 实现任务记录和状态展示。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class MkExportTask(Base):
    """异步导出任务."""

    __tablename__ = "mk_export_task"
    __table_args__ = (
        Index("ix_mk_export_task_tenant", "tenant_id"),
        Index("ix_mk_export_task_status", "status"),
    )

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    created_by: Mapped[str | None] = mapped_column(String(50))
    scope_json: Mapped[dict | list | None] = mapped_column(JSON)
    row_count: Mapped[int | None] = mapped_column(Integer)
    # pending / running / success / failed / expired
    status: Mapped[str] = mapped_column(String(20), default="pending")
    file_url: Mapped[str | None] = mapped_column(String(500))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    error_message: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<MkExportTask id={self.task_id} status={self.status} "
            f"rows={self.row_count}>"
        )
