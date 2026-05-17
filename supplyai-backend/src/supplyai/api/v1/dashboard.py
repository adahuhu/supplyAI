"""Dashboard API 端点 — 全部 POST."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.db import get_db_session
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.schemas.dashboard import (
    AlertsDTO,
    AlertsRequest,
    DashboardSnapshotDTO,
    DashboardSnapshotRequest,
    FiltersDTO,
    FiltersRequest,
    FinanceDTO,
    FinanceRequest,
    HolidayDeleteDTO,
    HolidayDeleteRequest,
    HolidayItem,
    HolidayUpsertRequest,
    HolidaysDTO,
    HolidaysRequest,
    RiskQueueDTO,
    RiskQueueRequest,
    StoresDTO,
    StoresRequest,
)
from supplyai.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _build_service(session: AsyncSession) -> DashboardService:
    return DashboardService(DashboardRepository(session))


@router.post("/snapshot", response_model=DashboardSnapshotDTO)
async def snapshot(
    req: DashboardSnapshotRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DashboardSnapshotDTO:
    """工作台聚合: 风险分布 / 7 天断货 / 建议采购汇总 / 多币种."""
    return await _build_service(session).snapshot(req)


@router.post("/risk-queue", response_model=RiskQueueDTO)
async def risk_queue(
    req: RiskQueueRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RiskQueueDTO:
    """工作台风险队列: P1 优先 + 断货日期升序,带 action_hint."""
    return await _build_service(session).risk_queue(req)


@router.post("/filters", response_model=FiltersDTO)
async def filters(
    req: FiltersRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FiltersDTO:
    """顶部过滤器选项 — store / country / owner 三组,各带计数."""
    return await _build_service(session).filters(req)


@router.post("/stores", response_model=StoresDTO)
async def stores(
    req: StoresRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StoresDTO:
    """侧栏"店铺空间" — 每店铺 SKU 数 + 风险分布,P1 多的排前."""
    return await _build_service(session).stores(req)


@router.post("/finance", response_model=FinanceDTO)
async def finance(
    req: FinanceRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FinanceDTO:
    """昨日财务摘要 + 同比 — 派生自 rl_amz_sales_daily_report."""
    return await _build_service(session).finance(req)


@router.post("/data-quality-alerts", response_model=AlertsDTO)
async def data_quality_alerts(
    req: AlertsRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AlertsDTO:
    """工作台"需关注"面板 — 数据质量 / 规则配置 / 风险变化告警."""
    return await _build_service(session).alerts(req)


@router.post("/holidays", response_model=HolidaysDTO)
async def holidays(
    req: HolidaysRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HolidaysDTO:
    """节日列表 — 前端 SKU 详情节日色带 + Calc Engine 节日乘数都用."""
    return await _build_service(session).holidays(req)


@router.post("/holidays/upsert", response_model=HolidayItem)
async def upsert_holiday(
    req: HolidayUpsertRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HolidayItem:
    """新建或更新一条节日 — 节日色带前端拖动后调用."""
    result = await _build_service(session).upsert_holiday(req)
    await session.commit()
    return result


@router.post("/holidays/delete", response_model=HolidayDeleteDTO)
async def delete_holiday(
    req: HolidayDeleteRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> HolidayDeleteDTO:
    """删除一条节日 — 软删除后不再参与大促提醒和预测计算."""
    result = await _build_service(session).delete_holiday(req)
    await session.commit()
    return result
