"""演示数据生成器 — 确定性随机(seed=42),保证可重现."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from scripts.seed_data.constants import (
    DEFAULT_LEAD_TIME,
    DEFAULT_RULE,
    DEFAULT_TOTAL_COVERAGE,
    OWNERS,
    PRODUCTS,
    RISK_DISTRIBUTION,
    SEED,
    STORES,
    TODAY,
    TOTAL_SKUS,
)

# 固定 seed 保证演示数据稳定
random.seed(SEED)


@dataclass
class SkuSeed:
    """单个 SKU 的演示数据种子(48 个 SKU 中的一个)."""

    # 标识
    listing_id: int
    msku: str
    sku: str  # ERP SKU
    asin: str
    fnsku: str
    parent_asin: str
    product_name: str
    category: str
    brand: str
    item_name: str  # listing 标题(亚马逊页面)
    image_url: str

    # 归属
    mall_id: int
    mall_name: str
    country_code: str
    country: str
    currency: str

    # ERP product
    product_id: int
    owner_user_id: int
    owner_name: str

    # 价格 / 成本
    sale_price: Decimal
    unit_cost: Decimal

    # 销量预测
    forecast_daily: Decimal  # 未来平均日销
    last_7d_raw_daily: Decimal
    last_7d_denoised_daily: Decimal
    daily_sales_history: list[int] = field(default_factory=list)  # 90 天 history

    # FBA 库存
    fba_available: int = 0
    fba_inbound_working: int = 0
    fba_inbound_shipped: int = 0
    fba_inbound_receiving: int = 0
    fba_reserved: int = 0

    # 本地库存
    local_actual: int = 0  # 真实可用 + 锁定 + 次品
    local_plan: int = 0  # 在途增量

    # 派生
    risk_level: str = "safe"
    fba_sellable_days: Decimal = Decimal("0")
    sellable_days: Decimal = Decimal("0")
    total_stock: int = 0
    coverage_demand: Decimal = Decimal("0")
    suggest_qty: int = 0
    stockout_date: date | None = None
    suggest_purchase_date: date | None = None


def _gen_asin(seed: int) -> str:
    base = (seed * 13 + 113) % (36**8)
    s = ""
    for _ in range(8):
        s = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[base % 36] + s
        base //= 36
    return ("B0" + s)[:10]


def _gen_msku(idx: int) -> str:
    return f"MS{40021 + idx * 13:05d}"[-7:]


def _gen_fnsku(idx: int) -> str:
    return f"X00{(idx * 31 + 417) % 10000:04d}"


def _gen_sku(idx: int, country: str) -> str:
    return f"SKU-{70000 + idx * 7:05d}-{country}"


def _gen_image_url(idx: int, msku: str) -> str:
    suffix = msku[-3:]
    color = "f1f5f9" if idx % 2 else "e2e8f0"
    return f"https://placehold.co/96x96/{color}/64748b?text={suffix}"


def _build_risk_targets() -> list[str]:
    """生成 48 个风险等级目标(按分布预先打乱)."""
    targets: list[str] = []
    for level, count in RISK_DISTRIBUTION.items():
        targets.extend([level] * count)
    random.shuffle(targets)
    return targets


def _pick_fba_sellable_days(risk: str) -> int:
    """按风险等级返回目标 FBA 可售天数."""
    if risk == "p1":
        return random.randint(2, 7)
    if risk == "p2":
        return random.randint(8, 15)
    if risk == "p3":
        return random.randint(16, 30)
    return random.randint(31, 80)


def _gen_sales_history(forecast_daily: float, days: int = 90) -> list[int]:
    """生成 90 天历史销量,围绕 forecast_daily 上下波动."""
    history: list[int] = []
    for i in range(days):
        # 加少量趋势(向下倾斜) + 噪声
        trend = 1.0 - (i / (days * 4))
        noise = random.uniform(0.7, 1.3)
        v = max(0, round(forecast_daily * trend * noise))
        history.append(v)
    return history


def _gen_fba_inventory(forecast_daily: float, target_days: int) -> tuple[int, int, int, int, int]:
    """
    根据目标 FBA 可售天数反推 (available, working, shipped, receiving, reserved).

    fba_sellable_days = (available + working + shipped + receiving) / forecast_daily
    所以 fba_total = target_days * forecast_daily
    分配比例:
      available 60% / shipped 20% / receiving 15% / working 5%
    reserved 单独额外 ~3-8%
    """
    fba_total = max(0, round(target_days * forecast_daily))
    available = round(fba_total * 0.60)
    shipped = round(fba_total * 0.20)
    receiving = round(fba_total * 0.15)
    working = fba_total - available - shipped - receiving  # 剩余给 working,可能 0
    working = max(0, working)
    reserved = round(fba_total * random.uniform(0.03, 0.08))
    return available, working, shipped, receiving, reserved


def _gen_local_inventory(forecast_daily: float, has_inbound: bool) -> tuple[int, int]:
    """生成本地实际 + 本地预计增量."""
    # local_actual:0-30 天日销量
    actual_days = random.randint(0, 30)
    local_actual = round(forecast_daily * actual_days)
    # local_plan(在途增量):有 50% 概率有,数量等于 5-15 天日销量
    if has_inbound and random.random() < 0.5:
        plan_days = random.randint(5, 15)
        local_plan = round(forecast_daily * plan_days)
    else:
        local_plan = 0
    return local_actual, local_plan


def _compute_derived(sku: SkuSeed) -> None:
    """计算派生字段(风险/可售天数/建议采购量等)."""
    fd = float(sku.forecast_daily)
    if fd <= 0:
        sku.fba_sellable_days = Decimal("0")
        sku.sellable_days = Decimal("0")
        sku.total_stock = 0
        return

    # FBA 总(不含 reserved)
    fba_total = (
        sku.fba_available
        + sku.fba_inbound_working
        + sku.fba_inbound_shipped
        + sku.fba_inbound_receiving
    )

    # 总库存
    sku.total_stock = fba_total + sku.local_actual + sku.local_plan

    # 可售天数
    sku.fba_sellable_days = Decimal(round(fba_total / fd, 2))
    sku.sellable_days = Decimal(round(sku.total_stock / fd, 2))

    # 风险等级(按 FBA 侧)
    fba_days = float(sku.fba_sellable_days)
    if fba_days <= 7:
        sku.risk_level = "p1"
    elif fba_days <= 15:
        sku.risk_level = "p2"
    elif fba_days <= 30:
        sku.risk_level = "p3"
    else:
        sku.risk_level = "safe"

    # 覆盖周期需求量
    sku.coverage_demand = Decimal(round(fd * DEFAULT_TOTAL_COVERAGE, 2))

    # 建议采购量(向上取整)
    diff = float(sku.coverage_demand) - sku.total_stock
    sku.suggest_qty = max(0, math.ceil(diff))

    # 预计断货日期(FBA 侧)
    sku.stockout_date = TODAY + timedelta(days=int(fba_days))
    # 建议采购时间(全链路)
    sku.suggest_purchase_date = sku.stockout_date - timedelta(days=DEFAULT_LEAD_TIME)


def generate_skus() -> list[SkuSeed]:
    """生成 48 个 SKU 完整种子数据."""
    risk_targets = _build_risk_targets()
    skus: list[SkuSeed] = []

    for i in range(TOTAL_SKUS):
        store = STORES[i % len(STORES)]
        owner = OWNERS[i % len(OWNERS)]
        product_name, category, brand = PRODUCTS[i % len(PRODUCTS)]
        risk = risk_targets[i]

        msku = _gen_msku(i)
        listing_id = 1000000 + i  # BIGINT, URL safe
        product_id = 600000 + i

        # forecast_daily:基础 5-50 件,与产品类型挂钩
        base_daily = [5, 8, 12, 18, 25, 32, 42, 55][i % 8]
        forecast_daily = float(base_daily) * random.uniform(0.85, 1.15)

        # 历史销量
        history = _gen_sales_history(forecast_daily)
        last_7 = history[-7:]
        last_7_avg = sum(last_7) / 7
        last_7_denoised = round(last_7_avg * 0.94, 2)

        # 库存
        target_fba_days = _pick_fba_sellable_days(risk)
        fba_avail, fba_working, fba_shipped, fba_receiving, fba_reserved = (
            _gen_fba_inventory(forecast_daily, target_fba_days)
        )
        local_actual, local_plan = _gen_local_inventory(
            forecast_daily, has_inbound=(risk in ("p1", "p2", "p3"))
        )

        # 价格 / 成本
        sale_price = round(8.99 + (i % 9) * 1.7, 2)
        unit_cost = round(sale_price * 0.42, 2)

        sku = SkuSeed(
            listing_id=listing_id,
            msku=msku,
            sku=_gen_sku(i, store["country_code"]),
            asin=_gen_asin(i),
            fnsku=_gen_fnsku(i),
            parent_asin=_gen_asin(i // 3),
            product_name=product_name,
            category=category,
            brand=brand,
            item_name=f"{brand} {product_name} - {store['country']}",
            image_url=_gen_image_url(i, msku),
            mall_id=store["mall_id"],
            mall_name=store["name"],
            country_code=store["country_code"],
            country=store["country"],
            currency=store["currency"],
            product_id=product_id,
            owner_user_id=owner["user_id"],
            owner_name=owner["name"],
            sale_price=Decimal(str(sale_price)),
            unit_cost=Decimal(str(unit_cost)),
            forecast_daily=Decimal(str(round(forecast_daily, 2))),
            last_7d_raw_daily=Decimal(str(round(last_7_avg, 2))),
            last_7d_denoised_daily=Decimal(str(last_7_denoised)),
            daily_sales_history=history,
            fba_available=fba_avail,
            fba_inbound_working=fba_working,
            fba_inbound_shipped=fba_shipped,
            fba_inbound_receiving=fba_receiving,
            fba_reserved=fba_reserved,
            local_actual=local_actual,
            local_plan=local_plan,
        )

        _compute_derived(sku)
        skus.append(sku)

    return skus


# ===== 汇率 =====
FX_RATES_TO_USD: dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "CAD": 0.74,
    "JPY": 0.0067,
}


def fx_rate_to_base(currency: str, base: str = "USD") -> float:
    """演示用静态汇率."""
    if base != "USD":
        return 1.0  # 简化:base 仅支持 USD
    return FX_RATES_TO_USD.get(currency, 1.0)
