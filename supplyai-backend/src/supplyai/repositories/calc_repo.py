"""Calc Engine 数据访问层 — 加载 + 持久化."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.models.mk import (
    MkCalcRun,
    MkListingProductSources,
    MkReplenishmentRule,
    MkRuleLogisticsMethod,
    MkSkuForecastDaily,
    MkSupplySkuDailyStat,
)
from supplyai.models.rl import (
    RlAmzManageFbaInventory,
    RlAmzSalesDailyReport,
    RlInventoryDetail,
)


class CalcRepository:
    """Calc Engine 专用数据访问."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_fba_listings(
        self, tenant_id: int
    ) -> list[MkListingProductSources]:
        """所有 FBA listing(Phase 1 算子只跑 FBA)."""
        result = await self._session.execute(
            select(MkListingProductSources).where(
                MkListingProductSources.tenant_id == tenant_id,
                MkListingProductSources.delivery_method == "FBA",
            )
        )
        return list(result.scalars().all())

    async def fba_inventory_map(
        self, tenant_id: int
    ) -> dict[tuple[int | None, str], RlAmzManageFbaInventory]:
        """按 (mall_id, msku) 索引 FBA 库存."""
        result = await self._session.execute(
            select(RlAmzManageFbaInventory).where(
                RlAmzManageFbaInventory.tenant_id == tenant_id,
                RlAmzManageFbaInventory.del_flag == 0,
            )
        )
        out: dict[tuple[int | None, str], RlAmzManageFbaInventory] = {}
        for row in result.scalars().all():
            if row.msku:
                out[(row.mall_id, row.msku)] = row
        return out

    async def local_inventory_sum(
        self, tenant_id: int
    ) -> dict[tuple[int | None, str], int]:
        """聚合本地仓 available_quantity(同 mall_id+msku 求和)."""
        result = await self._session.execute(
            select(RlInventoryDetail).where(
                RlInventoryDetail.tenant_id == tenant_id,
                RlInventoryDetail.del_flag == 0,
            )
        )
        agg: dict[tuple[int | None, str], int] = defaultdict(int)
        for row in result.scalars().all():
            if row.msku:
                agg[(row.mall_id, row.msku)] += row.available_quantity or 0
        return dict(agg)

    async def sales_history(
        self,
        *,
        tenant_id: int,
        end_date: date,
        days: int,
    ) -> dict[tuple[int | None, str], list[RlAmzSalesDailyReport]]:
        """加载最近 days 天销量,按 (mall_id, msku) 分组并按日期升序."""
        start_str = (end_date - timedelta(days=days)).isoformat()
        result = await self._session.execute(
            select(RlAmzSalesDailyReport)
            .where(
                RlAmzSalesDailyReport.tenant_id == tenant_id,
                RlAmzSalesDailyReport.year_month_day >= start_str,
            )
            .order_by(RlAmzSalesDailyReport.year_month_day.asc())
        )
        out: dict[tuple[int | None, str], list[RlAmzSalesDailyReport]] = defaultdict(list)
        for row in result.scalars().all():
            if row.msku:
                out[(row.mall_id, row.msku)].append(row)
        return dict(out)

    async def list_rules(self, tenant_id: int) -> list[MkReplenishmentRule]:
        result = await self._session.execute(
            select(MkReplenishmentRule).where(
                MkReplenishmentRule.tenant_id == tenant_id,
                MkReplenishmentRule.enabled == 1,
            )
        )
        return list(result.scalars().all())

    async def rule_logistics_days(self, rule_ids: list[str]) -> dict[str, tuple[int, ...]]:
        if not rule_ids:
            return {}
        result = await self._session.execute(
            select(MkRuleLogisticsMethod).where(
                MkRuleLogisticsMethod.rule_id.in_(rule_ids),
                MkRuleLogisticsMethod.is_active == 1,
            )
        )
        out: dict[str, list[int]] = defaultdict(list)
        for row in result.scalars().all():
            out[row.rule_id].append(int(row.logistics_days or 0))
        return {rule_id: tuple(days) for rule_id, days in out.items()}

    async def insert_calc_run(self, run: MkCalcRun) -> MkCalcRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def bulk_insert_snapshots(
        self, rows: list[MkSupplySkuDailyStat]
    ) -> None:
        if not rows:
            return
        self._session.add_all(rows)
        await self._session.flush()

    async def bulk_insert_forecast(self, rows: list[MkSkuForecastDaily]) -> None:
        if not rows:
            return
        self._session.add_all(rows)
        await self._session.flush()

    async def update_run_status(
        self,
        calc_run_id: str,
        *,
        status: str,
        error_message: str | None = None,
    ) -> None:
        run = await self._session.scalar(
            select(MkCalcRun).where(MkCalcRun.calc_run_id == calc_run_id)
        )
        if run is None:
            return
        run.status = status
        if error_message:
            run.error_message = error_message[:500]
