"""mk_tenant_config — 租户配置(数据表设计 §4.1)."""
from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import JSON, BigInteger, DateTime, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class MkTenantConfig(Base):
    """租户配置表.

    Phase 2 第一个示例表,验证 SQLAlchemy + Alembic + SQLite 链路通顺。
    后续按数据表设计 §4 逐一添加 mk_warehouse_mapping / mk_calc_run 等。
    """

    __tablename__ = "mk_tenant_config"

    tenant_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_name: Mapped[str | None] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Shanghai")
    daily_push_time: Mapped[time | None] = mapped_column(Time)
    source_refresh_times_json: Mapped[list[str] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<MkTenantConfig tenant_id={self.tenant_id} name={self.tenant_name!r}>"
