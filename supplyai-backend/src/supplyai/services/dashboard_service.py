"""Dashboard 应用服务."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from supplyai.models.mk import MkSupplySkuDailyStat
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.schemas.common import CurrencyAmount, SuggestTotalAmount
from supplyai.schemas.dashboard import (
    ActionHint,
    AlertsDTO,
    AlertsRequest,
    HolidayItem,
    HolidayUpsertRequest,
    HolidaysDTO,
    HolidaysRequest,
    DashboardSnapshotDTO,
    DashboardSnapshotRequest,
    DataQualityAlert,
    FilterOption,
    FiltersDTO,
    FiltersRequest,
    FinanceDTO,
    FinanceMetric,
    FinanceRequest,
    RiskCounts,
    RiskQueueDTO,
    RiskQueueRequest,
    RiskQueueRow,
    StoreSummaryRow,
    StoresDTO,
    StoresRequest,
)

EXPENSE_RATE = 0.51  # 平台费 + 广告 + 物流(启发式;Phase 2 改读 mk_finance_daily_stat)
from supplyai.utils.exceptions import CalcRunNotFoundException


class DashboardService:
    """Dashboard 业务编排."""

    def __init__(self, repo: DashboardRepository) -> None:
        self._repo = repo

    async def snapshot(self, req: DashboardSnapshotRequest) -> DashboardSnapshotDTO:
        # 1. 解析 calc_run_id(不传则取最新)
        calc_run_id = req.calc_run_id or await self._repo.latest_calc_run_id(req.tenant_id)
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)

        calc_run = await self._repo.get_calc_run(calc_run_id)
        as_of = calc_run.run_at if calc_run else datetime.utcnow()

        # 2. 风险分布 + 断货数 + 7d/库存聚合(全部带 mall/country/owner 过滤)
        f = dict(
            mall_ids=req.mall_ids,
            country_codes=req.country_codes,
            owners=req.owners,
        )
        risk_counts = await self._repo.risk_counts(calc_run_id, req.tenant_id, **f)
        stockout_7 = await self._repo.stockout_7_count(calc_run_id, req.tenant_id, **f)
        total_sales_7d, total_stock = await self._repo.snapshot_aggregates(
            calc_run_id, req.tenant_id, **f
        )

        # 3. 建议采购合计 + 多币种(同样过滤)
        sku_count, total_qty, total_amount_base, by_currency_dict = (
            await self._repo.suggest_summary(calc_run_id, req.tenant_id, **f)
        )

        suggest_total_amount = SuggestTotalAmount(
            base=CurrencyAmount(currency="USD", amount=float(total_amount_base)),
            by_currency=[
                CurrencyAmount(currency=cur, amount=float(amt))
                for cur, amt in sorted(by_currency_dict.items())
            ],
            fx_rate_as_of=as_of,
        )

        return DashboardSnapshotDTO(
            calc_run_id=calc_run_id,
            as_of=as_of,
            risk_counts=RiskCounts(**risk_counts),
            stockout_7_count=stockout_7,
            total_sales_7d=total_sales_7d,
            total_stock=total_stock,
            suggest_sku_count=sku_count,
            suggest_total_qty=total_qty,
            suggest_total_amount=suggest_total_amount,
            stockout_trend=[],  # Phase 3.5 接入
        )

    async def finance(self, req: FinanceRequest) -> FinanceDTO:
        """昨日财务摘要 + 同比.

        D-1 = req.as_of_date 或 rl_amz_sales_daily_report 最大日期.
        D-2 = D-1 上一天,用于算 pct_change.
        """
        if req.as_of_date:
            d1 = req.as_of_date.isoformat()
        else:
            d1 = await self._repo.latest_sales_date(req.tenant_id)
            if not d1:
                # 无销售数据,返 0 + None
                return FinanceDTO(
                    as_of_date=datetime.utcnow().date().isoformat(),
                    sales=FinanceMetric(value=0),
                    gmv=FinanceMetric(value=0),
                    cost=FinanceMetric(value=0),
                    expense=FinanceMetric(value=0),
                    profit=FinanceMetric(value=0),
                )
        d2 = (
            datetime.strptime(d1, "%Y-%m-%d") - timedelta(days=1)
        ).date().isoformat()

        sv1, gmv1, cost1 = await self._repo.daily_sales_aggregate(
            tenant_id=req.tenant_id, ymd=d1,
            mall_ids=req.mall_ids, country_codes=req.country_codes,
        )
        sv2, gmv2, cost2 = await self._repo.daily_sales_aggregate(
            tenant_id=req.tenant_id, ymd=d2,
            mall_ids=req.mall_ids, country_codes=req.country_codes,
        )

        expense1 = float(gmv1) * EXPENSE_RATE
        expense2 = float(gmv2) * EXPENSE_RATE
        profit1 = float(gmv1) - float(cost1) - expense1
        profit2 = float(gmv2) - float(cost2) - expense2

        def _pct(cur: float, prev: float) -> float | None:
            if prev <= 0:
                return None
            return round((cur - prev) / prev * 100, 2)

        return FinanceDTO(
            as_of_date=d1,
            sales=FinanceMetric(value=float(sv1), pct_change=_pct(sv1, sv2)),
            gmv=FinanceMetric(value=round(float(gmv1), 2), pct_change=_pct(float(gmv1), float(gmv2))),
            cost=FinanceMetric(value=round(float(cost1), 2), pct_change=_pct(float(cost1), float(cost2))),
            expense=FinanceMetric(value=round(expense1, 2), pct_change=_pct(expense1, expense2)),
            profit=FinanceMetric(value=round(profit1, 2), pct_change=_pct(profit1, profit2)),
        )

    async def upsert_holiday(self, req: HolidayUpsertRequest) -> HolidayItem:
        row = await self._repo.upsert_holiday(req.model_dump())
        return HolidayItem(
            id=row.holiday_id,
            name=row.name,
            peak_date=row.peak_date.isoformat(),
            days_before=row.days_before,
            days_after=row.days_after,
            sales_multiplier=float(row.sales_multiplier),
            color=row.color,
            flag=row.flag,
            country_code=row.country_code,
        )

    async def holidays(self, req: HolidaysRequest) -> HolidaysDTO:
        rows = await self._repo.list_holidays(
            tenant_id=req.tenant_id, country_code=req.country_code
        )
        return HolidaysDTO(
            holidays=[
                HolidayItem(
                    id=h.holiday_id,
                    name=h.name,
                    peak_date=h.peak_date.isoformat(),
                    days_before=h.days_before,
                    days_after=h.days_after,
                    sales_multiplier=float(h.sales_multiplier),
                    color=h.color,
                    flag=h.flag,
                    country_code=h.country_code,
                )
                for h in rows
            ]
        )

    async def alerts(self, req: AlertsRequest) -> AlertsDTO:
        """数据质量告警 — "需关注"面板派生."""
        calc_run_id = req.calc_run_id or await self._repo.latest_calc_run_id(
            req.tenant_id
        )
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)
        c = await self._repo.alert_counts(
            calc_run_id=calc_run_id, tenant_id=req.tenant_id
        )
        out: list[DataQualityAlert] = []
        if c["forecast_default"] > 0:
            out.append(DataQualityAlert(
                id="forecast-default",
                kind="forecast",
                title=f"{c['forecast_default']} 个 SKU 销量预测样本不足(用默认值)",
                count=c["forecast_default"],
                action="检查预测",
            ))
        if c["cost_missing"] > 0:
            out.append(DataQualityAlert(
                id="cost-missing",
                kind="data_quality",
                title=f"{c['cost_missing']} 个 SKU 成本缺失,采购金额不准",
                count=c["cost_missing"],
                action="补成本",
            ))
        if c["review_p1_no_suggest"] > 0:
            out.append(DataQualityAlert(
                id="review-p1-no-suggest",
                kind="review",
                title=f"{c['review_p1_no_suggest']} 个 P1 风险但建议采购为 0,需复核",
                count=c["review_p1_no_suggest"],
                action="查看",
            ))
        return AlertsDTO(alerts=out)

    async def stores(self, req: StoresRequest) -> StoresDTO:
        """每个店铺 SKU 数 + 风险分布 — 侧栏"店铺空间"渲染."""
        calc_run_id = req.calc_run_id or await self._repo.latest_calc_run_id(
            req.tenant_id
        )
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)

        raw = await self._repo.store_risk_summary(
            calc_run_id=calc_run_id, tenant_id=req.tenant_id
        )
        rows = [
            StoreSummaryRow(
                mall_id=mid,
                mall_name=name,
                country_code=cc,
                sku_count=sum(counts.values()),
                p1_count=counts["p1"],
                p2_count=counts["p2"],
                p3_count=counts["p3"],
                safe_count=counts["safe"],
            )
            for mid, name, cc, counts in raw
        ]
        rows.sort(key=lambda r: (-r.p1_count, -r.sku_count))
        return StoresDTO(rows=rows)

    async def filters(self, req: FiltersRequest) -> FiltersDTO:
        """顶部过滤器选项 — store / country / owner 三组."""
        calc_run_id = req.calc_run_id or await self._repo.latest_calc_run_id(
            req.tenant_id
        )
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)

        stores_raw, countries_raw, owners_raw, brands_raw, cats_raw = await self._repo.filter_options(
            calc_run_id=calc_run_id, tenant_id=req.tenant_id
        )
        stores = [
            FilterOption(
                value=str(mall_id) if mall_id is not None else "",
                label=mall_name or f"mall {mall_id}",
                count=cnt,
            )
            for mall_id, mall_name, cnt in stores_raw
            if mall_id is not None
        ]
        stores.sort(key=lambda o: -o.count)

        countries = [
            FilterOption(value=c or "", label=c or "未知", count=cnt)
            for c, cnt in countries_raw
            if c
        ]
        countries.sort(key=lambda o: -o.count)

        owners = [
            FilterOption(value=o or "", label=o or "未分配", count=cnt)
            for o, cnt in owners_raw
            if o
        ]
        owners.sort(key=lambda o: -o.count)

        brands = [
            FilterOption(value=b, label=b, count=cnt)
            for b, cnt in brands_raw if b
        ]
        brands.sort(key=lambda o: -o.count)
        categories = [
            FilterOption(value=c, label=c, count=cnt)
            for c, cnt in cats_raw if c
        ]
        categories.sort(key=lambda o: -o.count)

        return FiltersDTO(
            stores=stores, countries=countries, owners=owners,
            brands=brands, categories=categories,
        )

    async def risk_queue(self, req: RiskQueueRequest) -> RiskQueueDTO:
        """风险队列(工作台右侧"今日动作"面板数据)."""
        calc_run_id = req.calc_run_id or await self._repo.latest_calc_run_id(
            req.tenant_id
        )
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)

        calc_run = await self._repo.get_calc_run(calc_run_id)
        as_of = calc_run.run_at if calc_run else datetime.utcnow()

        rows, total = await self._repo.risk_queue(
            calc_run_id=calc_run_id,
            tenant_id=req.tenant_id,
            priorities=req.priorities,
            mall_ids=req.mall_ids,
            country_codes=req.country_codes,
            limit=req.limit,
        )

        queue_rows = [_build_queue_row(stat, mall_name) for stat, mall_name in rows]
        return RiskQueueDTO(
            calc_run_id=calc_run_id,
            as_of=as_of,
            total=total,
            rows=queue_rows,
        )


def _to_float(v: Decimal | None) -> float | None:
    return float(v) if v is not None else None


def _action_hint(stat: MkSupplySkuDailyStat) -> ActionHint:
    """从风险等级 + 建议采购派生 action_hint."""
    if stat.risk_level == "p1":
        return "urgent_purchase"
    if stat.risk_level == "p2":
        return "follow_up"
    if stat.risk_level == "p3":
        return "review"
    return "ok"


def _build_queue_row(
    stat: MkSupplySkuDailyStat, store_name: str | None
) -> RiskQueueRow:
    return RiskQueueRow(
        listing_id=stat.listing_id,
        mall_id=stat.mall_id,
        msku=stat.msku,
        sku=stat.sku,
        asin=stat.asin,
        product_name=stat.product_name,
        store_name=store_name,
        country_code=stat.country_code,
        priority=stat.risk_level,  # type: ignore[arg-type]
        fba_sellable_days=_to_float(stat.fba_sellable_days),
        stockout_date=stat.stockout_date,
        suggest_qty=stat.suggest_qty,
        suggest_amount_base=_to_float(stat.suggest_amount_base),
        base_currency=stat.base_currency,
        action_hint=_action_hint(stat),
        calc_run_id=stat.calc_run_id,
    )
