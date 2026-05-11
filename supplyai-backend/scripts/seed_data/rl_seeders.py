"""rl_* 真实源表演示数据写入(8 张表)."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scripts.seed_data.constants import (
    LOCAL_WAREHOUSE_IDS,
    STORES,
    TODAY,
)
from scripts.seed_data.generators import (
    SkuSeed,
    fx_rate_to_base,
)
from supplyai.config import settings
from supplyai.models.rl import (
    RlAmzAllListing,
    RlAmzFinancesProfit,
    RlAmzListingDetail,
    RlAmzManageFbaInventory,
    RlAmzSalesDailyReport,
    RlInventoryDetail,
    RlMall,
    RlProduct,
)
from supplyai.utils.logging import get_logger

logger = get_logger("seed.rl")
TENANT = settings.default_tenant_id


async def _is_empty(session: AsyncSession, model) -> bool:
    cnt = await session.scalar(select(func.count()).select_from(model))
    return (cnt or 0) == 0


async def seed_rl_mall(session: AsyncSession) -> None:
    if not await _is_empty(session, RlMall):
        logger.info("rl_mall_skipped")
        return

    now = datetime.utcnow()
    for s in STORES:
        session.add(
            RlMall(
                mall_id=s["mall_id"],
                tenant_id=TENANT,
                account=s["account"],
                mall_name=s["name"],
                seller_id=f"AMZ-{s['account'].upper()}",
                status="NORMAL",
                mall_status="ENABLED",
                mall_type="amzon",
                type=0,
                country_code=s["country_code"],
                country=s["country"],
                region=s["region"],
                marketplace_id=s["marketplace_id"],
                aws_region=s["aws_region"],
                settlement_currency=s["currency"],
                transaction_rate=Decimal("0.025"),
                created_time=now,
                update_time=now,
                del_flag=0,
            )
        )
    await session.commit()
    logger.info("rl_mall_seeded", count=len(STORES))


async def seed_rl_listings(session: AsyncSession, skus: list[SkuSeed]) -> None:
    if not await _is_empty(session, RlAmzAllListing):
        logger.info("rl_amz_all_listing_skipped")
        return

    now = datetime.utcnow()
    open_date = TODAY - timedelta(days=180)
    for sku in skus:
        session.add(
            RlAmzAllListing(
                listing_id=sku.listing_id,
                tenant_id=TENANT,
                mall_id=sku.mall_id,
                country_code=sku.country_code,
                country=sku.country,
                amz_listing_id=f"AMZ-{sku.listing_id}",
                asin=sku.asin,
                parent_asin=sku.parent_asin,
                item_name=sku.item_name,
                msku=sku.msku,
                fnsku=sku.fnsku,
                delivery_method="FBA",  # Phase 1 全部 FBA
                fulfillment_channel="Amazon-NA",
                status="ACTIVE",
                product_type=sku.category,
                price=sku.sale_price,
                platform_fee=sku.sale_price * Decimal("0.15"),
                fba_estimated_fee=sku.sale_price * Decimal("0.10"),
                fbm_available_stock=0,
                open_date=open_date,
                asin_type="INDEPENDENT",
                default_currency=sku.currency,
                last_pull_time=now,
                created_time=now,
                update_time=now,
                del_flag=0,
            )
        )
    await session.commit()
    logger.info("rl_amz_all_listing_seeded", count=len(skus))


async def seed_rl_listing_details(session: AsyncSession, skus: list[SkuSeed]) -> None:
    if not await _is_empty(session, RlAmzListingDetail):
        logger.info("rl_amz_listing_detail_skipped")
        return

    now = datetime.utcnow()
    open_date = TODAY - timedelta(days=180)
    for i, sku in enumerate(skus):
        session.add(
            RlAmzListingDetail(
                listing_detail_id=2_000_000 + i,
                tenant_id=TENANT,
                listing_id=sku.listing_id,
                msku=sku.msku,
                mall_id=sku.mall_id,
                brand=sku.brand,
                image_url_px75=sku.image_url,
                image_url=sku.image_url.replace("96x96", "1600x1600"),
                product_type=sku.category,
                display_group_title=sku.category.split(" / ")[0] if " / " in sku.category else sku.category,
                classification_title=sku.category,
                package_length=Decimal("20"),
                package_width=Decimal("15"),
                package_height=Decimal("10"),
                package_weight=Decimal("0.5"),
                start_selling_date=datetime.combine(open_date, datetime.min.time()),
                first_order_date=datetime.combine(open_date + timedelta(days=3), datetime.min.time()),
                last_pull_time=now,
                created_time=now,
                update_time=now,
                del_flag=0,
            )
        )
    await session.commit()
    logger.info("rl_amz_listing_detail_seeded", count=len(skus))


async def seed_rl_product(session: AsyncSession, skus: list[SkuSeed]) -> None:
    if not await _is_empty(session, RlProduct):
        logger.info("rl_product_skipped")
        return

    now = datetime.utcnow()
    # ERP product 按 SKU 唯一去重(同 SKU 不同 mall 共享 product)
    seen_skus: set[str] = set()
    for sku in skus:
        if sku.sku in seen_skus:
            continue
        seen_skus.add(sku.sku)

        # 模拟产品物流配置(JSON)
        product_logistics = [
            {"mode": "海运", "days": 35, "cost_per_kg": 6.5},
            {"mode": "空运", "days": 8, "cost_per_kg": 28.0},
        ]
        session.add(
            RlProduct(
                product_id=sku.product_id,
                tenant_id=TENANT,
                type="ORDINARY",
                sku=sku.sku,
                product_name=sku.product_name,
                category_id=hash(sku.category) & 0xFFFFFF,
                prod_line_id=hash(sku.brand) & 0xFFFFFF,
                brand_id=hash(sku.brand) & 0xFFFFFF,
                model=f"{sku.brand}-{sku.sku[-6:]}",
                unit="件",
                status="ON_SALE",
                developer_user_id=sku.owner_user_id,
                responsible_user_ids=str(sku.owner_user_id),
                purchaseer_user_id=5099,
                purchase_delivery_date=5,
                purchase_price=sku.unit_cost,
                product_logistics_list=product_logistics,
                image_url=sku.image_url.replace("96x96", "1600x1600"),
                image_url_px75=sku.image_url,
                team_id=1,
                dept_id=1,
                created_time=now,
                updated_time=now,
                del_flag=0,
            )
        )
    await session.commit()
    logger.info("rl_product_seeded", count=len(seen_skus))


async def seed_rl_sales(session: AsyncSession, skus: list[SkuSeed]) -> None:
    """每个 SKU 写 90 天销量历史."""
    if not await _is_empty(session, RlAmzSalesDailyReport):
        logger.info("rl_amz_sales_daily_report_skipped")
        return

    now = datetime.utcnow()
    sales_id = 3_000_000
    for sku in skus:
        for d_idx, qty in enumerate(sku.daily_sales_history):
            ymd = TODAY - timedelta(days=len(sku.daily_sales_history) - d_idx)
            sales_revenue = Decimal(qty) * sku.sale_price
            session.add(
                RlAmzSalesDailyReport(
                    id=sales_id,
                    tenant_id=TENANT,
                    mall_id=sku.mall_id,
                    msku=sku.msku,
                    year_month_day=ymd.isoformat(),
                    listing_id=sku.listing_id,
                    asin=sku.asin,
                    parent_asin=sku.parent_asin,
                    country=sku.country,
                    country_code=sku.country_code,
                    currency_code=sku.currency,
                    item_name=sku.item_name,
                    image_url=sku.image_url,
                    image_url_px75=sku.image_url,
                    sales_volume=qty,
                    sales=sales_revenue,
                    order_quantity=max(1, qty // 2) if qty > 0 else 0,
                    created_time=now,
                    update_time=now,
                )
            )
            sales_id += 1
    await session.commit()
    logger.info("rl_amz_sales_daily_report_seeded", rows=sales_id - 3_000_000)


async def seed_rl_fba_inventory(session: AsyncSession, skus: list[SkuSeed]) -> None:
    if not await _is_empty(session, RlAmzManageFbaInventory):
        logger.info("rl_amz_manage_fba_inventory_skipped")
        return

    now = datetime.utcnow()
    inv_id = 4_000_000
    for sku in skus:
        afn_total = (
            sku.fba_available
            + sku.fba_inbound_working
            + sku.fba_inbound_shipped
            + sku.fba_inbound_receiving
            + sku.fba_reserved
        )
        # 预留拆分
        reserved_orders = round(sku.fba_reserved * 0.6)
        reserved_transfers = round(sku.fba_reserved * 0.3)
        reserved_processing = sku.fba_reserved - reserved_orders - reserved_transfers

        session.add(
            RlAmzManageFbaInventory(
                manage_inventory_id=inv_id,
                tenant_id=TENANT,
                mall_id=sku.mall_id,
                msku=sku.msku,
                fnsku=sku.fnsku,
                asin=sku.asin,
                afn_fulfillable_quantity=sku.fba_available,
                afn_inbound_working_quantity=sku.fba_inbound_working,
                afn_inbound_shipped_quantity=sku.fba_inbound_shipped,
                afn_inbound_receiving_quantity=sku.fba_inbound_receiving,
                reserved_qty=sku.fba_reserved,
                reserved_customerorders=reserved_orders,
                reserved_fc_transfers=reserved_transfers,
                reserved_fc_processing=reserved_processing,
                afn_unsellable_quantity=0,
                afn_total_quantity=afn_total,
                last_pull_time=now,
                created_time=now,
                update_time=now,
                del_flag=0,
            )
        )
        inv_id += 1
    await session.commit()
    logger.info("rl_amz_manage_fba_inventory_seeded", count=len(skus))


async def seed_rl_inventory_detail(session: AsyncSession, skus: list[SkuSeed]) -> None:
    """本地库存明细 — 按 (warehouse, sku, mall, fnsku) 维度展开."""
    if not await _is_empty(session, RlInventoryDetail):
        logger.info("rl_inventory_detail_skipped")
        return

    now = datetime.utcnow()
    detail_id = 5_000_000
    for sku in skus:
        if sku.local_actual <= 0:
            continue

        # 把 local_actual 拆成 4 类
        avail = round(sku.local_actual * 0.70)
        avail_locked = round(sku.local_actual * 0.15)
        defective = round(sku.local_actual * 0.10)
        defective_locked = sku.local_actual - avail - avail_locked - defective
        defective_locked = max(0, defective_locked)

        # 选一个本地仓
        warehouse_id = LOCAL_WAREHOUSE_IDS[hash(sku.msku) % len(LOCAL_WAREHOUSE_IDS)]

        unit_price = sku.unit_cost * Decimal("0.7")
        unit_cost = sku.unit_cost * Decimal("0.2")
        unit_logistics = sku.unit_cost * Decimal("0.1")
        unit_inventory = sku.unit_cost
        total_qty = sku.local_actual
        inventory_value = unit_price * Decimal(total_qty)
        total_cost = (unit_cost + unit_logistics) * Decimal(total_qty)
        total_inventory_cost = unit_inventory * Decimal(total_qty)

        session.add(
            RlInventoryDetail(
                detail_id=detail_id,
                tenant_id=TENANT,
                key=f"{warehouse_id}-{sku.sku}-{sku.mall_id}-{sku.fnsku}",
                product_id=sku.product_id,
                sku=sku.sku,
                warehouse_id=warehouse_id,
                mall_id=sku.mall_id,
                msku=sku.msku,
                mall_identify_code=sku.fnsku,
                mall_type=0,
                available_quantity=avail,
                available_locked_quantity=avail_locked,
                defective_quantity=defective,
                defective_locked_quantity=defective_locked,
                unit_price=unit_price,
                unit_cost=unit_cost,
                unit_logistics_cost=unit_logistics,
                unit_inventory_cost=unit_inventory,
                inventory_value=inventory_value,
                total_cost=total_cost,
                total_inventory_cost=total_inventory_cost,
                owners=str(sku.owner_user_id),
                dept_id=1,
                country_code=sku.country_code,
                country=sku.country,
                created_time=now,
                update_time=now,
                del_flag=0,
            )
        )
        detail_id += 1
    await session.commit()
    logger.info("rl_inventory_detail_seeded", rows=detail_id - 5_000_000)


async def seed_rl_finances_profit(session: AsyncSession) -> None:
    """店铺级利润 / 费用日结 — 每店铺写 30 天."""
    if not await _is_empty(session, RlAmzFinancesProfit):
        logger.info("rl_amz_finances_profit_skipped")
        return

    now = datetime.utcnow()
    fin_id = 6_000_000
    for store in STORES:
        for d in range(30):
            settle_date = TODAY - timedelta(days=d + 1)
            # 简化的日财务数据
            base_sales = Decimal(str(2000 + (store["mall_id"] % 1000)))
            session.add(
                RlAmzFinancesProfit(
                    id=fin_id,
                    tenant_id=TENANT,
                    mall_id=store["mall_id"],
                    settlement_date=settle_date,
                    currency_code=store["currency"],
                    sp_ads_fee=base_sales * Decimal("0.05"),
                    sb_ads_fee=base_sales * Decimal("0.02"),
                    sbv_ads_fee=Decimal("0"),
                    sd_ads_fee=base_sales * Decimal("0.01"),
                    ads_fee_share=base_sales * Decimal("0.005"),
                    product_ads_payment=Decimal("0"),
                    month_storage_fee=base_sales * Decimal("0.03"),
                    permanent_storage_fee=Decimal("0"),
                    excess_storage_fee=Decimal("0"),
                    fba_storage_fee=base_sales * Decimal("0.025"),
                    fba_long_storage_fee=base_sales * Decimal("0.005"),
                    fba_sales=base_sales * Decimal("0.95"),
                    fbm_sales=base_sales * Decimal("0.05"),
                    commission=base_sales * Decimal("0.15"),
                    fba_commission=base_sales * Decimal("0.12"),
                    fbm_commission=base_sales * Decimal("0.03"),
                    fba_shipment_fee=base_sales * Decimal("0.08"),
                    created_time=now,
                    update_time=now,
                )
            )
            fin_id += 1
    await session.commit()
    logger.info("rl_amz_finances_profit_seeded", rows=fin_id - 6_000_000)
