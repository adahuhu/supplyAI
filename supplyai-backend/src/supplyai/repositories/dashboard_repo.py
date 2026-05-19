"""Dashboard 聚合查询."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from datetime import datetime

from sqlalchemy import asc, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.models.mk import MkCalcRun, MkSupplySkuDailyStat
from supplyai.models.rl import RlMall


class DashboardRepository:
    """Dashboard 数据聚合."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def latest_calc_run_id(self, tenant_id: int) -> str | None:
        """取最新成功 calc_run_id."""
        return await self._session.scalar(
            select(MkCalcRun.calc_run_id)
            .where(MkCalcRun.tenant_id == tenant_id, MkCalcRun.status == "success")
            .order_by(desc(MkCalcRun.run_at))
            .limit(1)
        )

    async def get_calc_run(self, calc_run_id: str) -> MkCalcRun | None:
        return await self._session.scalar(
            select(MkCalcRun).where(MkCalcRun.calc_run_id == calc_run_id)
        )

    async def risk_counts(
        self,
        calc_run_id: str,
        tenant_id: int,
        *,
        mall_ids: list[int] | None = None,
        country_codes: list[str] | None = None,
        owners: list[str] | None = None,
    ) -> dict[str, int]:
        """风险等级分布,可选 mall/country/owner 过滤."""
        from supplyai.models.mk import MkListingProductSources

        stat = MkSupplySkuDailyStat
        filters = [
            stat.calc_run_id == calc_run_id,
            stat.tenant_id == tenant_id,
        ]
        if mall_ids:
            filters.append(stat.mall_id.in_(mall_ids))
        if country_codes:
            filters.append(stat.country_code.in_(country_codes))

        query = select(stat.risk_level, func.count(stat.id))
        if owners:
            # owner 字段在 lps 表,需 join
            lps = MkListingProductSources
            query = query.join(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
            filters.append(lps.owner.in_(owners))

        query = query.where(*filters).group_by(stat.risk_level)
        result = await self._session.execute(query)
        counts = {"p1": 0, "p2": 0, "p3": 0, "safe": 0}
        for level, cnt in result:
            counts[level] = cnt
        return counts

    async def snapshot_aggregates(
        self,
        calc_run_id: str,
        tenant_id: int,
        *,
        mall_ids: list[int] | None = None,
        country_codes: list[str] | None = None,
        owners: list[str] | None = None,
    ) -> tuple[int, int]:
        """快照聚合:(total_sales_7d, total_stock) 求和,可选过滤."""
        from supplyai.models.mk import MkListingProductSources

        stat = MkSupplySkuDailyStat
        filters = [
            stat.calc_run_id == calc_run_id,
            stat.tenant_id == tenant_id,
        ]
        if mall_ids:
            filters.append(stat.mall_id.in_(mall_ids))
        if country_codes:
            filters.append(stat.country_code.in_(country_codes))

        query = select(
            func.coalesce(func.sum(stat.sales_7d), 0),
            func.coalesce(func.sum(stat.total_stock), 0),
        )
        if owners:
            lps = MkListingProductSources
            query = query.join(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
            filters.append(lps.owner.in_(owners))

        s7, ts = (await self._session.execute(query.where(*filters))).one()
        return int(s7 or 0), int(ts or 0)

    async def stockout_7_count(
        self,
        calc_run_id: str,
        tenant_id: int,
        *,
        mall_ids: list[int] | None = None,
        country_codes: list[str] | None = None,
        owners: list[str] | None = None,
        stockout_since: datetime | None = None,
    ) -> int:
        """7 天内 FBA 断货 SKU 数,可选过滤."""
        from supplyai.models.mk import MkListingProductSources, MkStockoutEvent

        stat = MkSupplySkuDailyStat
        filters = [
            stat.calc_run_id == calc_run_id,
            stat.tenant_id == tenant_id,
        ]
        if stockout_since is not None:
            filters.append(
                select(MkStockoutEvent.event_id)
                .where(
                    MkStockoutEvent.tenant_id == stat.tenant_id,
                    MkStockoutEvent.mall_id == stat.mall_id,
                    MkStockoutEvent.msku == stat.msku,
                    MkStockoutEvent.start_at >= stockout_since,
                )
                .exists()
            )
        if mall_ids:
            filters.append(stat.mall_id.in_(mall_ids))
        if country_codes:
            filters.append(stat.country_code.in_(country_codes))

        query = select(func.count(stat.id))
        if owners:
            lps = MkListingProductSources
            query = query.join(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
            filters.append(lps.owner.in_(owners))

        cnt = await self._session.scalar(query.where(*filters))
        return cnt or 0

    async def suggest_summary(
        self,
        calc_run_id: str,
        tenant_id: int,
        *,
        mall_ids: list[int] | None = None,
        country_codes: list[str] | None = None,
        owners: list[str] | None = None,
    ) -> tuple[int, int, Decimal, dict[str, Decimal]]:
        """建议采购汇总: (sku_count, total_qty, total_amount_base, by_currency)."""
        from supplyai.models.mk import MkListingProductSources

        stat = MkSupplySkuDailyStat
        base_filters = [
            stat.calc_run_id == calc_run_id,
            stat.tenant_id == tenant_id,
            stat.suggest_purchase == 1,
        ]
        if mall_ids:
            base_filters.append(stat.mall_id.in_(mall_ids))
        if country_codes:
            base_filters.append(stat.country_code.in_(country_codes))

        def _maybe_join_owners(q):
            if not owners:
                return q
            lps = MkListingProductSources
            return q.join(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
        filters = list(base_filters)
        if owners:
            filters.append(MkListingProductSources.owner.in_(owners))

        total_q = _maybe_join_owners(select(
            func.count(stat.id),
            func.coalesce(func.sum(stat.suggest_qty), 0),
            func.coalesce(func.sum(stat.suggest_amount_base), 0),
        )).where(*filters)
        sku_count, total_qty, total_amount_base = (await self._session.execute(total_q)).one()

        # 按币种分组
        by_q = _maybe_join_owners(select(
            stat.currency,
            func.coalesce(func.sum(stat.suggest_amount), 0),
        )).where(*filters).group_by(stat.currency)
        by_currency_result = await self._session.execute(by_q)
        by_currency: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for currency, amount in by_currency_result:
            if currency:
                by_currency[currency] = Decimal(amount)

        return (
            int(sku_count or 0),
            int(total_qty or 0),
            Decimal(total_amount_base),
            dict(by_currency),
        )

    async def latest_sales_date(self, tenant_id: int) -> str | None:
        """返回 rl_amz_sales_daily_report 中最大 year_month_day."""
        from supplyai.models.rl import RlAmzSalesDailyReport

        return await self._session.scalar(
            select(func.max(RlAmzSalesDailyReport.year_month_day)).where(
                RlAmzSalesDailyReport.tenant_id == tenant_id
            )
        )

    async def daily_sales_aggregate(
        self,
        *,
        tenant_id: int,
        ymd: str,
        mall_ids: list[int] | None = None,
        country_codes: list[str] | None = None,
    ) -> tuple[int, Decimal, Decimal]:
        """指定日期的 (sales_volume, gmv, cost) 聚合,可选 mall/country 过滤."""
        from supplyai.models.mk import MkListingProductSources
        from supplyai.models.rl import RlAmzSalesDailyReport

        sales = RlAmzSalesDailyReport
        lps = MkListingProductSources

        filters = [
            sales.tenant_id == tenant_id,
            sales.year_month_day == ymd,
        ]
        if mall_ids:
            filters.append(sales.mall_id.in_(mall_ids))
        if country_codes:
            filters.append(sales.country_code.in_(country_codes))

        agg_q = select(
            func.coalesce(func.sum(sales.sales_volume), 0),
            func.coalesce(func.sum(sales.sales), 0),
        ).where(*filters)
        sv, gmv = (await self._session.execute(agg_q)).one()

        cost_q = select(
            func.coalesce(
                func.sum(
                    func.coalesce(sales.sales_volume, 0)
                    * func.coalesce(lps.unit_cost, 0)
                ),
                0,
            )
        ).select_from(
            sales.__table__.outerjoin(
                lps.__table__,
                (sales.tenant_id == lps.tenant_id)
                & (sales.listing_id == lps.listing_id),
            )
        ).where(*filters)
        cost = (await self._session.scalar(cost_q)) or Decimal("0")
        return int(sv or 0), Decimal(gmv or 0), Decimal(cost)

    async def upsert_holiday(self, payload: dict) -> "MkHoliday":
        from supplyai.models.mk import MkHoliday
        from decimal import Decimal as _D

        existing = await self._session.scalar(
            select(MkHoliday).where(
                MkHoliday.tenant_id == payload["tenant_id"],
                MkHoliday.holiday_id == payload["holiday_id"],
            )
        )
        if existing is None:
            existing = MkHoliday(
                holiday_id=payload["holiday_id"],
                tenant_id=payload["tenant_id"],
                source_type="mock",
            )
            self._session.add(existing)
        existing.name = payload["name"]
        existing.peak_date = payload["peak_date"]
        existing.days_before = payload["days_before"]
        existing.days_after = payload["days_after"]
        existing.sales_multiplier = _D(str(payload["sales_multiplier"]))
        existing.color = payload.get("color")
        existing.flag = payload.get("flag")
        existing.country_code = payload.get("country_code")
        existing.enabled = 1 if payload.get("enabled", True) else 0
        await self._session.flush()
        return existing

    async def delete_holiday(self, *, tenant_id: int, holiday_id: str) -> bool:
        from supplyai.models.mk import MkHoliday

        existing = await self._session.scalar(
            select(MkHoliday).where(
                MkHoliday.tenant_id == tenant_id,
                MkHoliday.holiday_id == holiday_id,
            )
        )
        if existing is None:
            return False
        existing.enabled = 0
        await self._session.flush()
        return True

    async def list_holidays(
        self, *, tenant_id: int, country_code: str | None = None
    ) -> list:
        from supplyai.models.mk import MkHoliday

        filters = [MkHoliday.tenant_id == tenant_id, MkHoliday.enabled == 1]
        if country_code:
            filters.append(
                (MkHoliday.country_code == country_code) | (MkHoliday.country_code.is_(None))
            )
        rows = (
            await self._session.execute(
                select(MkHoliday).where(*filters).order_by(MkHoliday.peak_date.asc())
            )
        ).scalars().all()
        return list(rows)

    async def alert_counts(
        self, *, calc_run_id: str, tenant_id: int
    ) -> dict[str, int]:
        """派生数据质量告警计数."""
        stat = MkSupplySkuDailyStat
        # forecast_source='default' 的 SKU 数(预测样本不足)
        forecast_default = await self._session.scalar(
            select(func.count(stat.id)).where(
                stat.calc_run_id == calc_run_id,
                stat.tenant_id == tenant_id,
                stat.forecast_source == "default",
            )
        )
        # unit_cost 为 NULL 的 SKU 数(成本数据缺失)
        cost_missing = await self._session.scalar(
            select(func.count(stat.id)).where(
                stat.calc_run_id == calc_run_id,
                stat.tenant_id == tenant_id,
                stat.unit_cost.is_(None),
            )
        )
        # P1 风险但 suggest_qty=0 的(算异常,需复核)
        review = await self._session.scalar(
            select(func.count(stat.id)).where(
                stat.calc_run_id == calc_run_id,
                stat.tenant_id == tenant_id,
                stat.risk_level == "p1",
                stat.suggest_qty == 0,
            )
        )
        return {
            "forecast_default": int(forecast_default or 0),
            "cost_missing": int(cost_missing or 0),
            "review_p1_no_suggest": int(review or 0),
        }

    async def store_risk_summary(
        self, *, calc_run_id: str, tenant_id: int
    ) -> list[tuple[int, str, str | None, dict[str, int]]]:
        """每个店铺的 SKU 总数 + 风险等级分布.

        返回 [(mall_id, mall_name, country_code, {p1, p2, p3, safe -> count}), ...]
        """
        stat = MkSupplySkuDailyStat
        q = (
            select(
                stat.mall_id,
                RlMall.mall_name,
                stat.country_code,
                stat.risk_level,
                func.count(stat.id),
            )
            .outerjoin(RlMall, RlMall.mall_id == stat.mall_id)
            .where(
                stat.calc_run_id == calc_run_id,
                stat.tenant_id == tenant_id,
                stat.delivery_method == "FBA",
                stat.mall_id.isnot(None),
            )
            .group_by(stat.mall_id, RlMall.mall_name, stat.country_code, stat.risk_level)
        )
        rows = (await self._session.execute(q)).all()

        # 聚合到 (mall_id) 级
        bucket: dict[int, dict] = {}
        for mall_id, mall_name, cc, level, cnt in rows:
            entry = bucket.setdefault(
                mall_id,
                {
                    "mall_name": mall_name,
                    "country_code": cc,
                    "counts": {"p1": 0, "p2": 0, "p3": 0, "safe": 0},
                },
            )
            entry["counts"][level] = int(cnt)
        return [
            (mid, b["mall_name"] or f"mall {mid}", b["country_code"], b["counts"])
            for mid, b in bucket.items()
        ]

    async def filter_options(
        self, *, calc_run_id: str, tenant_id: int
    ) -> tuple[
        list[tuple[int | None, str | None, int]],
        list[tuple[str | None, int]],
        list[tuple[str | None, int]],
        list[tuple[str | None, int]],
        list[tuple[str | None, int]],
    ]:
        """工作台顶部过滤器:返回 (stores, countries, owners) 三组聚合.

        stores: [(mall_id, mall_name, count), ...]
        countries: [(country_code, count), ...]
        owners: [(owner, count), ...]
        都基于当前批次的 FBA 快照 + 关联 listing meta。
        """
        from supplyai.models.mk import MkListingProductSources

        stat = MkSupplySkuDailyStat
        lps = MkListingProductSources

        base = (
            select(stat.mall_id, RlMall.mall_name, func.count(stat.id))
            .outerjoin(RlMall, RlMall.mall_id == stat.mall_id)
            .where(
                stat.calc_run_id == calc_run_id,
                stat.tenant_id == tenant_id,
                stat.delivery_method == "FBA",
            )
            .group_by(stat.mall_id, RlMall.mall_name)
        )
        store_rows = (await self._session.execute(base)).all()

        country_q = (
            select(stat.country_code, func.count(stat.id))
            .where(
                stat.calc_run_id == calc_run_id,
                stat.tenant_id == tenant_id,
                stat.delivery_method == "FBA",
            )
            .group_by(stat.country_code)
        )
        country_rows = (await self._session.execute(country_q)).all()

        # owner 来自 lps,通过 listing_id join
        owner_q = (
            select(lps.owner, func.count(stat.id))
            .join(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
            .where(
                stat.calc_run_id == calc_run_id,
                stat.tenant_id == tenant_id,
                stat.delivery_method == "FBA",
            )
            .group_by(lps.owner)
        )
        owner_rows = (await self._session.execute(owner_q)).all()

        # brand / category 也来自 lps,通过 listing_id join
        brand_q = (
            select(lps.brand, func.count(stat.id))
            .join(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
            .where(
                stat.calc_run_id == calc_run_id,
                stat.tenant_id == tenant_id,
                stat.delivery_method == "FBA",
            )
            .group_by(lps.brand)
        )
        brand_rows = (await self._session.execute(brand_q)).all()

        category_q = (
            select(lps.category, func.count(stat.id))
            .join(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
            .where(
                stat.calc_run_id == calc_run_id,
                stat.tenant_id == tenant_id,
                stat.delivery_method == "FBA",
            )
            .group_by(lps.category)
        )
        category_rows = (await self._session.execute(category_q)).all()

        return (
            [(m_id, m_name, int(cnt)) for m_id, m_name, cnt in store_rows],
            [(c, int(cnt)) for c, cnt in country_rows],
            [(o, int(cnt)) for o, cnt in owner_rows],
            [(b, int(cnt)) for b, cnt in brand_rows],
            [(cat, int(cnt)) for cat, cnt in category_rows],
        )

    async def risk_queue(
        self,
        *,
        calc_run_id: str,
        tenant_id: int,
        priorities: list[str] | None = None,
        mall_ids: list[int] | None = None,
        country_codes: list[str] | None = None,
        limit: int = 10,
    ) -> tuple[list[tuple[MkSupplySkuDailyStat, str | None]], int]:
        """风险队列: P1 优先 + 断货日期升序,join store_name."""
        stat = MkSupplySkuDailyStat
        filters = [
            stat.calc_run_id == calc_run_id,
            stat.tenant_id == tenant_id,
            stat.delivery_method == "FBA",
        ]
        if priorities:
            filters.append(stat.risk_level.in_(priorities))
        if mall_ids:
            filters.append(stat.mall_id.in_(mall_ids))
        if country_codes:
            filters.append(stat.country_code.in_(country_codes))

        total = await self._session.scalar(
            select(func.count(stat.id)).where(*filters)
        )

        priority_order = case(
            {"p1": 0, "p2": 1, "p3": 2, "safe": 3},
            value=stat.risk_level,
            else_=99,
        )
        query = (
            select(stat, RlMall.mall_name)
            .outerjoin(RlMall, RlMall.mall_id == stat.mall_id)
            .where(*filters)
            .order_by(
                priority_order.asc(),
                stat.stockout_date.asc().nulls_last(),
                stat.sellable_days.asc().nulls_last(),
            )
            .limit(limit)
        )
        result = await self._session.execute(query)
        rows = [(row[0], row[1]) for row in result.all()]
        return rows, int(total or 0)
