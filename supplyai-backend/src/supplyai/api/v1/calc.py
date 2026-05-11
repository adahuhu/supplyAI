"""计算批次相关端点 — 全部 POST,接入 mk_calc_run."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.db import get_db_session
from supplyai.models.mk import MkCalcRun
from supplyai.repositories.calc_repo import CalcRepository
from supplyai.services.calc_service import CalcService
from supplyai.utils.exceptions import CalcRunNotFoundException

router = APIRouter(prefix="/calc", tags=["calc"])


class CalcLatestRequest(BaseModel):
    tenant_id: int


class CalcStatusRequest(BaseModel):
    calc_run_id: str


class CalcRunRequest(BaseModel):
    tenant_id: int
    run_type: Literal["scheduled", "rule_changed", "manual"] = "manual"
    rule_version: str | None = None


class CalcRunDTO(BaseModel):
    """对应前端 ViewModel: CalcRun."""

    model_config = ConfigDict(from_attributes=True)

    calc_run_id: str
    tenant_id: int
    stat_date: str  # YYYY-MM-DD
    run_type: Literal["scheduled", "rule_changed", "manual"]
    run_at: datetime
    rule_version: str | None = None
    status: Literal["running", "success", "failed"]


class CalcRunStatusDTO(BaseModel):
    """对应前端 ViewModel: CalcRunStatus."""

    calc_run_id: str
    status: Literal["pending", "running", "success", "failed"]
    progress: int | None = None  # 0-100
    completed_at: datetime | None = None
    error_message: str | None = None


def _to_dto(run: MkCalcRun) -> CalcRunDTO:
    return CalcRunDTO(
        calc_run_id=run.calc_run_id,
        tenant_id=run.tenant_id,
        stat_date=run.stat_date.isoformat(),
        run_type=run.run_type,  # type: ignore[arg-type]
        run_at=run.run_at,
        rule_version=run.rule_version,
        status=run.status,  # type: ignore[arg-type]
    )


def _progress_for(status: str) -> int:
    return {"running": 50, "success": 100, "failed": 100, "pending": 0}.get(status, 0)


@router.post("/latest", response_model=CalcRunDTO)
async def get_latest_calc_run(
    req: CalcLatestRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CalcRunDTO:
    """获取最新成功 calc_run."""
    run = await session.scalar(
        select(MkCalcRun)
        .where(MkCalcRun.tenant_id == req.tenant_id, MkCalcRun.status == "success")
        .order_by(desc(MkCalcRun.run_at))
        .limit(1)
    )
    if run is None:
        raise CalcRunNotFoundException(req.tenant_id)
    return _to_dto(run)


@router.post("/run", response_model=CalcRunDTO)
async def trigger_calc_run(
    req: CalcRunRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CalcRunDTO:
    """触发一次完整 Calc Engine 计算 — 同步执行,写新批次 + 快照 + 预测."""
    service = CalcService(CalcRepository(session))
    run = await service.run(
        tenant_id=req.tenant_id,
        run_type=req.run_type,
        rule_version=req.rule_version,
    )
    await session.commit()
    return _to_dto(run)


@router.post("/status", response_model=CalcRunStatusDTO)
async def get_calc_run_status(
    req: CalcStatusRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CalcRunStatusDTO:
    """查询计算批次状态."""
    run = await session.scalar(
        select(MkCalcRun).where(MkCalcRun.calc_run_id == req.calc_run_id)
    )
    if run is None:
        raise CalcRunNotFoundException(calc_run_id=req.calc_run_id)
    return CalcRunStatusDTO(
        calc_run_id=run.calc_run_id,
        status=run.status,  # type: ignore[arg-type]
        progress=_progress_for(run.status),
        completed_at=run.run_at if run.status in {"success", "failed"} else None,
        error_message=run.error_message,
    )
