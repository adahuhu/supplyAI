"""补充缺失数据脚本 - 扩展销售/财务/库存补货等各表到最新日期."""
import sqlite3
import random
import math
from datetime import date, timedelta, datetime

DB_PATH = "data/supplyai.db"
TENANT_ID = 100228
TODAY = date(2026, 5, 19)
CALC_RUN_ID = f"RUN-20260519080000-{TENANT_ID}-seed01"

random.seed(42)


def d(offset: int) -> str:
    return (TODAY + timedelta(days=offset)).isoformat()


def jitter(val, pct=0.08):
    return max(0, val * (1 + random.uniform(-pct, pct)))


conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ── 1. 获取所有 listing 基础数据 ──────────────────────────────
cur.execute("""
    SELECT s.listing_id, s.mall_id, s.msku, s.fnsku, s.sku, s.asin,
           s.country_code, s.risk_level, s.suggest_purchase, s.suggest_qty,
           s.forecast_daily, s.fba_available, s.fba_inbound_working,
           s.fba_inbound_shipped, s.fba_inbound_receiving, s.fba_reserved,
           s.local_actual, s.total_stock, s.sellable_days, s.fba_sellable_days,
           s.safety_days, s.lead_time_days, s.unit_cost, s.currency,
           s.product_name, s.yesterday_sales, s.sales_7d, s.sales_30d,
           s.yesterday_revenue, s.revenue_7d, s.gross_profit_7d, s.gross_margin,
           s.cost_7d, s.expense_7d, s.stockout_date, s.last_7d_raw_daily,
           s.last_7d_denoised_daily
    FROM mk_supply_sku_daily_stat s
    WHERE s.stat_date = '2026-05-18'
    AND s.calc_run_id = (
        SELECT calc_run_id FROM mk_supply_sku_daily_stat
        WHERE stat_date = '2026-05-18' ORDER BY rowid DESC LIMIT 1
    )
    GROUP BY s.listing_id
    ORDER BY s.listing_id
""")
listings = cur.fetchall()
print(f"加载 {len(listings)} 条 listing 数据")

MALL_CURRENCY = {1001: 'USD', 1002: 'EUR', 1003: 'GBP', 1004: 'JPY', 1005: 'CAD', 1006: 'EUR'}
MALL_FX = {1001: 1.0, 1002: 1.08, 1003: 1.27, 1004: 0.0067, 1005: 0.74, 1006: 1.08}

# ── 2. 扩展 rl_amz_sales_daily_report (2026-05-09 → 2026-05-19) ────────────
cur.execute("SELECT MAX(year_month_day) FROM rl_amz_sales_daily_report")
max_sales_date = date.fromisoformat(cur.fetchone()[0])
print(f"销售报表现有最新日期: {max_sales_date}")

# 获取每个 listing 在已有数据中的基础日销
cur.execute("""
    SELECT mall_id, msku, listing_id, asin, country_code, country,
           currency_code, item_name, image_url, image_url_px75,
           AVG(sales_volume) as avg_qty, AVG(sales) as avg_sales,
           AVG(order_quantity) as avg_orders
    FROM rl_amz_sales_daily_report
    GROUP BY listing_id
""")
sales_base = {r[2]: r for r in cur.fetchall()}

sales_rows = []
for listing_id, mall_id, msku, fnsku, sku, asin, country_code, risk_level, \
        suggest_purchase, suggest_qty, forecast_daily, fba_available, \
        fba_inbound_working, fba_inbound_shipped, fba_inbound_receiving, \
        fba_reserved, local_actual, total_stock, sellable_days, fba_sellable_days, \
        safety_days, lead_time_days, unit_cost, currency, product_name, \
        yesterday_sales, sales_7d, sales_30d, yesterday_revenue, revenue_7d, \
        gross_profit_7d, gross_margin, cost_7d, expense_7d, stockout_date, \
        last_7d_raw_daily, last_7d_denoised_daily in listings:

    base = sales_base.get(listing_id)
    avg_qty = base[10] if base else (forecast_daily or 5)
    avg_sales = base[11] if base else (avg_qty * 8.5)
    avg_orders = base[12] if base else max(1, avg_qty * 0.7)
    item_name = base[7] if base else (product_name or msku)
    image_url = base[8] if base else f"https://placehold.co/96x96/e2e8f0/64748b?text={msku[-3:]}"
    image_url_px75 = base[9] if base else image_url
    cur_code = MALL_CURRENCY.get(mall_id, 'USD')

    fill_start = max_sales_date + timedelta(days=1)
    fill_end = TODAY
    dt = fill_start
    while dt <= fill_end:
        qty = max(0, round(jitter(avg_qty, 0.15)))
        sales_rows.append((
            TENANT_ID, mall_id, msku, dt.isoformat(), listing_id,
            asin, asin, None, cur_code, item_name,
            image_url, image_url_px75,
            qty, round(qty * avg_sales / max(avg_qty, 0.01), 2),
            max(0, round(jitter(avg_orders, 0.15))),
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        dt += timedelta(days=1)

if sales_rows:
    cur.executemany("""
        INSERT OR IGNORE INTO rl_amz_sales_daily_report
        (tenant_id, mall_id, msku, year_month_day, listing_id, asin, parent_asin,
         country, currency_code, item_name, image_url, image_url_px75,
         sales_volume, sales, order_quantity, created_time, update_time)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, sales_rows)
    print(f"插入销售数据: {len(sales_rows)} 条")

# ── 3. 扩展 rl_amz_finances_profit_mall_100228 ──────────────────
cur.execute("SELECT MAX(settlement_date) FROM rl_amz_finances_profit_mall_100228")
max_fin_date = date.fromisoformat(cur.fetchone()[0])
print(f"财务数据现有最新日期: {max_fin_date}")

cur.execute("""
    SELECT mall_id, AVG(sp_ads_fee), AVG(sb_ads_fee), AVG(sd_ads_fee),
           AVG(month_storage_fee), AVG(fba_storage_fee), AVG(fba_long_storage_fee),
           AVG(fba_sales), AVG(fbm_sales), AVG(commission), AVG(fba_commission),
           AVG(fbm_commission), AVG(fba_shipment_fee)
    FROM rl_amz_finances_profit_mall_100228
    GROUP BY mall_id
""")
fin_base = {r[0]: r for r in cur.fetchall()}

fin_rows = []
for mall_id in [1001, 1002, 1003, 1004, 1005, 1006]:
    base = fin_base.get(mall_id)
    if not base:
        continue
    cur_code = MALL_CURRENCY.get(mall_id, 'USD')
    dt = max_fin_date + timedelta(days=1)
    while dt <= TODAY:
        fin_rows.append((
            TENANT_ID, mall_id, dt.isoformat(), cur_code,
            round(jitter(base[1], 0.12), 2),
            round(jitter(base[2], 0.12), 2),
            0,
            round(jitter(base[4], 0.12), 2),
            0, 0,
            round(jitter(base[6], 0.10), 2),
            round(jitter(base[7], 0.10), 2),
            round(jitter(base[8] or 0, 0.10), 2),
            round(jitter(base[9], 0.06), 2),
            round(jitter(base[10], 0.06), 2),
            round(jitter(base[11] or 0, 0.06), 2),
            round(jitter(base[7] or 0, 0.08), 2),
            round(jitter(base[12], 0.08), 2),
            datetime.now().isoformat(), datetime.now().isoformat()
        ))
        dt += timedelta(days=1)

if fin_rows:
    cur.executemany("""
        INSERT OR IGNORE INTO rl_amz_finances_profit_mall_100228
        (tenant_id, mall_id, settlement_date, currency_code,
         sp_ads_fee, sb_ads_fee, sbv_ads_fee, ads_fee_share, sd_ads_fee,
         product_ads_payment, fba_long_storage_fee, fba_sales, fbm_sales,
         commission, fba_commission, fbm_commission,
         permanent_storage_fee, fba_shipment_fee,
         created_time, update_time)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, fin_rows)
    print(f"插入财务数据: {len(fin_rows)} 条")

# ── 4. 新增 calc_run for 2026-05-19 ────────────────────────────
cur.execute("SELECT COUNT(*) FROM mk_calc_run WHERE calc_run_id = ?", (CALC_RUN_ID,))
if cur.fetchone()[0] == 0:
    cur.execute("""
        INSERT INTO mk_calc_run
        (calc_run_id, tenant_id, stat_date, run_type, run_at, rule_version, status, source_type)
        VALUES (?, ?, '2026-05-19', 'scheduled', ?, 'v1', 'success', 'derived')
    """, (CALC_RUN_ID, TENANT_ID, datetime.now().isoformat()))
    print(f"插入 calc_run: {CALC_RUN_ID}")

# ── 5. 新增 mk_supply_sku_daily_stat for 2026-05-19 ────────────
cur.execute("SELECT COUNT(*) FROM mk_supply_sku_daily_stat WHERE stat_date = '2026-05-19' AND calc_run_id = ?", (CALC_RUN_ID,))
if cur.fetchone()[0] == 0:
    stat_rows = []
    for i, (listing_id, mall_id, msku, fnsku, sku, asin, country_code, risk_level,
            suggest_purchase, suggest_qty, forecast_daily, fba_available,
            fba_inbound_working, fba_inbound_shipped, fba_inbound_receiving,
            fba_reserved, local_actual, total_stock, sellable_days, fba_sellable_days,
            safety_days, lead_time_days, unit_cost, currency, product_name,
            yesterday_sales, sales_7d, sales_30d, yesterday_revenue, revenue_7d,
            gross_profit_7d, gross_margin, cost_7d, expense_7d, stockout_date,
            last_7d_raw_daily, last_7d_denoised_daily) in enumerate(listings):

        cur_code = MALL_CURRENCY.get(mall_id, 'USD')
        fx = MALL_FX.get(mall_id, 1.0)
        fd = forecast_daily or 5.0
        yest_sales = max(0, round(jitter(fd, 0.12)))
        unit_price = (yesterday_revenue or 0) / max(yesterday_sales or 1, 1) if (yesterday_revenue or 0) > 0 else 8.5
        yest_rev = round(yest_sales * unit_price, 2)
        new_sellable = round(jitter(sellable_days or 30, 0.05), 2)
        new_fba_sell = round(jitter(fba_sellable_days or 15, 0.05), 2)
        sq = suggest_qty or 0
        sa = round(sq * (unit_cost or 4.5), 2)
        sa_base = round(sa * fx, 2)

        stat_rows.append((
            CALC_RUN_ID, TENANT_ID, '2026-05-19',
            listing_id, mall_id, country_code, msku, fnsku, sku, asin,
            product_name, 'ACTIVE', 'FBA', risk_level,
            yest_sales, yest_rev,
            round(jitter(revenue_7d or 0, 0.06), 2),
            round(jitter(expense_7d or 0, 0.06), 2),
            round(jitter(cost_7d or 0, 0.06), 2),
            round(jitter(gross_profit_7d or 0, 0.06), 2),
            round(gross_margin or 0.07, 4), 'allocated',
            sales_7d or 0, sales_30d or 0,
            round(sales_30d * 2 if sales_30d else 0),
            round(sales_30d * 3 if sales_30d else 0),
            round(fd, 2), 'default',
            round(fd * (safety_days or 14), 2),
            round(jitter(last_7d_raw_daily or fd, 0.05), 2),
            round(jitter(last_7d_denoised_daily or fd, 0.05), 2),
            fba_available or 0, fba_inbound_working or 0,
            fba_inbound_shipped or 0, fba_inbound_receiving or 0,
            fba_reserved or 0, local_actual or 0, 0,
            (fba_available or 0) + (local_actual or 0),
            round(new_sellable, 2), round(new_fba_sell, 2),
            round(new_sellable - new_fba_sell, 2),
            safety_days or 14,
            stockout_date,
            lead_time_days or 30,
            suggest_purchase or 0, sq,
            d(-12),  # suggest_purchase_date
            unit_cost or 4.5, cur_code, 'USD', fx,
            datetime.now().isoformat(),
            sa, sa_base,
            datetime.now().isoformat(), 'derived'
        ))

    cur.executemany("""
        INSERT INTO mk_supply_sku_daily_stat
        (calc_run_id, tenant_id, stat_date,
         listing_id, mall_id, country_code, msku, fnsku, sku, asin,
         product_name, listing_status, delivery_method, risk_level,
         yesterday_sales, yesterday_revenue,
         revenue_7d, expense_7d, cost_7d, gross_profit_7d,
         gross_margin, financial_estimate_type,
         sales_7d, sales_30d, sales_60d, sales_90d,
         forecast_daily, forecast_source, coverage_demand,
         last_7d_raw_daily, last_7d_denoised_daily,
         fba_available, fba_inbound_working, fba_inbound_shipped,
         fba_inbound_receiving, fba_reserved, local_actual, local_plan,
         total_stock, sellable_days, fba_sellable_days, local_sellable_days,
         safety_days, stockout_date, lead_time_days,
         suggest_purchase, suggest_qty, suggest_purchase_date,
         unit_cost, currency, base_currency, fx_rate_to_base, fx_rate_as_of,
         suggest_amount, suggest_amount_base,
         updated_at, source_type)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, stat_rows)
    print(f"插入 sku_daily_stat (2026-05-19): {len(stat_rows)} 条")

# ── 6. 补充 mk_sku_inbound_detail ─────────────────────────────
cur.execute("SELECT DISTINCT msku FROM mk_sku_inbound_detail")
existing_inbound_msks = {r[0] for r in cur.fetchall()}

inbound_rows = []
inbound_id_counter = 1000
for listing_id, mall_id, msku, fnsku, sku, asin, country_code, risk_level, \
        suggest_purchase, suggest_qty, forecast_daily, fba_available, \
        fba_inbound_working, fba_inbound_shipped, fba_inbound_receiving, \
        *rest in listings:

    fd = forecast_daily or 5.0
    base_qty = max(30, round(fd * 30))

    # 每个 SKU 确保有 3 条入库记录（不同状态和到货日期）
    existing_for_msku = []
    cur.execute("SELECT inbound_status, expected_arrival_date FROM mk_sku_inbound_detail WHERE msku = ? AND mall_id = ?", (msku, mall_id))
    existing_for_msku = [(r[0], r[1]) for r in cur.fetchall()]
    existing_statuses = {r[0] for r in existing_for_msku}

    records = [
        ('in_transit', d(5),  round(jitter(base_qty * 0.5, 0.2)), 'sea'),
        ('pending',    d(18), round(jitter(base_qty * 0.8, 0.2)), 'sea_express'),
        ('pending',    d(35), round(jitter(base_qty, 0.2)),        'sea'),
    ]
    for status, arr_date, qty, ltype in records:
        # 不重复插入同一状态+到货日期
        if (status, arr_date) in existing_for_msku:
            continue
        inbound_id_counter += 1
        inbound_rows.append((
            f"INB-{msku}-{inbound_id_counter:04d}",
            TENANT_ID, mall_id, msku, sku,
            'purchase', status, max(10, qty), arr_date,
            f"PO-{msku}-{inbound_id_counter}", 'mock', ltype
        ))

if inbound_rows:
    cur.executemany("""
        INSERT OR IGNORE INTO mk_sku_inbound_detail
        (inbound_id, tenant_id, mall_id, msku, sku,
         inbound_type, inbound_status, qty, expected_arrival_date,
         source_order_no, source_type, logistics_type)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, inbound_rows)
    print(f"插入入库记录: {len(inbound_rows)} 条")

# ── 7. 补充 mk_purchase_draft ──────────────────────────────────
cur.execute("SELECT COUNT(*) FROM mk_purchase_draft")
if cur.fetchone()[0] == 0:
    draft_rows = []
    suppliers = ['东莞市宏瑞达供应商', '深圳科技元器件有限公司', '广州跨境贸易商行',
                 '义乌精品贸易中心', '上海外贸直供工厂']
    for listing_id, mall_id, msku, fnsku, sku, asin, country_code, risk_level, \
            suggest_purchase, suggest_qty, forecast_daily, *rest in listings:
        if not suggest_purchase or not suggest_qty:
            continue
        draft_rows.append((
            f"DRAFT-{msku}-{mall_id}",
            CALC_RUN_ID, TENANT_ID, mall_id, msku, sku,
            suggest_qty,
            random.choice(suppliers),
            'pending',
            'system',
            datetime.now().isoformat(),
            'derived'
        ))
    if draft_rows:
        cur.executemany("""
            INSERT OR IGNORE INTO mk_purchase_draft
            (draft_id, calc_run_id, tenant_id, mall_id, msku, sku,
             suggest_qty, supplier_name, status, created_by, created_at, source_type)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, draft_rows)
        print(f"插入采购草稿: {len(draft_rows)} 条")

# ── 8. 补充 mk_rule_logistics_method（为现有 SKU 级规则补物流方式）──
cur.execute("SELECT rule_id FROM mk_replenishment_rule WHERE scope_type != 'global'")
sku_rules = [r[0] for r in cur.fetchall()]
lm_rows = []
for rule_id in sku_rules:
    cur.execute("SELECT COUNT(*) FROM mk_rule_logistics_method WHERE rule_id = ?", (rule_id,))
    if cur.fetchone()[0] == 0:
        lm_rows += [
            (rule_id, 'sea', 35, 1, 'seed'),
            (rule_id, 'air', 8, 1, 'seed'),
        ]
if lm_rows:
    cur.executemany("""
        INSERT OR IGNORE INTO mk_rule_logistics_method
        (rule_id, logistics_mode, logistics_days, is_active, source_type)
        VALUES (?,?,?,?,?)
    """, lm_rows)
    print(f"插入物流方式: {len(lm_rows)} 条")

# ── 9. 补充 mk_stockout_event ─────────────────────────────────
cur.execute("SELECT DISTINCT msku FROM mk_stockout_event")
existing_events = {r[0] for r in cur.fetchall()}
event_rows = []
p1_listings = [(l[2], l[1]) for l in listings if l[7] == 'p1']
for msku, mall_id in p1_listings[:8]:
    if msku in existing_events:
        continue
    start = TODAY - timedelta(days=random.randint(3, 20))
    end = start + timedelta(days=random.randint(2, 10))
    event_rows.append((
        f"EVT-{msku}-{mall_id}",
        TENANT_ID, mall_id, msku,
        start.isoformat(), end.isoformat(),
        (end - start).days, 'resolved', 'seed'
    ))
if event_rows:
    cur.executemany("""
        INSERT OR IGNORE INTO mk_stockout_event
        (event_id, tenant_id, mall_id, msku, start_at, end_at,
         duration_days, event_status, source_type)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, event_rows)
    print(f"插入断货事件: {len(event_rows)} 条")

conn.commit()
conn.close()
print("\n✅ 数据补充完成！")
