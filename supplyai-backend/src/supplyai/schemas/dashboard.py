"""Dashboard 域 DTO."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from supplyai.schemas.common import SuggestTotalAmount

ActionHint = Literal["urgent_purchase", "follow_up", "review", "ok"]
Priority = Literal["p1", "p2", "p3", "safe"]


class DashboardSnapshotRequest(BaseModel):
    """工作台聚合请求."""

    tenant_id: int
    calc_run_id: str | None = None  # 不传 = latest
    mall_ids: list[int] | None = None
    country_codes: list[str] | None = None
    owners: list[str] | None = None


class RiskCounts(BaseModel):
    """风险等级分布."""

    p1: int = 0
    p2: int = 0
    p3: int = 0
    safe: int = 0


class StockoutTrendPoint(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class DashboardSnapshotDTO(BaseModel):
    """工作台聚合响应 — 对应前端 ViewModel: DashboardSnapshot."""

    model_config = ConfigDict(from_attributes=True)

    calc_run_id: str
    as_of: datetime
    risk_counts: RiskCounts
    stockout_7_count: int
    total_sales_7d: int  # 近 7 天总销量(各 SKU sales_7d 求和)
    total_stock: int  # 总库存(各 SKU total_stock 求和)
    suggest_sku_count: int
    suggest_total_qty: int
    suggest_total_amount: SuggestTotalAmount
    stockout_trend: list[StockoutTrendPoint] = Field(default_factory=list)


class RiskQueueRequest(BaseModel):
    """风险队列请求 — 工作台右侧"今日动作"面板."""

    tenant_id: int
    calc_run_id: str | None = None
    priorities: list[Priority] | None = None  # 默认全部,按 p1>p2>p3>safe 排序
    mall_ids: list[int] | None = None
    country_codes: list[str] | None = None
    limit: int = 10


class RiskQueueRow(BaseModel):
    """风险队列单行 — 精简 SKU 信息 + 行动提示."""

    listing_id: int | None
    mall_id: int | None
    msku: str
    sku: str | None
    asin: str | None
    product_name: str | None
    store_name: str | None
    country_code: str | None
    priority: Priority
    fba_sellable_days: float | None
    stockout_date: date | None
    suggest_qty: int
    suggest_amount_base: float | None
    base_currency: str | None
    action_hint: ActionHint
    calc_run_id: str


class RiskQueueDTO(BaseModel):
    """风险队列响应."""

    calc_run_id: str
    as_of: datetime
    total: int  # 队列内总匹配数(可能 > limit)
    rows: list[RiskQueueRow] = Field(default_factory=list)


class FilterOption(BaseModel):
    """过滤器单选项 — 用于前端 dropdown / chip."""

    value: str  # mall_id / country_code / owner 唯一值
    label: str  # 用户可见文案
    count: int  # 匹配的 SKU 数


class FiltersRequest(BaseModel):
    tenant_id: int
    calc_run_id: str | None = None


class FiltersDTO(BaseModel):
    """工作台顶部过滤器选项."""

    stores: list[FilterOption] = Field(default_factory=list)
    countries: list[FilterOption] = Field(default_factory=list)
    owners: list[FilterOption] = Field(default_factory=list)
    brands: list[FilterOption] = Field(default_factory=list)
    categories: list[FilterOption] = Field(default_factory=list)


class StoreSummaryRow(BaseModel):
    """单个店铺的风险摘要 — 侧栏"店铺空间"渲染用."""

    mall_id: int
    mall_name: str
    country_code: str | None
    sku_count: int
    p1_count: int
    p2_count: int
    p3_count: int
    safe_count: int


class StoresRequest(BaseModel):
    tenant_id: int
    calc_run_id: str | None = None


class StoresDTO(BaseModel):
    rows: list[StoreSummaryRow] = Field(default_factory=list)


class FinanceMetric(BaseModel):
    """单个财务指标 + 同比."""

    value: float
    pct_change: float | None = None


class FinanceRequest(BaseModel):
    tenant_id: int
    as_of_date: date | None = None
    mall_ids: list[int] | None = None
    country_codes: list[str] | None = None


class FinanceDTO(BaseModel):
    """昨日财务摘要 — 派生自 rl_amz_sales_daily_report + lps.unit_cost.

    Phase 1: cost/expense/profit 用启发式公式
       cost    = sum(qty * lps.unit_cost)
       expense = gmv * 0.51 (平台费 + 广告 + 物流)
       profit  = gmv - cost - expense
    Phase 2 上线 mk_finance_daily_stat 后改读派生表。
    """

    as_of_date: str  # YYYY-MM-DD
    currency: str = "USD"
    sales: FinanceMetric  # 销量(件)
    gmv: FinanceMetric  # 收入($)
    cost: FinanceMetric  # 成本($)
    expense: FinanceMetric
    profit: FinanceMetric


class DataQualityAlert(BaseModel):
    """单条数据质量告警."""

    id: str
    kind: Literal["forecast", "rule", "review", "data_quality"]
    title: str
    count: int
    action: str | None = None


class AlertsRequest(BaseModel):
    tenant_id: int
    calc_run_id: str | None = None


class AlertsDTO(BaseModel):
    alerts: list[DataQualityAlert] = Field(default_factory=list)


class HolidayItem(BaseModel):
    """节日项 — 前端 SKU 详情节日色带 + Calc Engine 节日乘数."""

    id: str
    name: str
    peak_date: str  # YYYY-MM-DD
    days_before: int
    days_after: int
    sales_multiplier: float
    color: str | None = None
    flag: str | None = None
    country_code: str | None = None


class HolidaysRequest(BaseModel):
    tenant_id: int
    country_code: str | None = None  # 可按国家过滤


class HolidaysDTO(BaseModel):
    holidays: list[HolidayItem] = Field(default_factory=list)


class HolidayUpsertRequest(BaseModel):
    """节日 upsert — 节日色带拖动 / 改系数时持久化."""

    tenant_id: int
    holiday_id: str  # 客户端用稳定 id(如 'mothers' / 'memorial');不存在则新建
    name: str
    peak_date: date
    days_before: int = 0
    days_after: int = 0
    sales_multiplier: float = 1.0
    color: str | None = None
    flag: str | None = None
    country_code: str | None = None
    enabled: bool = True
