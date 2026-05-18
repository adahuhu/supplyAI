"""mk_* 派生 / 配置表种子数据写入(13 张表).

注:mk_supply_sku_daily_stat / mk_sku_forecast_daily / mk_listing_product_sources
等"派生"表在本期通过简化版 Calc 直接落表;
Phase 4 引入 Calc Engine 后改为正式 calc_run 触发。
"""
from __future__ import annotations

import math
from datetime import datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scripts.seed_data.constants import (
    DEFAULT_CALC_RUN_ID,
    DEFAULT_FORECAST,
    DEFAULT_LEAD_TIME,
    DEFAULT_RULE,
    LOGISTICS_METHODS,
    STORES,
    TODAY,
    WAREHOUSES,
)
from scripts.seed_data.generators import (
    SkuSeed,
    fx_rate_to_base,
)
from supplyai.config import settings
from supplyai.models.mk import (
    MkCalcRun,
    MkForecastRule,
    MkListingProductSources,
    MkReplenishmentRule,
    MkRuleLogisticsMethod,
    MkSkuForecastDaily,
    MkSkuInboundDetail,
    MkStockoutEvent,
    MkSupplySkuDailyStat,
    MkTenantConfig,
    MkWarehouseMapping,
)
from supplyai.utils.logging import get_logger

logger = get_logger("seed.mk")
TENANT = settings.default_tenant_id


async def _is_empty(session: AsyncSession, model) -> bool:
    cnt = await session.scalar(select(func.count()).select_from(model))
    return (cnt or 0) == 0


async def seed_mk_tenant_config(session: AsyncSession) -> None:
    if not await _is_empty(session, MkTenantConfig):
        logger.info("mk_tenant_config_skipped")
        return
    session.add(
        MkTenantConfig(
            tenant_id=TENANT,
            tenant_name="Aurora Demo",
            timezone="Asia/Shanghai",
            daily_push_time=time(8, 0, 0),
            source_refresh_times_json=["00:30", "12:00", "18:00"],
        )
    )
    await session.commit()
    logger.info("mk_tenant_config_seeded")


async def seed_mk_warehouse_mapping(session: AsyncSession) -> None:
    if not await _is_empty(session, MkWarehouseMapping):
        logger.info("mk_warehouse_mapping_skipped")
        return
    now = datetime.utcnow()
    for w in WAREHOUSES:
        session.add(
            MkWarehouseMapping(
                tenant_id=TENANT,
                warehouse_id=w["warehouse_id"],
                warehouse_name=w["warehouse_name"],
                warehouse_type=w["warehouse_type"],
                include_in_local_actual=w["include_in_local_actual"],
                source_type="mock",
                updated_at=now,
            )
        )
    await session.commit()
    logger.info("mk_warehouse_mapping_seeded", count=len(WAREHOUSES))


async def seed_mk_rules(session: AsyncSession) -> None:
    """全局补货规则 + 多物流方式 + 全局预测规则."""
    if not await _is_empty(session, MkReplenishmentRule):
        logger.info("mk_replenishment_rule_skipped")
        return

    now = datetime.utcnow()
    # 1. 补货规则(global)
    session.add(
        MkReplenishmentRule(
            rule_id=DEFAULT_RULE["rule_id"],
            tenant_id=TENANT,
            scope_type="global",
            mall_id=None,
            msku=None,
            safety_days=DEFAULT_RULE["safety_days"],
            purchase_duration_days=DEFAULT_RULE["purchase_duration_days"],
            delivery_days=DEFAULT_RULE["delivery_days"],
            qc_days=DEFAULT_RULE["qc_days"],
            rule_version=DEFAULT_RULE["rule_version"],
            enabled=1,
            updated_by="system",
            updated_at=now,
            source_type="mock",
        )
    )
    # 2. 物流方式(每行一个)
    for i, m in enumerate(LOGISTICS_METHODS):
        session.add(
            MkRuleLogisticsMethod(
                rule_id=DEFAULT_RULE["rule_id"],
                logistics_mode=m["mode"],
                logistics_days=m["days"],
                is_active=1,
                source_type="mock",
            )
        )
    # 3. 预测规则(global default)
    session.add(
        MkForecastRule(
            rule_id=DEFAULT_FORECAST["rule_id"],
            tenant_id=TENANT,
            scope_type="global",
            mall_id=None,
            msku=None,
            forecast_mode=DEFAULT_FORECAST["forecast_mode"],
            default_daily_sales=Decimal(str(DEFAULT_FORECAST["default_daily_sales"])),
            denoise_enabled=DEFAULT_FORECAST["denoise_enabled"],
            allow_empty_rule=1,
            updated_by="system",
            updated_at=now,
            source_type="mock",
        )
    )
    await session.commit()
    logger.info(
        "mk_rules_seeded",
        replenishment=1,
        logistics=len(LOGISTICS_METHODS),
        forecast=1,
    )


async def seed_mk_calc_run(session: AsyncSession) -> None:
    if not await _is_empty(session, MkCalcRun):
        logger.info("mk_calc_run_skipped")
        return
    now = datetime.utcnow()
    session.add(
        MkCalcRun(
            calc_run_id=DEFAULT_CALC_RUN_ID,
            tenant_id=TENANT,
            stat_date=TODAY,
            run_type="scheduled",
            run_at=now,
            source_sales_at=now,
            source_inventory_at=now,
            source_inbound_at=now,
            rule_version=DEFAULT_RULE["rule_version"],
            status="success",
            source_type="derived",
        )
    )
    await session.commit()
    logger.info("mk_calc_run_seeded", calc_run_id=DEFAULT_CALC_RUN_ID)


async def seed_mk_listing_product_sources(
    session: AsyncSession, skus: list[SkuSeed]
) -> None:
    if not await _is_empty(session, MkListingProductSources):
        logger.info("mk_listing_product_sources_skipped")
        return
    now = datetime.utcnow()
    for sku in skus:
        session.add(
            MkListingProductSources(
                tenant_id=TENANT,
                listing_id=sku.listing_id,
                mall_id=sku.mall_id,
                msku=sku.msku,
                sku=sku.sku,
                asin=sku.asin,
                fnsku=sku.fnsku,
                delivery_method="FBA",
                listing_status="ACTIVE",
                title=sku.item_name,
                product_name=sku.product_name,
                image_url=sku.image_url,
                brand=sku.brand,
                category=sku.category,
                label_ids=sku.label_ids,
                country_code=sku.country_code,
                country=sku.country,
                unit_cost=sku.unit_cost,
                sale_price=sku.sale_price,
                currency=sku.currency,
                owner=str(sku.owner_user_id),
                refreshed_at=now,
            )
        )
    await session.commit()
    logger.info("mk_listing_product_sources_seeded", count=len(skus))


async def seed_mk_supply_snapshots(session: AsyncSession, skus: list[SkuSeed]) -> None:
    """备货计划核心快照 — 简化版 calc,Phase 4 由 Calc Engine 替代."""
    if not await _is_empty(session, MkSupplySkuDailyStat):
        logger.info("mk_supply_sku_daily_stat_skipped")
        return

    now = datetime.utcnow()
    for sku in skus:
        # 财务字段(简化:基于近 7 天销量 × 单价 × 系数)
        sales_7d = sum(sku.daily_sales_history[-7:])
        sales_30d = sum(sku.daily_sales_history[-30:])
        sales_60d = sum(sku.daily_sales_history[-60:])
        sales_90d = sum(sku.daily_sales_history)
        revenue_7d = Decimal(sales_7d) * sku.sale_price
        cost_7d = Decimal(sales_7d) * sku.unit_cost
        expense_7d = revenue_7d * Decimal("0.51")
        gross_profit_7d = revenue_7d - expense_7d - cost_7d
        gross_margin = (
            (gross_profit_7d / revenue_7d).quantize(Decimal("0.0001"))
            if revenue_7d > 0
            else Decimal("0")
        )

        # 多币种
        fx = fx_rate_to_base(sku.currency)
        suggest_amount = Decimal(sku.suggest_qty) * sku.unit_cost
        suggest_amount_base = suggest_amount * Decimal(str(fx))

        session.add(
            MkSupplySkuDailyStat(
                calc_run_id=DEFAULT_CALC_RUN_ID,
                tenant_id=TENANT,
                stat_date=TODAY,
                listing_id=sku.listing_id,
                mall_id=sku.mall_id,
                country_code=sku.country_code,
                msku=sku.msku,
                fnsku=sku.fnsku,
                sku=sku.sku,
                asin=sku.asin,
                product_name=sku.product_name,
                label_ids=sku.label_ids,
                listing_status="ACTIVE",
                delivery_method="FBA",
                risk_level=sku.risk_level,
                yesterday_sales=sku.daily_sales_history[-1],
                yesterday_revenue=Decimal(sku.daily_sales_history[-1]) * sku.sale_price,
                revenue_7d=revenue_7d,
                expense_7d=expense_7d,
                cost_7d=cost_7d,
                gross_profit_7d=gross_profit_7d,
                gross_margin=gross_margin,
                financial_estimate_type="allocated",  # SKU 级毛利为店铺分摊估算
                sales_7d=sales_7d,
                sales_30d=sales_30d,
                sales_60d=sales_60d,
                sales_90d=sales_90d,
                forecast_daily=sku.forecast_daily,
                forecast_source="default",
                coverage_demand=sku.coverage_demand,
                last_7d_raw_daily=sku.last_7d_raw_daily,
                last_7d_denoised_daily=sku.last_7d_denoised_daily,
                fba_available=sku.fba_available,
                fba_inbound_working=sku.fba_inbound_working,
                fba_inbound_shipped=sku.fba_inbound_shipped,
                fba_inbound_receiving=sku.fba_inbound_receiving,
                fba_reserved=sku.fba_reserved,
                local_actual=sku.local_actual,
                local_plan=sku.local_plan,
                total_stock=sku.total_stock,
                sellable_days=sku.sellable_days,
                fba_sellable_days=sku.fba_sellable_days,
                local_sellable_days=Decimal(
                    round(
                        (sku.local_actual + sku.local_plan) / float(sku.forecast_daily)
                        if float(sku.forecast_daily) > 0
                        else 0,
                        2,
                    )
                ),
                safety_days=DEFAULT_RULE["safety_days"],
                stockout_date=sku.stockout_date,
                lead_time_days=DEFAULT_LEAD_TIME,
                suggest_purchase=1 if sku.suggest_qty > 0 else 0,
                suggest_qty=sku.suggest_qty,
                suggest_purchase_date=sku.suggest_purchase_date,
                unit_cost=sku.unit_cost,
                currency=sku.currency,
                base_currency="USD",
                fx_rate_to_base=Decimal(str(fx)),
                fx_rate_as_of=now,
                suggest_amount=suggest_amount,
                suggest_amount_base=suggest_amount_base,
                updated_at=now,
                source_type="derived",
            )
        )
    await session.commit()
    logger.info("mk_supply_sku_daily_stat_seeded", count=len(skus))


async def seed_mk_sku_forecast_daily(
    session: AsyncSession, skus: list[SkuSeed]
) -> None:
    """未来 45 天逐日预测 = 每天 forecast_daily(简化:无节日加成)."""
    if not await _is_empty(session, MkSkuForecastDaily):
        logger.info("mk_sku_forecast_daily_skipped")
        return

    future_days = 45
    for sku in skus:
        for d in range(future_days):
            forecast_date = TODAY + timedelta(days=d)
            session.add(
                MkSkuForecastDaily(
                    calc_run_id=DEFAULT_CALC_RUN_ID,
                    tenant_id=TENANT,
                    mall_id=sku.mall_id,
                    msku=sku.msku,
                    forecast_date=forecast_date,
                    day_offset=d,
                    forecast_qty=sku.forecast_daily,
                    forecast_source="default",
                    sales_multiplier=Decimal("1"),
                    is_adjusted=0,
                    source_type="derived",
                )
            )
    await session.commit()
    logger.info(
        "mk_sku_forecast_daily_seeded",
        sku_count=len(skus),
        rows=len(skus) * future_days,
    )


async def seed_mk_sku_inbound_detail(
    session: AsyncSession, skus: list[SkuSeed]
) -> None:
    """本地侧在途明细 — 仅有 local_plan > 0 的 SKU."""
    if not await _is_empty(session, MkSkuInboundDetail):
        logger.info("mk_sku_inbound_detail_skipped")
        return

    inbound_count = 0
    for sku in skus:
        if sku.local_plan <= 0:
            continue

        # 拆 local_plan 成 1-3 条单据
        remaining = sku.local_plan
        types = ["purchase", "transfer", "processing"]
        statuses = ["in_transit", "pending", "receiving"]
        for i in range(min(2, max(1, remaining // 50))):
            qty = remaining if i == 1 else round(remaining * 0.6)
            remaining -= qty
            if qty <= 0:
                continue

            session.add(
                MkSkuInboundDetail(
                    inbound_id=f"INB-{sku.msku}-{i:02d}",
                    tenant_id=TENANT,
                    mall_id=sku.mall_id,
                    msku=sku.msku,
                    sku=sku.sku,
                    inbound_type=types[i % len(types)],
                    inbound_status=statuses[i % len(statuses)],
                    qty=qty,
                    expected_arrival_date=TODAY + timedelta(days=10 + i * 7),
                    source_order_no=f"PO-{sku.msku}-{i}",
                    source_type="mock",
                )
            )
            inbound_count += 1
    await session.commit()
    logger.info("mk_sku_inbound_detail_seeded", rows=inbound_count)


async def seed_mk_stockout_events(
    session: AsyncSession, skus: list[SkuSeed]
) -> None:
    """断货事件 — 模拟近 7 天断货趋势(P1 SKU 部分曾断货)."""
    if not await _is_empty(session, MkStockoutEvent):
        logger.info("mk_stockout_event_skipped")
        return

    event_count = 0
    p1_skus = [s for s in skus if s.risk_level == "p1"]

    # 选 60% 的 P1 SKU 模拟历史断货事件
    for i, sku in enumerate(p1_skus):
        if i % 5 == 0:  # 跳过部分,模拟 80% 命中
            continue

        # 历史断货:5-15 天前发生,持续 1-3 天后恢复
        days_ago = 3 + (i % 12)
        duration = 1 + (i % 3)
        start_at = datetime.combine(TODAY - timedelta(days=days_ago), datetime.min.time())
        end_at = start_at + timedelta(days=duration)

        session.add(
            MkStockoutEvent(
                event_id=f"SO-{sku.msku}-{days_ago:02d}",
                tenant_id=TENANT,
                mall_id=sku.mall_id,
                msku=sku.msku,
                start_at=start_at,
                end_at=end_at,
                duration_days=Decimal(str(duration)),
                event_status="closed",
                source_type="derived",
            )
        )
        event_count += 1
    await session.commit()
    logger.info("mk_stockout_event_seeded", rows=event_count)
