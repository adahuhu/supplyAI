"""鉴权端点 — Phase 1 仅 /auth/me 占位.

鉴权未上线时返回 settings.default_tenant_id + tenant_config 的展示信息。
Phase 6 接入 JWT 后,改从 token 读 user_id → 查 rl_user.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.config import settings
from supplyai.db import get_db_session
from supplyai.models.mk import MkTenantConfig

router = APIRouter(prefix="/auth", tags=["auth"])


class MeRequest(BaseModel):
    pass  # 鉴权上线后 token 在 header,这里保持空 body


class MeDTO(BaseModel):
    tenant_id: int
    display_name: str  # 用户显示名(占位)
    role_label: str  # 角色标签
    workspace: str  # 租户工作区名
    timezone: str


@router.post("/me", response_model=MeDTO)
async def me(
    _req: MeRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MeDTO:
    tenant_id = settings.default_tenant_id
    config = await session.scalar(
        select(MkTenantConfig).where(MkTenantConfig.tenant_id == tenant_id)
    )
    workspace = (config.tenant_name if config else None) or f"tenant-{tenant_id}"
    timezone = (config.timezone if config else None) or "Asia/Shanghai"
    return MeDTO(
        tenant_id=tenant_id,
        display_name="演示账户",
        role_label="运营 / 备货管理",
        workspace=workspace,
        timezone=timezone,
    )
