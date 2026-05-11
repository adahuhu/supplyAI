"""规则 API — POST /rules/*."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.db import get_db_session
from supplyai.repositories.rule_repo import RuleRepository
from supplyai.schemas.rule import (
    ForecastRuleDTO,
    ForecastRuleListRequest,
    ForecastRuleListResponse,
    ForecastRuleUpsertRequest,
    RuleDTO,
    RuleListRequest,
    RuleListResponse,
    RuleStateRequest,
    RuleUpsertRequest,
)
from supplyai.services.rule_service import ForecastRuleService, RuleService

router = APIRouter(prefix="/rules", tags=["rules"])


def _build_service(session: AsyncSession) -> RuleService:
    return RuleService(RuleRepository(session))


@router.post("/list", response_model=RuleListResponse)
async def list_rules(
    req: RuleListRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RuleListResponse:
    return await _build_service(session).list_rules(req)


@router.post("/upsert", response_model=RuleDTO)
async def upsert_rule(
    req: RuleUpsertRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RuleDTO:
    """新建或更新一条规则(rule_id 不传 = 新建)."""
    result = await _build_service(session).upsert(req)
    await session.commit()
    return result


@router.post("/disable", response_model=RuleDTO)
async def disable_rule(
    req: RuleStateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RuleDTO:
    """禁用规则(不删除,enabled=False)."""
    result = await _build_service(session).disable(
        tenant_id=req.tenant_id, rule_id=req.rule_id
    )
    await session.commit()
    return result


@router.post("/forecast/list", response_model=ForecastRuleListResponse)
async def list_forecast_rules(
    req: ForecastRuleListRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ForecastRuleListResponse:
    return await ForecastRuleService(session).list_rules(req)


@router.post("/forecast/upsert", response_model=ForecastRuleDTO)
async def upsert_forecast_rule(
    req: ForecastRuleUpsertRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ForecastRuleDTO:
    """新建或更新销量预测规则(rule_id 不传 = 新建)."""
    result = await ForecastRuleService(session).upsert(req)
    await session.commit()
    return result
