"""Calc Engine 编排服务.

把 forecast / stock / risk / suggest / rules 五个纯模块串成端到端管线,
对一个租户的所有 FBA listing 跑一次,生成新的 calc_run + snapshot + forecast 序列。
"""
from __future__ import annotations

import logging
import re
import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Literal

from supplyai.domain.calc.forecast import ForecastInput, compute_forecast
from supplyai.domain.calc.risk import classify_risk, compute_stockout_date
from supplyai.domain.calc.rules import (
    DEFAULT_STOCK_SCOPE,
    ReplenishmentRule,
    normalize_stock_scope,
    resolve_rule,
)
from supplyai.domain.calc.stock import aggregate_stock, participating_stock, sellable_days
from supplyai.domain.calc.suggest import SuggestInput, compute_suggest
from supplyai.models.mk import (
    MkCalcRun,
    MkHoliday,
    MkListingProductSources,
    MkReplenishmentRule,
    MkSkuForecastDaily,
    MkSupplySkuDailyStat,
)
from supplyai.models.rl import RlAmzManageFbaInventory, RlAmzSalesDailyReport
from supplyai.repositories.calc_repo import CalcRepository
from supplyai.utils.exceptions import BusinessException

logger = logging.getLogger(__name__)

RunType = Literal["scheduled", "rule_changed", "manual"]
HISTORY_DAYS = 90
HORIZON_DAYS = 45
MIN_HOLIDAY_MULTIPLIER = 0.3
MAX_HOLIDAY_MULTIPLIER = 4.0


class NoListingsException(BusinessException):
    code = "NO_LISTINGS"

    def __init__(self, tenant_id: int) -> None:
        super().__init__(
            f"租户 {tenant_id} 暂无 FBA listing,无法触发计算。",
            status_code=400,
        )


class CalcService:
    """Calc 编排."""

    def __init__(self, repo: CalcRepository) -> None:
        self._repo = repo

    async def run(
        self,
        *,
        tenant_id: int,
        run_type: RunType = "manual",
        rule_version: str | None = None,
        today: date | None = None,
    ) -> MkCalcRun:
        """跑一次完整管线 — 写 mk_calc_run + 快照 + 逐日预测."""
        today = today or date.today()
        now = datetime.utcnow()

        # 0. 创建 running 记录
        suffix = secrets.token_hex(3)
        calc_run_id = f"RUN-{now.strftime('%Y%m%d%H%M%S')}-{tenant_id}-{suffix}"
        run = MkCalcRun(
            calc_run_id=calc_run_id,
            tenant_id=tenant_id,
            stat_date=today,
            run_type=run_type,
            run_at=now,
            rule_version=rule_version,
            status="running",
            source_type="derived",
        )
        await self._repo.insert_calc_run(run)

        try:
            await self._execute(run=run, today=today)
            await self._repo.update_run_status(calc_run_id, status="success")
            run.status = "success"
        except BusinessException:
            await self._repo.update_run_status(calc_run_id, status="failed")
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception("calc_run_failed", extra={"calc_run_id": calc_run_id})
            await self._repo.update_run_status(
                calc_run_id, status="failed", error_message=str(e)
            )
            run.status = "failed"
            raise

        return run

    async def _execute(self, *, run: MkCalcRun, today: date) -> None:
        tenant_id = run.tenant_id

        # 1. 加载 listing + 库存 + 销量 + 规则
        listings = await self._repo.list_fba_listings(tenant_id)
        if not listings:
            raise NoListingsException(tenant_id)

        fba_inv = await self._repo.fba_inventory_map(tenant_id)
        local_inv = await self._repo.local_inventory_sum(tenant_id)
        sales_map = await self._repo.sales_history(
            tenant_id=tenant_id, end_date=today, days=HISTORY_DAYS
        )
        orm_rules = await self._repo.list_rules(tenant_id)
        logistics_by_rule = await self._repo.rule_logistics_days(
            [r.rule_id for r in orm_rules]
        )
        rules = self._to_rule_dataclasses(orm_rules, logistics_by_rule)
        holidays = await self._repo.list_holidays(tenant_id)

        snapshots: list[MkSupplySkuDailyStat] = []
        forecasts: list[MkSkuForecastDaily] = []

        for lp in listings:
            snap, fc_rows = self._compute_for_listing(
                lp=lp,
                run=run,
                today=today,
                fba_inv=fba_inv,
                local_inv=local_inv,
                sales_map=sales_map,
                rules=rules,
                holidays=holidays,
            )
            snapshots.append(snap)
            forecasts.extend(fc_rows)

        await self._repo.bulk_insert_snapshots(snapshots)
        await self._repo.bulk_insert_forecast(forecasts)

    @staticmethod
    def _to_rule_dataclasses(
        orm_rules: list[MkReplenishmentRule],
        logistics_by_rule: dict[str, tuple[int, ...]] | None = None,
    ) -> list[ReplenishmentRule]:
        logistics_by_rule = logistics_by_rule or {}
        return [
            ReplenishmentRule(
                rule_id=r.rule_id,
                scope_type=r.scope_type,
                mall_id=r.mall_id,
                msku=r.msku,
                safety_days=r.safety_days,
                purchase_duration_days=r.purchase_duration_days,
                delivery_days=r.delivery_days,
                qc_days=r.qc_days,
                enabled=bool(r.enabled),
                logistics_days=logistics_by_rule.get(r.rule_id, ()),
                stock_scope=normalize_stock_scope(
                    r.stock_scope_json or DEFAULT_STOCK_SCOPE
                ),
                updated_at=r.updated_at,
            )
            for r in orm_rules
        ]

    def _compute_for_listing(
        self,
        *,
        lp: MkListingProductSources,
        run: MkCalcRun,
        today: date,
        fba_inv: dict[tuple[int | None, str], RlAmzManageFbaInventory],
        local_inv: dict[tuple[int | None, str], int],
        sales_map: dict[tuple[int | None, str], list[RlAmzSalesDailyReport]],
        rules: list[ReplenishmentRule],
        holidays: list[MkHoliday],
    ) -> tuple[MkSupplySkuDailyStat, list[MkSkuForecastDaily]]:
        key = (lp.mall_id, lp.msku)

        # 1. 规则
        resolved = resolve_rule(rules=rules, mall_id=lp.mall_id, msku=lp.msku)

        # 2. 销量历史 + 预测
        history_rows = sales_map.get(key, [])
        history = [r.sales_volume or 0 for r in history_rows]
        holiday_multipliers = build_holiday_multipliers(
            history_rows=history_rows,
            holidays=holidays,
            country_code=lp.country_code,
            today=today,
            horizon_days=HORIZON_DAYS,
        )
        fc = compute_forecast(
            ForecastInput(
                history=history,
                today=today,
                horizon_days=HORIZON_DAYS,
                seasonal_multipliers=holiday_multipliers,
            )
        )

        # 3. 库存聚合
        inv = fba_inv.get(key)
        stock = aggregate_stock(
            fba_available=inv.afn_fulfillable_quantity if inv else 0,
            fba_inbound_working=inv.afn_inbound_working_quantity if inv else 0,
            fba_inbound_shipped=inv.afn_inbound_shipped_quantity if inv else 0,
            fba_inbound_receiving=inv.afn_inbound_receiving_quantity if inv else 0,
            local_actual=local_inv.get(key, 0),
            local_plan=0,
        )

        # 4. 可售天数
        # sellable_days / suggest_qty 使用规则配置的库存参与口径;
        # total_stock 仍保留完整库存结构,用于展示和库存构成分析。
        planning_stock = participating_stock(stock, resolved.stock_scope)
        sd = sellable_days(stock=planning_stock, daily=fc.forecast_daily)
        fba_only_stock = stock.fba_available + stock.fba_inbound
        fsd = sellable_days(stock=fba_only_stock, daily=fc.forecast_daily)
        local_sd = sellable_days(
            stock=stock.local_actual + stock.local_plan, daily=fc.forecast_daily
        )

        # 5. 风险 + 断货日
        priority = classify_risk(fba_sellable_days=fsd)
        stockout_date = compute_stockout_date(today=today, fba_sellable_days=fsd)

        # 6. Suggest
        sug = compute_suggest(
            SuggestInput(
                forecast_daily=fc.forecast_daily,
                total_stock=planning_stock,
                lead_time_days=resolved.lead_time_days,
                safety_days=resolved.safety_days,
                today=today,
                stockout_date=stockout_date,
                unit_cost=lp.unit_cost,
                currency=lp.currency,
                fx_rate_to_base=Decimal("1"),  # Phase 1 默认 1.0,后续接 fx 表
                base_currency="USD",
            )
        )

        # 7. 销售窗口聚合
        sales_7d = sum(int(r.sales_volume or 0) for r in history_rows[-7:])
        sales_30d = sum(int(r.sales_volume or 0) for r in history_rows[-30:])
        sales_60d = sum(int(r.sales_volume or 0) for r in history_rows[-60:])
        sales_90d = sum(int(r.sales_volume or 0) for r in history_rows)

        snap = MkSupplySkuDailyStat(
            calc_run_id=run.calc_run_id,
            tenant_id=run.tenant_id,
            stat_date=today,
            listing_id=lp.listing_id,
            mall_id=lp.mall_id,
            country_code=lp.country_code,
            msku=lp.msku,
            fnsku=lp.fnsku,
            sku=lp.sku,
            asin=lp.asin,
            product_name=lp.product_name,
            label_ids=lp.label_ids,
            listing_status=lp.listing_status,
            delivery_method=lp.delivery_method,
            risk_level=priority,
            yesterday_sales=int(history_rows[-1].sales_volume or 0)
            if history_rows
            else 0,
            sales_7d=sales_7d,
            sales_30d=sales_30d,
            sales_60d=sales_60d,
            sales_90d=sales_90d,
            forecast_daily=Decimal(str(round(fc.forecast_daily, 2))),
            forecast_source=fc.forecast_source,
            coverage_demand=Decimal(str(round(sug.coverage_demand, 2))),
            fba_available=stock.fba_available,
            fba_inbound_working=inv.afn_inbound_working_quantity if inv else 0,
            fba_inbound_shipped=inv.afn_inbound_shipped_quantity if inv else 0,
            fba_inbound_receiving=inv.afn_inbound_receiving_quantity if inv else 0,
            fba_reserved=inv.reserved_qty if inv else 0,
            local_actual=stock.local_actual,
            local_plan=stock.local_plan,
            total_stock=stock.total_stock,
            planning_stock=planning_stock,
            stock_scope_json=list(resolved.stock_scope),
            sellable_days=Decimal(str(round(sd, 2))) if sd is not None else None,
            fba_sellable_days=Decimal(str(round(fsd, 2))) if fsd is not None else None,
            local_sellable_days=Decimal(str(round(local_sd, 2)))
            if local_sd is not None
            else None,
            safety_days=resolved.safety_days,
            stockout_date=stockout_date,
            lead_time_days=resolved.lead_time_days,
            suggest_purchase=1 if sug.suggest_purchase else 0,
            suggest_qty=sug.suggest_qty,
            suggest_purchase_date=sug.suggest_purchase_date,
            unit_cost=lp.unit_cost,
            currency=lp.currency,
            base_currency="USD",
            fx_rate_to_base=Decimal("1"),
            fx_rate_as_of=run.run_at,
            suggest_amount=Decimal(str(round(sug.suggest_amount, 2)))
            if sug.suggest_amount is not None
            else None,
            suggest_amount_base=Decimal(str(round(sug.suggest_amount_base, 2)))
            if sug.suggest_amount_base is not None
            else None,
            financial_estimate_type="hidden",  # Phase 1 财务派生未接入
            source_type="derived",
        )

        forecast_rows = [
            MkSkuForecastDaily(
                calc_run_id=run.calc_run_id,
                tenant_id=run.tenant_id,
                mall_id=lp.mall_id,
                msku=lp.msku,
                forecast_date=p.forecast_date,
                day_offset=p.day_offset,
                forecast_qty=Decimal(str(round(p.forecast_qty, 2))),
                forecast_source=fc.forecast_source,
                sales_multiplier=Decimal(str(round(p.sales_multiplier, 4))),
                is_adjusted=0,
                source_type="derived",
            )
            for p in fc.series
        ]
        return snap, forecast_rows


def build_holiday_multipliers(
    *,
    history_rows: list[RlAmzSalesDailyReport],
    holidays: list[MkHoliday],
    country_code: str | None,
    today: date,
    horizon_days: int,
) -> list[float] | None:
    """Build daily forecast multipliers from holiday windows.

    Historical closed holiday windows are converted into SKU-level observed
    coefficients. Future/current windows first reuse matching historical
    coefficients, then fall back to the configured holiday coefficient.
    """
    relevant_holidays = [
        h for h in holidays if _holiday_matches_country(h, country_code)
    ]
    if not relevant_holidays:
        return None

    history_by_date = _history_sales_by_date(history_rows)
    historical_by_key = _historical_holiday_coefficients(
        history_by_date=history_by_date,
        holidays=relevant_holidays,
        today=today,
    )
    fallback_coeff = _average(
        coeff for values in historical_by_key.values() for coeff in values
    )

    multipliers: list[float] = []
    has_effect = False
    for i in range(horizon_days):
        forecast_date = today + timedelta(days=i)
        daily_multiplier = 1.0
        for holiday in relevant_holidays:
            start, end = _holiday_window(holiday)
            if start <= forecast_date <= end:
                configured = _clamped_multiplier(float(holiday.sales_multiplier or 1))
                observed = _average(historical_by_key.get(_holiday_key(holiday), []))
                effective = observed if observed is not None else fallback_coeff
                daily_multiplier *= _clamped_multiplier(
                    effective if effective is not None else configured
                )
        if abs(daily_multiplier - 1.0) >= 0.001:
            has_effect = True
        multipliers.append(round(daily_multiplier, 4))

    return multipliers if has_effect else None


def _historical_holiday_coefficients(
    *,
    history_by_date: dict[date, int],
    holidays: list[MkHoliday],
    today: date,
) -> dict[str, list[float]]:
    coefficients: dict[str, list[float]] = {}
    if not history_by_date:
        return coefficients

    for holiday in holidays:
        start, end = _holiday_window(holiday)
        if end >= today:
            continue
        in_window = [
            qty
            for day, qty in history_by_date.items()
            if start <= day <= end
        ]
        if not in_window:
            continue

        baseline_start = start - timedelta(days=max(14, holiday.days_before + 7))
        baseline_end = start - timedelta(days=1)
        baseline = [
            qty
            for day, qty in history_by_date.items()
            if baseline_start <= day <= baseline_end
        ]
        if len(baseline) < 3:
            baseline = [
                qty
                for day, qty in history_by_date.items()
                if day < start or day > end
            ]
        base_avg = _average(baseline)
        holiday_avg = _average(in_window)
        if not base_avg or holiday_avg is None:
            continue

        coeff = _clamped_multiplier(holiday_avg / base_avg)
        if coeff > 0:
            coefficients.setdefault(_holiday_key(holiday), []).append(coeff)

    return coefficients


def _history_sales_by_date(rows: list[RlAmzSalesDailyReport]) -> dict[date, int]:
    out: dict[date, int] = {}
    for row in rows:
        if not row.year_month_day:
            continue
        try:
            day = date.fromisoformat(row.year_month_day[:10])
        except ValueError:
            continue
        out[day] = out.get(day, 0) + int(row.sales_volume or 0)
    return out


def _holiday_window(holiday: MkHoliday) -> tuple[date, date]:
    start = holiday.peak_date - timedelta(days=max(0, int(holiday.days_before or 0)))
    end = holiday.peak_date + timedelta(days=max(0, int(holiday.days_after or 0)))
    return start, end


def _holiday_matches_country(holiday: MkHoliday, country_code: str | None) -> bool:
    if not holiday.country_code or not country_code:
        return True
    return holiday.country_code.upper() == country_code.upper()


def _holiday_key(holiday: MkHoliday) -> str:
    text = f"{holiday.holiday_id or ''} {holiday.name or ''}".lower()
    aliases = {
        "mother": "mothers_day",
        "mothers": "mothers_day",
        "母亲": "mothers_day",
        "memorial": "memorial_day",
        "阵亡": "memorial_day",
        "prime": "prime_day",
        "black": "black_friday",
        "黑五": "black_friday",
        "christmas": "christmas",
        "圣诞": "christmas",
        "new year": "new_year",
        "春节": "spring_festival",
    }
    for needle, key in aliases.items():
        if needle in text:
            return key
    normalized = re.sub(r"\d{4}|[^a-z\u4e00-\u9fa5]+", " ", text)
    words = [w for w in normalized.split() if w]
    return "_".join(words[:3]) or "holiday"


def _average(values) -> float | None:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _clamped_multiplier(value: float) -> float:
    if value <= 0:
        return 1.0
    return max(MIN_HOLIDAY_MULTIPLIER, min(MAX_HOLIDAY_MULTIPLIER, value))
