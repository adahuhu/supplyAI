"""演示数据生成脚本 — 写入 SQLite 本地 DB.

覆盖全部 21 张表:8 rl_*(真实源表镜像)+ 13 mk_*(派生 / 配置)。

执行顺序:
  1. mk_tenant_config + mk_warehouse_mapping(基础配置)
  2. rl_mall(店铺)
  3. rl_amz_all_listing / rl_amz_listing_detail / rl_product(商品主数据)
  4. rl_amz_sales_daily_report(90 天历史销量)
  5. rl_amz_manage_fba_inventory(FBA 库存)
  6. rl_inventory_detail(本地库存明细)
  7. rl_amz_finances_profit_mall_100228(店铺日财务)
  8. mk_replenishment_rule + mk_rule_logistics_method + mk_forecast_rule
  9. mk_calc_run(默认演示批次)
 10. mk_listing_product_sources(物化商品视图)
 11. mk_supply_sku_daily_stat(核心快照)
 12. mk_sku_forecast_daily(未来 45 天逐日预测)
 13. mk_sku_inbound_detail(本地在途明细)
 14. mk_stockout_event(断货事件)

幂等:每个 seeder 检查目标表是否为空,非空则跳过。
重置:删除 data/supplyai.db 后 alembic upgrade head 再重跑。
"""
from __future__ import annotations

import asyncio
import sys
import time

from supplyai.config import settings
from supplyai.db import async_session_factory
from supplyai.utils.logging import configure_logging, get_logger

# scripts/ 不是包,需要把项目根加进 sys.path 以便 import scripts.seed_data.*
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.seed_data.generators import generate_skus  # noqa: E402
from scripts.seed_data.mk_seeders import (  # noqa: E402
    seed_mk_calc_run,
    seed_mk_listing_product_sources,
    seed_mk_rules,
    seed_mk_sku_forecast_daily,
    seed_mk_sku_inbound_detail,
    seed_mk_stockout_events,
    seed_mk_supply_snapshots,
    seed_mk_tenant_config,
    seed_mk_warehouse_mapping,
)
from scripts.seed_data.rl_seeders import (  # noqa: E402
    seed_rl_fba_inventory,
    seed_rl_finances_profit,
    seed_rl_inventory_detail,
    seed_rl_listing_details,
    seed_rl_listings,
    seed_rl_mall,
    seed_rl_product,
    seed_rl_sales,
)

logger = get_logger("seed")


async def main() -> None:
    configure_logging(level=settings.log_level, fmt=settings.log_format)
    logger.info("seeding_start", db=settings.database_url)
    t0 = time.time()

    # 1. 生成 48 个 SKU 完整种子(确定性,seed=42)
    skus = generate_skus()
    logger.info("skus_generated", count=len(skus))

    # 2. 写入数据库(每个 step 一个事务)
    async with async_session_factory() as session:
        # 配置层
        await seed_mk_tenant_config(session)
        await seed_mk_warehouse_mapping(session)

        # 真实源表
        await seed_rl_mall(session)
        await seed_rl_listings(session, skus)
        await seed_rl_listing_details(session, skus)
        await seed_rl_product(session, skus)
        await seed_rl_sales(session, skus)
        await seed_rl_fba_inventory(session, skus)
        await seed_rl_inventory_detail(session, skus)
        await seed_rl_finances_profit(session)

        # 规则
        await seed_mk_rules(session)

        # 计算批次 + 派生
        await seed_mk_calc_run(session)
        await seed_mk_listing_product_sources(session, skus)
        await seed_mk_supply_snapshots(session, skus)
        await seed_mk_sku_forecast_daily(session, skus)
        await seed_mk_sku_inbound_detail(session, skus)
        await seed_mk_stockout_events(session, skus)

    elapsed = time.time() - t0
    logger.info("seeding_done", elapsed_seconds=round(elapsed, 2))

    # 3. 风险等级分布概览
    risk_counts: dict[str, int] = {"p1": 0, "p2": 0, "p3": 0, "safe": 0}
    for sku in skus:
        risk_counts[sku.risk_level] = risk_counts.get(sku.risk_level, 0) + 1
    suggest_count = sum(1 for s in skus if s.suggest_qty > 0)
    suggest_total_qty = sum(s.suggest_qty for s in skus)
    logger.info(
        "summary",
        total_skus=len(skus),
        risk_distribution=risk_counts,
        suggest_purchase_count=suggest_count,
        suggest_total_qty=suggest_total_qty,
    )


if __name__ == "__main__":
    asyncio.run(main())
