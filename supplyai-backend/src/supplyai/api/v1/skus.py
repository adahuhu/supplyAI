"""SKU API 端点 — 全部 POST."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.db import get_db_session
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.repositories.sku_repo import SkuRepository
from supplyai.schemas.common import PageResult
from supplyai.schemas.sku import (
    InventoryOverrideDTO,
    InventoryOverrideUpsertRequest,
    SkuDetailDTO,
    SkuDetailRequest,
    SkuListRequest,
    SkuSummaryDTO,
    SkuTrendsDTO,
    SkuTrendsRequest,
)
from supplyai.services.sku_service import SkuService

router = APIRouter(prefix="/skus", tags=["skus"])


def _build_service(session: AsyncSession) -> SkuService:
    return SkuService(SkuRepository(session), DashboardRepository(session))


@router.post("/list", response_model=PageResult[SkuSummaryDTO])
async def list_skus(
    req: SkuListRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PageResult[SkuSummaryDTO]:
    """备货列表: 风险/店铺/关键字过滤、风险+断货排序、分页(Phase 1 仅 FBA)."""
    return await _build_service(session).list_skus(req)


@router.post("/detail", response_model=SkuDetailDTO)
async def sku_detail(
    req: SkuDetailRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SkuDetailDTO:
    """SKU 详情: summary + 预测序列 + 在途单据 + 数据质量."""
    return await _build_service(session).detail(req)


@router.post("/trends", response_model=SkuTrendsDTO)
async def sku_trends(
    req: SkuTrendsRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SkuTrendsDTO:
    """SKU 趋势: 历史销量(rl_amz_sales_daily_report) + 未来预测."""
    return await _build_service(session).trends(req)


@router.post("/inventory-overrides/upsert", response_model=InventoryOverrideDTO)
async def upsert_inventory_override(
    req: InventoryOverrideUpsertRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryOverrideDTO:
    """SKU 趋势图库存点位保存."""
    return await _build_service(session).upsert_inventory_override(req)
