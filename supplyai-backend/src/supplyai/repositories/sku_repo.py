"""SKU 数据查询封装."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import asc, case, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.models.mk import (
    MkListingProductSources,
    MkPurchaseDraft,
    MkSkuForecastDaily,
    MkSkuInboundDetail,
    MkSkuInventoryOverride,
    MkStockoutEvent,
    MkSupplySkuDailyStat,
)
from supplyai.models.rl import RlAmzSalesDailyReport, RlFbaShipmentItem, RlMall


class SkuRepository:
    """SKU 列表 / 详情查询."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_skus(
        self,
        *,
        calc_run_id: str,
        tenant_id: int,
        priorities: list[str] | None = None,
        mall_ids: list[int] | None = None,
        country_codes: list[str] | None = None,
        tags: list[str] | None = None,
        keyword: str | None = None,
        suggest_only: bool = False,
        stockout_within_days: int | None = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "priority",
        sort_desc: bool = False,
        stockout_since: datetime | None = None,
    ) -> tuple[list[tuple], int]:
        """查询 SKU 列表 + 总数(返回 (rows, total))."""
        stat = MkSupplySkuDailyStat
        lps = MkListingProductSources

        base_filters = [
            stat.calc_run_id == calc_run_id,
            stat.tenant_id == tenant_id,
            stat.delivery_method == "FBA",  # Phase 1 仅 FBA
        ]

        if priorities:
            base_filters.append(stat.risk_level.in_(priorities))
        if mall_ids:
            base_filters.append(stat.mall_id.in_(mall_ids))
        if country_codes:
            base_filters.append(stat.country_code.in_(country_codes))
        if tags:
            tag_filters = []
            for tag in tags:
                clean_tag = (tag or "").strip()
                if not clean_tag:
                    continue
                tag_filters.append(
                    or_(
                        stat.label_ids == clean_tag,
                        stat.label_ids.ilike(f"{clean_tag},%"),
                        stat.label_ids.ilike(f"%,{clean_tag},%"),
                        stat.label_ids.ilike(f"%,{clean_tag}"),
                    )
                )
            if tag_filters:
                base_filters.append(or_(*tag_filters))
        if keyword:
            kw = f"%{keyword}%"
            base_filters.append(
                or_(stat.msku.ilike(kw), stat.sku.ilike(kw), stat.asin.ilike(kw),
                    stat.fnsku.ilike(kw), stat.product_name.ilike(kw))
            )
        if suggest_only:
            base_filters.append(stat.suggest_purchase == 1)
        if stockout_within_days is not None and stockout_since is not None:
            base_filters.append(
                select(MkStockoutEvent.event_id)
                .where(
                    MkStockoutEvent.tenant_id == stat.tenant_id,
                    MkStockoutEvent.mall_id == stat.mall_id,
                    MkStockoutEvent.msku == stat.msku,
                    MkStockoutEvent.start_at >= stockout_since,
                )
                .exists()
            )

        # 总数
        total_query = select(func.count(stat.id)).where(*base_filters)
        total = (await self._session.scalar(total_query)) or 0

        # 数据查询: join lps 拿 image / brand / category;join rl_mall 拿 store_name
        # 用 outerjoin 防止 lps 缺数据
        query = (
            select(stat, lps, RlMall.mall_name)
            .outerjoin(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
            .outerjoin(RlMall, RlMall.mall_id == stat.mall_id)
            .where(*base_filters)
        )

        # 排序
        sort_columns = self._sort_columns(sort_by, sort_desc)
        query = query.order_by(*sort_columns)

        # 分页
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(query)
        rows = result.all()
        return list(rows), int(total)

    async def stockout_recent_map(
        self,
        *,
        tenant_id: int,
        msku_mall_pairs: list[tuple[str | None, int | None]],
        since: datetime,
    ) -> dict[tuple[str | None, int | None], bool]:
        """近 7 天实际 FBA 断货事件映射.

        口径:只看事件开始时间是否落在近 7 天窗口内,排除更早已经断货的历史事件。
        """
        if not msku_mall_pairs:
            return {}
        event = MkStockoutEvent
        pair_filters = [
            (event.msku == msku) & (event.mall_id == mall_id)
            for msku, mall_id in msku_mall_pairs
        ]
        result = await self._session.execute(
            select(event.msku, event.mall_id)
            .where(
                event.tenant_id == tenant_id,
                event.start_at >= since,
                or_(*pair_filters),
            )
            .group_by(event.msku, event.mall_id)
        )
        return {(msku, mall_id): True for msku, mall_id in result.all()}

    def _sort_columns(self, sort_by: str, sort_desc: bool):
        stat = MkSupplySkuDailyStat
        # 风险等级排序: 用 CASE WHEN 把 p1/p2/p3/safe 映射成 0/1/2/3
        priority_order = case(
            {"p1": 0, "p2": 1, "p3": 2, "safe": 3},
            value=stat.risk_level,
            else_=99,
        )
        order_fn = desc if sort_desc else asc

        if sort_by == "priority":
            # 默认: priority asc, stockout_date asc, last_updated desc
            return [
                priority_order.asc(),
                stat.stockout_date.asc().nulls_last(),
                stat.updated_at.desc(),
            ]
        if sort_by == "stockout_date":
            return [order_fn(stat.stockout_date).nulls_last()]
        if sort_by == "fba_sellable_days":
            return [order_fn(stat.sellable_days).nulls_last()]
        if sort_by == "last_updated":
            return [order_fn(stat.updated_at)]
        return [priority_order.asc()]

    async def get_one(
        self,
        *,
        calc_run_id: str,
        tenant_id: int,
        listing_id: int,
    ) -> tuple[MkSupplySkuDailyStat, MkListingProductSources | None, str | None] | None:
        """按 listing_id 取详情主行."""
        stat = MkSupplySkuDailyStat
        lps = MkListingProductSources
        query = (
            select(stat, lps, RlMall.mall_name)
            .outerjoin(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
            .outerjoin(RlMall, RlMall.mall_id == stat.mall_id)
            .where(
                stat.calc_run_id == calc_run_id,
                stat.tenant_id == tenant_id,
                stat.listing_id == listing_id,
            )
        )
        result = await self._session.execute(query)
        row = result.first()
        if row is None:
            return None
        return tuple(row)  # type: ignore[return-value]

    async def last_purchase_dates_map(
        self, *, tenant_id: int, msku_mall_pairs: list[tuple[str, int | None]]
    ) -> dict[tuple[str, int | None], tuple[datetime | None, datetime | None]]:
        """批量拿每个 (msku, mall_id) 最近采购时间 + 最近发货时间.

        - last_purchase_date: max(mk_purchase_draft.created_at) - 任意状态(含 draft)
        - last_shipment_date: max(rl_fba_shipment_item.created_time) - 真实 FBA 发货记录
        """
        if not msku_mall_pairs:
            return {}
        mskus = {m for m, _ in msku_mall_pairs}
        out: dict[tuple[str, int | None], tuple[datetime | None, datetime | None]] = {}

        # 最近采购 — 草稿创建时间
        purchase_rows = (await self._session.execute(
            select(
                MkPurchaseDraft.msku,
                MkPurchaseDraft.mall_id,
                func.max(MkPurchaseDraft.created_at),
            )
            .where(
                MkPurchaseDraft.tenant_id == tenant_id,
                MkPurchaseDraft.msku.in_(mskus),
            )
            .group_by(MkPurchaseDraft.msku, MkPurchaseDraft.mall_id)
        )).all()
        for msku, mall_id, max_t in purchase_rows:
            k = (msku, mall_id)
            out[k] = (max_t, out.get(k, (None, None))[1])

        # 最近发货 — rl_fba_shipment_item 真实数据
        shipment_rows = (await self._session.execute(
            select(
                RlFbaShipmentItem.msku,
                RlFbaShipmentItem.mall_id,
                func.max(RlFbaShipmentItem.created_time),
            )
            .where(
                RlFbaShipmentItem.tenant_id == tenant_id,
                RlFbaShipmentItem.msku.in_(mskus),
                RlFbaShipmentItem.del_flag == 0,
            )
            .group_by(RlFbaShipmentItem.msku, RlFbaShipmentItem.mall_id)
        )).all()
        for msku, mall_id, max_t in shipment_rows:
            k = (msku, mall_id)
            out[k] = (out.get(k, (None, None))[0], max_t)
        return out

    async def earliest_arrival_map(
        self, *, tenant_id: int, msku_mall_pairs: list[tuple[str, int | None]]
    ) -> dict[tuple[str, int | None], "date | None"]:
        """批量拿每个 (msku, mall_id) 最早一笔在途的预计到货日期.

        基于 mk_sku_inbound_detail.expected_arrival_date 的最小值。供列表页"预计到货"列使用,
        避免每行都 round-trip 调 skus/detail。
        """
        if not msku_mall_pairs:
            return {}
        mskus = {m for m, _ in msku_mall_pairs}
        rows = (await self._session.execute(
            select(
                MkSkuInboundDetail.msku,
                MkSkuInboundDetail.mall_id,
                func.min(MkSkuInboundDetail.expected_arrival_date),
            )
            .where(
                MkSkuInboundDetail.tenant_id == tenant_id,
                MkSkuInboundDetail.msku.in_(mskus),
                MkSkuInboundDetail.inbound_status.in_(("in_transit", "receiving", "pending")),
                MkSkuInboundDetail.expected_arrival_date.is_not(None),
            )
            .group_by(MkSkuInboundDetail.msku, MkSkuInboundDetail.mall_id)
        )).all()
        return {(msku, mall_id): dt for msku, mall_id, dt in rows}

    async def get_listing_only(
        self, *, tenant_id: int, listing_id: int
    ) -> MkListingProductSources | None:
        """跳过 stat,直接查 listing 主表 — 用于 FBM 兜底判断."""
        return await self._session.scalar(
            select(MkListingProductSources).where(
                MkListingProductSources.tenant_id == tenant_id,
                MkListingProductSources.listing_id == listing_id,
            )
        )

    async def forecast_trend(
        self,
        *,
        calc_run_id: str,
        tenant_id: int,
        mall_id: int | None,
        msku: str,
    ) -> list[MkSkuForecastDaily]:
        fc = MkSkuForecastDaily
        filters = [
            fc.calc_run_id == calc_run_id,
            fc.tenant_id == tenant_id,
            fc.msku == msku,
        ]
        if mall_id is not None:
            filters.append(fc.mall_id == mall_id)
        result = await self._session.execute(
            select(fc).where(*filters).order_by(fc.day_offset.asc())
        )
        return list(result.scalars().all())

    async def forecast_by_offset(
        self,
        *,
        calc_run_id: str,
        tenant_id: int,
        mall_id: int | None,
        msku: str,
        day_offset: int,
    ) -> MkSkuForecastDaily | None:
        """按 day_offset 查预测点,用于库存 override 对齐 forecast_date."""
        fc = MkSkuForecastDaily
        filters = [
            fc.calc_run_id == calc_run_id,
            fc.tenant_id == tenant_id,
            fc.msku == msku,
            fc.day_offset == day_offset,
        ]
        if mall_id is not None:
            filters.append(fc.mall_id == mall_id)
        return await self._session.scalar(select(fc).where(*filters))

    async def list_inventory_overrides(
        self,
        *,
        tenant_id: int,
        listing_id: int,
    ) -> list[MkSkuInventoryOverride]:
        """读取 SKU 已保存的库存点位覆盖."""
        ovr = MkSkuInventoryOverride
        result = await self._session.execute(
            select(ovr)
            .where(ovr.tenant_id == tenant_id, ovr.listing_id == listing_id)
            .order_by(ovr.day_offset.asc())
        )
        return list(result.scalars().all())

    async def upsert_inventory_override(
        self,
        row: MkSkuInventoryOverride,
    ) -> MkSkuInventoryOverride:
        """按 tenant + listing + forecast_date 幂等保存库存覆盖点."""
        existing = await self._session.scalar(
            select(MkSkuInventoryOverride).where(
                MkSkuInventoryOverride.tenant_id == row.tenant_id,
                MkSkuInventoryOverride.listing_id == row.listing_id,
                MkSkuInventoryOverride.forecast_date == row.forecast_date,
            )
        )
        if existing is None:
            self._session.add(row)
            await self._session.commit()
            await self._session.refresh(row)
            return row

        existing.calc_run_id = row.calc_run_id
        existing.mall_id = row.mall_id
        existing.msku = row.msku
        existing.day_offset = row.day_offset
        existing.stock_qty = row.stock_qty
        existing.updated_by = row.updated_by
        existing.source_type = row.source_type
        await self._session.commit()
        await self._session.refresh(existing)
        return existing

    async def inbound_list(
        self,
        *,
        tenant_id: int,
        mall_id: int | None,
        msku: str,
    ) -> list[MkSkuInboundDetail]:
        inb = MkSkuInboundDetail
        filters = [inb.tenant_id == tenant_id, inb.msku == msku]
        if mall_id is not None:
            filters.append(inb.mall_id == mall_id)

        bind = self._session.get_bind()
        has_logistics_type = True
        if bind.dialect.name == "sqlite":
            columns = await self._session.execute(
                text("PRAGMA table_info(mk_sku_inbound_detail)")
            )
            has_logistics_type = any(row[1] == "logistics_type" for row in columns.fetchall())
        if not has_logistics_type:
            # 兼容已存在的本地演示库:旧表没有 logistics_type 列。
            result = await self._session.execute(
                select(
                    inb.inbound_id,
                    inb.tenant_id,
                    inb.mall_id,
                    inb.msku,
                    inb.sku,
                    inb.inbound_type,
                    inb.inbound_status,
                    inb.qty,
                    inb.expected_arrival_date,
                    inb.source_order_no,
                    inb.source_type,
                )
                .where(*filters)
                .order_by(inb.expected_arrival_date.asc().nulls_last())
            )
            return [
                MkSkuInboundDetail(
                    inbound_id=row.inbound_id,
                    tenant_id=row.tenant_id,
                    mall_id=row.mall_id,
                    msku=row.msku,
                    sku=row.sku,
                    inbound_type=row.inbound_type,
                    inbound_status=row.inbound_status,
                    logistics_type=None,
                    qty=row.qty,
                    expected_arrival_date=row.expected_arrival_date,
                    source_order_no=row.source_order_no,
                    source_type=row.source_type,
                )
                for row in result.all()
            ]

        result = await self._session.execute(
            select(inb).where(*filters).order_by(inb.expected_arrival_date.asc().nulls_last())
        )
        return list(result.scalars().all())

    async def recent_7d_sales_map(
        self, *, tenant_id: int, msku_mall_pairs: list[tuple[str, int | None]]
    ) -> dict[tuple[str, int | None], list[int]]:
        """批量拿每个 (msku, mall_id) 过去 7 天每天销量,返回长度 7 数组 [D-6..D-0]."""
        from datetime import timedelta

        if not msku_mall_pairs:
            return {}
        d0_str = await self._session.scalar(
            select(func.max(RlAmzSalesDailyReport.year_month_day)).where(
                RlAmzSalesDailyReport.tenant_id == tenant_id
            )
        )
        if not d0_str:
            return {}
        d0 = datetime.strptime(d0_str, "%Y-%m-%d").date()
        days = [(d0 - timedelta(days=6 - i)).isoformat() for i in range(7)]
        mskus = {m for m, _ in msku_mall_pairs}

        rows = (await self._session.execute(
            select(
                RlAmzSalesDailyReport.msku,
                RlAmzSalesDailyReport.mall_id,
                RlAmzSalesDailyReport.year_month_day,
                func.coalesce(func.sum(RlAmzSalesDailyReport.sales_volume), 0),
            )
            .where(
                RlAmzSalesDailyReport.tenant_id == tenant_id,
                RlAmzSalesDailyReport.msku.in_(mskus),
                RlAmzSalesDailyReport.year_month_day.in_(days),
            )
            .group_by(
                RlAmzSalesDailyReport.msku,
                RlAmzSalesDailyReport.mall_id,
                RlAmzSalesDailyReport.year_month_day,
            )
        )).all()

        day_index = {d: i for i, d in enumerate(days)}
        out: dict[tuple[str, int | None], list[int]] = {}
        for msku, mall_id, ymd, qty in rows:
            key = (msku, mall_id)
            if key not in out:
                out[key] = [0] * 7
            idx = day_index.get(ymd)
            if idx is not None:
                out[key][idx] = int(qty or 0)
        return out

    async def history_sales(
        self,
        *,
        tenant_id: int,
        mall_id: int | None,
        msku: str,
        days: int,
    ) -> list[RlAmzSalesDailyReport]:
        """从 rl_amz_sales_daily_report 取最近 N 天销量记录."""
        sales = RlAmzSalesDailyReport
        filters = [sales.tenant_id == tenant_id, sales.msku == msku]
        if mall_id is not None:
            filters.append(sales.mall_id == mall_id)
        result = await self._session.execute(
            select(sales)
            .where(*filters)
            .order_by(desc(sales.year_month_day))
            .limit(days)
        )
        rows = list(result.scalars().all())
        rows.sort(key=lambda r: r.year_month_day or "")  # 升序回归
        return rows
