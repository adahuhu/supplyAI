# SupplyAI 字段映射表 v2

更新时间：2026-05-09

本文定义前端 ViewModel 与项目内数据库表字段的映射。原则：

- 前端组件只消费 ViewModel，不直接消费 `rl_*` / `mk_*` 原始字段。
- API 可以返回 snake_case DTO；前端 Adapter 统一转为 camelCase ViewModel。
- 所有补货结论型字段优先来自 `mk_supply_sku_daily_stat`，并以同一个 `calc_run_id` 保证一致。
- `rl_*` 只作为真实源数据补充和溯源，不在组件层直接 join。

## 1. 关键枚举

| 业务字段 | DB 值 | ViewModel 值 | 展示值 |
|-|-|-|-|
| 风险等级 | `p1` / `p2` / `p3` / `safe` | `priority` | P1 / P2 / P3 / 安全 |
| 履约方式 | `FBA` / `FBM` | `deliveryMethod` | FBA / FBM |
| 财务估算类型 | `allocated` / `actual` / `hidden` | `financialEstimateType` | 分摊估算 / 真实 / 隐藏 |
| 预测来源 | `fixed` / `dynamic` / `default` / `denoised` / `raw` | `forecastSource` | 固定 / 动态 / 默认 / 去噪 / 原始 |

## 2. `SkuSummary`

用于备货计划列表、Dashboard 风险队列、全局 AI 风险摘要。

| ViewModel 字段 | 类型 | DB 来源 | 说明 |
|-|-|-|-|
| `id` | string | `mk_supply_sku_daily_stat.listing_id` | 路由主键，前端按 string。 |
| `calcRunId` | string | `mk_supply_sku_daily_stat.calc_run_id` | 计算批次。 |
| `tenantId` | string | `mk_supply_sku_daily_stat.tenant_id` | 租户。 |
| `mallId` | string | `mk_supply_sku_daily_stat.mall_id` | 店铺 ID。 |
| `storeName` | string | `rl_mall.mall_name` | 店铺展示名。 |
| `countryCode` | string | `mk_supply_sku_daily_stat.country_code` | 国家筛选。 |
| `msku` | string | `mk_supply_sku_daily_stat.msku` | MSKU。 |
| `sku` | string | `mk_supply_sku_daily_stat.sku` | ERP SKU。 |
| `asin` | string | `mk_supply_sku_daily_stat.asin` | ASIN。 |
| `fnsku` | string | `mk_supply_sku_daily_stat.fnsku` | FNSKU。 |
| `name` | string | `mk_supply_sku_daily_stat.product_name` | 品名，来自 `mk_listing_product_sources.product_name`。 |
| `title` | string | `mk_listing_product_sources.title` | Listing 标题。 |
| `image` | string | `mk_listing_product_sources.image_url` | 商品图片。 |
| `brand` | string | `mk_listing_product_sources.brand` | 品牌。 |
| `category` | string | `mk_listing_product_sources.category` | 分类。 |
| `owner` | string | `mk_listing_product_sources.owner` | 负责人。 |
| `deliveryMethod` | string | `mk_supply_sku_daily_stat.delivery_method` | Phase 1 列表仅返回 FBA。 |
| `status` | string | `mk_supply_sku_daily_stat.listing_status` | Listing 状态。 |
| `priority` | string | `mk_supply_sku_daily_stat.risk_level` | DB 全小写，前端展示映射为 P1/P2/P3/安全。 |
| `yesterdaySales` | number | `mk_supply_sku_daily_stat.yesterday_sales` | 昨日销量。 |
| `futureDaily` | number | `mk_supply_sku_daily_stat.forecast_daily` | 最终未来平均日销。 |
| `forecastSource` | string | `mk_supply_sku_daily_stat.forecast_source` | 预测来源。 |
| `coverageDemand` | number | `mk_supply_sku_daily_stat.coverage_demand` | 覆盖周期需求量。 |
| `sellable` | number | `mk_supply_sku_daily_stat.sellable_days` | 主表展示，总库存可售天数。 |
| `fbaSellable` | number | `mk_supply_sku_daily_stat.fba_sellable_days` | 风险和预计断货用。 |
| `localSellable` | number | `mk_supply_sku_daily_stat.local_sellable_days` | hover 子项。 |
| `stockoutDate` | string | `mk_supply_sku_daily_stat.stockout_date` | 预计断货日期，FBA 侧口径。 |
| `purchaseDate` | string | `mk_supply_sku_daily_stat.suggest_purchase_date` | 建议采购时间，全链路口径。 |
| `suggest` | boolean | `mk_supply_sku_daily_stat.suggest_purchase` | 是否建议采购。 |
| `suggestQty` | number | `mk_supply_sku_daily_stat.suggest_qty` | 已向上取整。 |
| `suggestAmountBase` | number | `mk_supply_sku_daily_stat.suggest_amount_base` | 基准币种预计采购金额。 |
| `baseCurrency` | string | `mk_supply_sku_daily_stat.base_currency` | Phase 1 默认 USD。 |
| `lastUpdated` | string | `mk_supply_sku_daily_stat.updated_at` | 快照更新时间。 |

## 3. `StockBreakdown`

用于列表 hover、SKU 详情库存卡、AI 解释。

| ViewModel 字段 | 类型 | DB 来源 | 说明 |
|-|-|-|-|
| `totalStock` | number | `mk_supply_sku_daily_stat.total_stock` | 不含 `fba_reserved`。 |
| `fbaAvailable` | number | `mk_supply_sku_daily_stat.fba_available` | FBA 可售。 |
| `fbaInboundWorking` | number | `mk_supply_sku_daily_stat.fba_inbound_working` | FBA 计划入库。 |
| `fbaInboundShipped` | number | `mk_supply_sku_daily_stat.fba_inbound_shipped` | FBA 标发在途。 |
| `fbaInboundReceiving` | number | `mk_supply_sku_daily_stat.fba_inbound_receiving` | FBA 入库中。 |
| `fbaReserved` | number | `mk_supply_sku_daily_stat.fba_reserved` | 仅展示，不参与总库存和风险计算。 |
| `localActual` | number | `mk_supply_sku_daily_stat.local_actual` | 本地实际。 |
| `localPlan` | number | `mk_supply_sku_daily_stat.local_plan` | 本地未来可用增量，不含 `localActual`。 |

公式：

```text
totalStock = fbaAvailable
           + fbaInboundWorking
           + fbaInboundShipped
           + fbaInboundReceiving
           + localActual
           + localPlan
```

## 4. `SkuDetail`

用于 SKU 分析详情页。

| ViewModel 字段 | 类型 | DB 来源 | 说明 |
|-|-|-|-|
| `summary` | `SkuSummary` | `mk_supply_sku_daily_stat` + `mk_listing_product_sources` | 详情头部。 |
| `stock` | `StockBreakdown` | `mk_supply_sku_daily_stat` | 库存构成。 |
| `last7Daily` | number | `mk_supply_sku_daily_stat.last_7d_raw_daily` | 近 7 天原始日销。 |
| `last7Denoised` | number | `mk_supply_sku_daily_stat.last_7d_denoised_daily` | 近 7 天去噪日销。 |
| `revenue7` | number | `mk_supply_sku_daily_stat.revenue_7d` | 近 7 天收入。 |
| `expense7` | number | `mk_supply_sku_daily_stat.expense_7d` | SKU 级分摊估算或隐藏。 |
| `cost7` | number | `mk_supply_sku_daily_stat.cost_7d` | 成本。 |
| `grossProfit7` | number | `mk_supply_sku_daily_stat.gross_profit_7d` | 毛利。 |
| `grossMargin` | number | `mk_supply_sku_daily_stat.gross_margin` | 毛利率。 |
| `financialEstimateType` | string | `mk_supply_sku_daily_stat.financial_estimate_type` | 影响页面是否显示估算提示。 |
| `rules` | object | `mk_replenishment_rule` + `mk_forecast_rule` | 当前生效规则。 |
| `inboundDetails` | array | `mk_sku_inbound_detail` | 本地/采购在途解释。 |

FBM 兜底：

- 如果 URL 命中 `mk_listing_product_sources.delivery_method = 'FBM'`，详情页可展示基础信息，但不展示备货风险、预计断货和采购建议。
- 页面状态文案使用“暂不支持 FBM 备货分析”。

## 5. `SalesTrendPoint`

用于 SKU 销量趋势图的历史段。

| ViewModel 字段 | 类型 | DB 来源 | 说明 |
|-|-|-|-|
| `date` | string | `rl_amz_sales_daily_report.year_month_day` | 历史口径不包含今天。 |
| `salesQty` | number | `SUM(rl_amz_sales_daily_report.sales_volume)` | 日销量。 |
| `revenue` | number | `SUM(rl_amz_sales_daily_report.sales)` | 日收入。 |
| `orderQty` | number | `SUM(rl_amz_sales_daily_report.order_quantity)` | 日订单数。 |
| `sourceType` | string | constant `actual` | 真实来源。 |

## 6. `ForecastTrendPoint`

用于 SKU 销量趋势图的未来段。

| ViewModel 字段 | 类型 | DB 来源 | 说明 |
|-|-|-|-|
| `date` | string | `mk_sku_forecast_daily.forecast_date` | 未来口径包含今天。 |
| `dayOffset` | number | `mk_sku_forecast_daily.day_offset` | D0/D1。 |
| `forecastQty` | number | `mk_sku_forecast_daily.forecast_qty` | 保留小数参与计算，展示可取整。 |
| `forecastSource` | string | `mk_sku_forecast_daily.forecast_source` | 来源。 |
| `salesMultiplier` | number | `mk_sku_forecast_daily.sales_multiplier` | 用户调整系数。 |
| `isAdjusted` | boolean | `mk_sku_forecast_daily.is_adjusted` | 是否调整。 |

一致性：

- `AVG(forecastQty)` 必须与 `SkuSummary.futureDaily` 在 `0.01` 误差内一致。
- `forecastQty` 和 `SkuSummary.futureDaily` 必须属于同一 `calcRunId`。

## 7. `DashboardSnapshot`

| ViewModel 字段 | 类型 | DB 来源 | 说明 |
|-|-|-|-|
| `calcRunId` | string | latest `mk_calc_run.calc_run_id` | 最新成功批次。 |
| `riskCounts` | object | `COUNT(*) FROM mk_supply_sku_daily_stat GROUP BY risk_level` | 风险分布。 |
| `stockout7Count` | number | `COUNT(*) WHERE fba_sellable_days <= 7` | 近 7 天断货风险。 |
| `suggestSkuCount` | number | `COUNT(*) WHERE suggest_purchase = 1` | 建议采购 SKU 数。 |
| `suggestTotalQty` | number | `SUM(suggest_qty)` | 建议采购件数。 |
| `suggestTotalAmountBase` | number | `SUM(suggest_amount_base)` | 基准币种采购金额。 |
| `byCurrency` | object | `SUM(suggest_amount) GROUP BY currency` | 多币种 hover 明细。 |
| `stockoutTrend` | array | `mk_stockout_event` | 断货趋势。 |
| `feeSummary` | object | `rl_amz_finances_profit_mall_100228` | 店铺级广告费/仓储费/费用。 |

## 8. Adapter 规则

| DTO 字段 | ViewModel 字段 | 规则 |
|-|-|-|
| `risk_level` | `priority` | 保持小写值，展示层映射文案。 |
| `listing_id` | `id` | 转 string。 |
| `mall_id` / `tenant_id` | `mallId` / `tenantId` | 转 string。 |
| `suggest_purchase` | `suggest` | `1 -> true`，`0 -> false`。 |
| `updated_at` | `lastUpdated` | ISO string。 |
| nullable 数值 | number/null | 不默认填 0；展示层用 `-`。 |

