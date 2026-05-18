"""SKU 应用服务."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from decimal import Decimal

from supplyai.models.mk import (
    MkListingProductSources,
    MkSkuForecastDaily,
    MkSkuInboundDetail,
    MkSkuInventoryOverride,
    MkSupplySkuDailyStat,
)
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.repositories.sku_repo import SkuRepository
from supplyai.schemas.common import DataQuality, DataQualityWarning, PageResult
from supplyai.schemas.sku import (
    ForecastTrendPoint,
    InventoryOverrideDTO,
    InventoryOverrideUpsertRequest,
    InboundDetailDTO,
    SkuDetailDTO,
    SkuDetailRequest,
    SkuListRequest,
    SkuSummaryDTO,
    SkuTrendsDTO,
    SkuTrendsRequest,
    TrendPoint,
)
from supplyai.utils.exceptions import (
    CalcRunNotFoundException,
    FbmNotSupportedException,
    SkuNotFoundException,
)


def _to_float(v: Decimal | None) -> float | None:
    return float(v) if v is not None else None


_GROSS_MARGIN_HEURISTIC = 0.30  # Phase 2 改读 mk_finance_daily_stat 真实毛利率


def _compute_loss_revenue_7d(
    fba_sellable_days: Decimal | None,
    future_daily: Decimal | None,
    unit_cost: Decimal | None,
) -> float:
    """未来 7 天因 FBA 断货预期销售损失(成本币种)."""
    if future_daily is None or unit_cost is None or fba_sellable_days is None:
        return 0.0
    days_short = max(0.0, 7.0 - float(fba_sellable_days))
    if days_short <= 0:
        return 0.0
    return round(days_short * float(future_daily) * float(unit_cost), 2)


def _compute_future_30d_profit(
    future_daily: Decimal | None,
    unit_cost: Decimal | None,
) -> float:
    """未来 30 天预期毛利估算(启发式毛利率 30%)."""
    if future_daily is None or unit_cost is None:
        return 0.0
    return round(
        float(future_daily) * 30 * float(unit_cost) * _GROSS_MARGIN_HEURISTIC, 2
    )


def _parse_label_ids(value: str | None) -> list[str]:
    """把 ERP/物化表里的标签串拆成前端可展示的标签列表."""
    if not value:
        return []
    tags: list[str] = []
    seen: set[str] = set()
    for part in re.split(r"[,，;；|/]+", value):
        tag = part.strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)
    return tags


def _inventory_override_id(
    *, tenant_id: int, listing_id: int, forecast_date: date
) -> str:
    return f"INVOVR-{tenant_id}-{listing_id}-{forecast_date.isoformat()}"


def _row_to_dto(
    stat: MkSupplySkuDailyStat,
    lps: MkListingProductSources | None,
    store_name: str | None,
    last_purchase_date: "datetime | None" = None,
    last_shipment_date: "datetime | None" = None,
    estimated_arrival_date: "date | None" = None,
    recent_7d: list[int] | None = None,
    stockout_recent_7: bool = False,
) -> SkuSummaryDTO:
    """ORM row tuple → SkuSummaryDTO."""
    fba_inbound = (
        (stat.fba_inbound_working or 0)
        + (stat.fba_inbound_shipped or 0)
        + (stat.fba_inbound_receiving or 0)
    )
    label_ids = stat.label_ids or (lps.label_ids if lps else None)
    return SkuSummaryDTO(
        id=stat.listing_id or stat.id,
        calc_run_id=stat.calc_run_id,
        tenant_id=stat.tenant_id,
        listing_id=stat.listing_id or 0,
        mall_id=stat.mall_id,
        msku=stat.msku,
        sku=stat.sku,
        asin=stat.asin,
        fnsku=stat.fnsku,
        product_name=stat.product_name or (lps.product_name if lps else None),
        image_url=lps.image_url if lps else None,
        brand=lps.brand if lps else None,
        category=lps.category if lps else None,
        label_ids=label_ids,
        tags=_parse_label_ids(label_ids),
        owner=lps.owner if lps else None,
        store_name=store_name,
        country_code=stat.country_code,
        delivery_method=stat.delivery_method,  # type: ignore[arg-type]
        listing_status=stat.listing_status,
        priority=stat.risk_level,  # type: ignore[arg-type]
        yesterday_sales=stat.yesterday_sales,
        sales_7d=stat.sales_7d,
        recent_7d=recent_7d or [],
        future_daily=_to_float(stat.forecast_daily),
        forecast_source=stat.forecast_source,
        coverage_demand=_to_float(stat.coverage_demand),
        total_stock=stat.total_stock,
        planning_stock=stat.planning_stock if stat.planning_stock is not None else stat.fba_available,
        stock_scope=stat.stock_scope_json or ["fba_available"],
        fba_available=stat.fba_available,
        fba_inbound=fba_inbound,
        local_actual=stat.local_actual,
        local_plan=stat.local_plan,
        sellable_days=_to_float(stat.sellable_days),
        fba_sellable_days=_to_float(stat.fba_sellable_days),
        local_sellable_days=_to_float(stat.local_sellable_days),
        safety_days=stat.safety_days,
        lead_time_days=stat.lead_time_days,
        stockout_date=stat.stockout_date,
        purchase_date=stat.suggest_purchase_date,
        stockout_recent_7=stockout_recent_7,
        suggest=bool(stat.suggest_purchase),
        suggest_qty=stat.suggest_qty,
        suggest_amount=_to_float(stat.suggest_amount),
        suggest_amount_base=_to_float(stat.suggest_amount_base),
        base_currency=stat.base_currency,
        revenue_7d=_to_float(stat.revenue_7d),
        expense_7d=_to_float(stat.expense_7d),
        cost_7d=_to_float(stat.cost_7d),
        gross_profit_7d=_to_float(stat.gross_profit_7d),
        gross_margin=_to_float(stat.gross_margin),
        financial_estimate_type=stat.financial_estimate_type,  # type: ignore[arg-type]
        expected_loss_revenue_7d=_compute_loss_revenue_7d(
            stat.fba_sellable_days, stat.forecast_daily, stat.unit_cost
        ),
        future_30d_profit=_compute_future_30d_profit(
            stat.forecast_daily, stat.unit_cost
        ),
        last_purchase_date=last_purchase_date,
        last_shipment_date=last_shipment_date,
        estimated_arrival_date=estimated_arrival_date,
        last_updated=stat.updated_at,
    )


class SkuService:
    """SKU 列表 / 详情业务编排."""

    def __init__(
        self,
        sku_repo: SkuRepository,
        dashboard_repo: DashboardRepository,
    ) -> None:
        self._sku_repo = sku_repo
        self._dashboard_repo = dashboard_repo

    async def list_skus(self, req: SkuListRequest) -> PageResult[SkuSummaryDTO]:
        """备货列表查询."""
        calc_run_id = req.calc_run_id or await self._dashboard_repo.latest_calc_run_id(
            req.tenant_id
        )
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)
        calc_run = await self._dashboard_repo.get_calc_run(calc_run_id)
        as_of = calc_run.run_at if calc_run else datetime.utcnow()
        stockout_since = datetime.combine(
            as_of.date() - timedelta(days=6),
            datetime.min.time(),
        )

        rows, total = await self._sku_repo.list_skus(
            calc_run_id=calc_run_id,
            tenant_id=req.tenant_id,
            priorities=req.priorities,
            mall_ids=req.mall_ids,
            country_codes=req.country_codes,
            keyword=req.keyword,
            suggest_only=req.suggest_only,
            stockout_within_days=req.stockout_within_days,
            page=req.page,
            page_size=req.page_size,
            sort_by=req.sort_by,
            sort_desc=req.sort_desc,
            stockout_since=stockout_since,
        )

        # 批量查最近采购/发货时间 + 最早在途到货 + 过去 7 天每日销量(避免 N+1)
        pairs = [(stat.msku, stat.mall_id) for stat, _, _ in rows]
        date_map = await self._sku_repo.last_purchase_dates_map(
            tenant_id=req.tenant_id, msku_mall_pairs=pairs
        )
        arrival_map = await self._sku_repo.earliest_arrival_map(
            tenant_id=req.tenant_id, msku_mall_pairs=pairs
        )
        recent7_map = await self._sku_repo.recent_7d_sales_map(
            tenant_id=req.tenant_id, msku_mall_pairs=pairs
        )
        stockout_recent_map = await self._sku_repo.stockout_recent_map(
            tenant_id=req.tenant_id,
            msku_mall_pairs=pairs,
            since=stockout_since,
        )

        items = []
        for stat, lps, mall_name in rows:
            key = (stat.msku, stat.mall_id)
            lp, ls = date_map.get(key, (None, None))
            ea = arrival_map.get(key)
            r7 = recent7_map.get(key, [])
            items.append(
                _row_to_dto(
                    stat,
                    lps,
                    mall_name,
                    lp,
                    ls,
                    ea,
                    r7,
                    stockout_recent_map.get(key, False),
                )
            )
        return PageResult[SkuSummaryDTO](
            rows=items,
            total=total,
            page=req.page,
            page_size=req.page_size,
        )

    async def detail(self, req: SkuDetailRequest) -> SkuDetailDTO:
        """SKU 详情."""
        calc_run_id = req.calc_run_id or await self._dashboard_repo.latest_calc_run_id(
            req.tenant_id
        )
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)

        row = await self._sku_repo.get_one(
            calc_run_id=calc_run_id,
            tenant_id=req.tenant_id,
            listing_id=req.listing_id,
        )
        if row is None:
            # 没快照行 — 区分 FBM(产品需求:有兜底)与"真不存在"
            listing = await self._sku_repo.get_listing_only(
                tenant_id=req.tenant_id, listing_id=req.listing_id
            )
            if listing is not None and listing.delivery_method == "FBM":
                raise FbmNotSupportedException(req.listing_id)
            raise SkuNotFoundException(req.listing_id)

        stat, lps, mall_name = row
        date_map = await self._sku_repo.last_purchase_dates_map(
            tenant_id=req.tenant_id, msku_mall_pairs=[(stat.msku, stat.mall_id)]
        )
        arrival_map = await self._sku_repo.earliest_arrival_map(
            tenant_id=req.tenant_id, msku_mall_pairs=[(stat.msku, stat.mall_id)]
        )
        recent7_map = await self._sku_repo.recent_7d_sales_map(
            tenant_id=req.tenant_id, msku_mall_pairs=[(stat.msku, stat.mall_id)]
        )
        key = (stat.msku, stat.mall_id)
        lp, ls = date_map.get(key, (None, None))
        ea = arrival_map.get(key)
        r7 = recent7_map.get(key, [])
        summary = _row_to_dto(stat, lps, mall_name, lp, ls, ea, r7)

        forecast_rows = await self._sku_repo.forecast_trend(
            calc_run_id=calc_run_id,
            tenant_id=req.tenant_id,
            mall_id=stat.mall_id,
            msku=stat.msku,
        )
        forecast_trend = [
            ForecastTrendPoint(
                date=fc.forecast_date,
                qty=float(fc.forecast_qty),
                source=fc.forecast_source,
                is_adjusted=bool(fc.is_adjusted),
            )
            for fc in forecast_rows
        ]

        inbound_rows = await self._sku_repo.inbound_list(
            tenant_id=req.tenant_id,
            mall_id=stat.mall_id,
            msku=stat.msku,
        )
        inbound_list = _fba_inbound_breakdown(stat) + [
            InboundDetailDTO.model_validate(inb) for inb in inbound_rows
        ]

        data_quality = _build_data_quality(stat, lps, forecast_rows)

        return SkuDetailDTO(
            calc_run_id=calc_run_id,
            summary=summary,
            forecast_trend=forecast_trend,
            inbound_list=inbound_list,
            data_quality=data_quality,
        )


    async def trends(self, req: SkuTrendsRequest) -> SkuTrendsDTO:
        """详情页趋势曲线: 历史销量 + 未来预测."""
        calc_run_id = req.calc_run_id or await self._dashboard_repo.latest_calc_run_id(
            req.tenant_id
        )
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)

        row = await self._sku_repo.get_one(
            calc_run_id=calc_run_id,
            tenant_id=req.tenant_id,
            listing_id=req.listing_id,
        )
        if row is None:
            raise SkuNotFoundException(req.listing_id)
        stat, _lps, _mall_name = row

        history_rows = await self._sku_repo.history_sales(
            tenant_id=req.tenant_id,
            mall_id=stat.mall_id,
            msku=stat.msku,
            days=req.history_days,
        )
        history = [
            TrendPoint(
                date=_parse_iso_date(s.year_month_day),
                qty=float(s.sales_volume or 0),
            )
            for s in history_rows
            if s.year_month_day
        ]

        forecast_rows = await self._sku_repo.forecast_trend(
            calc_run_id=calc_run_id,
            tenant_id=req.tenant_id,
            mall_id=stat.mall_id,
            msku=stat.msku,
        )
        forecast = [
            TrendPoint(date=fc.forecast_date, qty=float(fc.forecast_qty))
            for fc in forecast_rows
        ]
        overrides = await self._sku_repo.list_inventory_overrides(
            tenant_id=req.tenant_id,
            listing_id=req.listing_id,
        )

        return SkuTrendsDTO(
            calc_run_id=calc_run_id,
            msku=stat.msku,
            mall_id=stat.mall_id,
            history=history,
            forecast=forecast,
            inventory_overrides=[
                InventoryOverrideDTO.model_validate(row) for row in overrides
            ],
        )

    async def upsert_inventory_override(
        self,
        req: InventoryOverrideUpsertRequest,
    ) -> InventoryOverrideDTO:
        """保存 SKU 趋势图上的库存点位覆盖."""
        calc_run_id = req.calc_run_id or await self._dashboard_repo.latest_calc_run_id(
            req.tenant_id
        )
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)

        calc_run = await self._dashboard_repo.get_calc_run(calc_run_id)
        if not calc_run:
            raise CalcRunNotFoundException(req.tenant_id)

        row = await self._sku_repo.get_one(
            calc_run_id=calc_run_id,
            tenant_id=req.tenant_id,
            listing_id=req.listing_id,
        )
        if row is None:
            listing = await self._sku_repo.get_listing_only(
                tenant_id=req.tenant_id, listing_id=req.listing_id
            )
            if listing is not None and listing.delivery_method == "FBM":
                raise FbmNotSupportedException(req.listing_id)
            raise SkuNotFoundException(req.listing_id)
        stat, _lps, _mall_name = row

        forecast_row = await self._sku_repo.forecast_by_offset(
            calc_run_id=calc_run_id,
            tenant_id=req.tenant_id,
            mall_id=stat.mall_id,
            msku=stat.msku,
            day_offset=req.day_offset,
        )
        forecast_date = (
            (forecast_row.forecast_date if forecast_row else None)
            or req.forecast_date
            or (calc_run.stat_date + timedelta(days=req.day_offset))
        )

        saved = await self._sku_repo.upsert_inventory_override(
            MkSkuInventoryOverride(
                override_id=_inventory_override_id(
                    tenant_id=req.tenant_id,
                    listing_id=req.listing_id,
                    forecast_date=forecast_date,
                ),
                tenant_id=req.tenant_id,
                listing_id=req.listing_id,
                calc_run_id=calc_run_id,
                mall_id=stat.mall_id,
                msku=stat.msku,
                forecast_date=forecast_date,
                day_offset=req.day_offset,
                stock_qty=req.stock_qty,
                updated_by=req.updated_by,
                source_type="frontend",
            )
        )
        return InventoryOverrideDTO.model_validate(saved)


def _parse_iso_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _fba_inbound_breakdown(stat: MkSupplySkuDailyStat) -> list[InboundDetailDTO]:
    """把 FBA 平台侧在途数量拆成详情页可展开明细.

    mk_sku_inbound_detail 只保留本地侧采购/调拨在途；FBA working/shipped/receiving
    来自快照表和 rl_amz_manage_fba_inventory,否则前端只有"1 笔"入口但没有内容。
    """
    specs = [
        ("fba_working", "pending", stat.fba_inbound_working or 0, "FBA-WORKING"),
        ("fba_shipped", "in_transit", stat.fba_inbound_shipped or 0, "FBA-SHIPPED"),
        ("fba_receiving", "receiving", stat.fba_inbound_receiving or 0, "FBA-RECEIVING"),
    ]
    rows: list[InboundDetailDTO] = []
    for inbound_type, status, qty, order_no in specs:
        if qty <= 0:
            continue
        rows.append(
            InboundDetailDTO(
                inbound_id=f"{order_no}-{stat.listing_id or stat.id}",
                inbound_type=inbound_type,
                inbound_status=status,
                logistics_type=None,  # FBA 平台侧暂无独立物流方式字段
                qty=qty,
                expected_arrival_date=stat.stockout_date,
                source_order_no=order_no,
            )
        )
    return rows


def _build_data_quality(
    stat: MkSupplySkuDailyStat,
    lps: MkListingProductSources | None,
    forecast_rows: list[MkSkuForecastDaily],
) -> DataQuality:
    """简单数据质量检查 — Phase 1 仅标几个高频缺失项."""
    missing: list[str] = []
    warnings: list[DataQualityWarning] = []
    if lps is None:
        missing.append("listing_meta")
        warnings.append(
            DataQualityWarning(
                code="LISTING_META_MISSING",
                field="listing_id",
                message="商品主物化信息缺失,详情字段降级。",
                severity="warn",
            )
        )
    if stat.unit_cost is None:
        missing.append("unit_cost")
    if stat.forecast_daily is None:
        missing.append("forecast_daily")
    if not forecast_rows:
        warnings.append(
            DataQualityWarning(
                code="FORECAST_TREND_EMPTY",
                field="forecast_trend",
                message="该 SKU 暂无未来预测明细。",
                severity="info",
            )
        )
    return DataQuality(missing_fields=missing, warnings=warnings)
