"""SKU 域 DTO."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from supplyai.schemas.common import DataQuality

Priority = Literal["p1", "p2", "p3", "safe"]
DeliveryMethod = Literal["FBA", "FBM"]
FinancialEstimateType = Literal["allocated", "actual", "hidden"]


class SkuListRequest(BaseModel):
    """备货列表查询请求."""

    tenant_id: int
    calc_run_id: str | None = None  # 不传 = latest
    # 筛选
    priorities: list[Priority] | None = None
    mall_ids: list[int] | None = None
    country_codes: list[str] | None = None
    keyword: str | None = None  # 模糊搜索 msku/sku/asin/product_name
    suggest_only: bool = False  # 仅显示建议采购
    stockout_within_days: int | None = None  # 7 天内断货
    # 分页
    page: int = 1
    page_size: int = 50
    # 排序: "priority" | "stockout_date" | "fba_sellable_days" | "last_updated"
    sort_by: str = "priority"
    sort_desc: bool = False


class SkuSummaryDTO(BaseModel):
    """对应前端 ViewModel: SkuSummary(field-mapping-v2 §2)."""

    model_config = ConfigDict(from_attributes=True)

    # 标识
    id: int  # = listing_id
    calc_run_id: str
    tenant_id: int
    listing_id: int
    mall_id: int | None
    msku: str
    sku: str | None
    asin: str | None
    fnsku: str | None
    product_name: str | None
    image_url: str | None = None  # 详情页用 mk_listing_product_sources 补
    brand: str | None = None
    category: str | None = None
    owner: str | None = None
    store_name: str | None = None
    country_code: str | None
    delivery_method: DeliveryMethod | None
    listing_status: str | None
    # 风险与销量
    priority: Priority
    yesterday_sales: int | None
    sales_7d: int | None = None  # 过去 7 天累计
    recent_7d: list[int] = Field(default_factory=list)  # 过去 7 天每天销量 [D-6 ... D-0]
    future_daily: float | None
    forecast_source: str | None
    coverage_demand: float | None
    # 库存与时效
    total_stock: int | None
    fba_available: int | None
    fba_inbound: int | None  # = working + shipped + receiving
    local_actual: int | None
    local_plan: int | None
    sellable_days: float | None
    fba_sellable_days: float | None
    local_sellable_days: float | None
    safety_days: int | None
    lead_time_days: int | None
    stockout_date: date | None
    purchase_date: date | None
    # 建议
    suggest: bool
    suggest_qty: int
    suggest_amount: float | None
    suggest_amount_base: float | None
    base_currency: str | None
    # 财务
    revenue_7d: float | None
    gross_margin: float | None
    financial_estimate_type: FinancialEstimateType | None
    # 价值维度(AI Agent / 列表排序 / 风险榜单用)
    expected_loss_revenue_7d: float | None = None
    """未来 7 天因 FBA 断货预期销售损失(单位:成本币种,启发式).

    公式:max(0, 7 - fba_sellable_days) × future_daily × unit_cost
    用 cost 作为下限估算(seed 无售价字段);≥ 7 天可售则为 0。
    """
    future_30d_profit: float | None = None
    """未来 30 天预期毛利估算(单位:成本币种,启发式,假设 30% 毛利).

    公式:future_daily × 30 × unit_cost × 0.30
    用于 AI 排序"高利润 SKU"维度;实际派生表上线后改用真实毛利率。
    """

    # 采购 / 发货时间 (P3 — 来自 mk_purchase_draft 派生)
    last_purchase_date: datetime | None = None
    """最近一次采购草稿创建时间(同 tenant+mall+msku)."""
    last_shipment_date: datetime | None = None
    """最近一次发货时间 — 当前用 draft.status='confirmed' 的更新时间近似."""
    estimated_arrival_date: date | None = None
    """最早一笔在途货件的预计到货日期(mk_sku_inbound_detail.min(expected_arrival_date))."""

    # 元数据
    last_updated: datetime | None


class SkuDetailRequest(BaseModel):
    """详情查询请求."""

    tenant_id: int
    listing_id: int
    calc_run_id: str | None = None  # 不传 = latest


class ForecastTrendPoint(BaseModel):
    date: date
    qty: float
    source: str | None = None
    is_adjusted: bool = False


class InboundDetailDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inbound_id: str
    inbound_type: str
    inbound_status: str
    qty: int
    expected_arrival_date: date | None
    source_order_no: str | None = None


class SkuDetailDTO(BaseModel):
    """对应前端 ViewModel: SkuDetail."""

    calc_run_id: str
    summary: SkuSummaryDTO
    forecast_trend: list[ForecastTrendPoint] = Field(default_factory=list)
    inbound_list: list[InboundDetailDTO] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)


class SkuTrendsRequest(BaseModel):
    """详情页趋势曲线请求."""

    tenant_id: int
    listing_id: int
    calc_run_id: str | None = None
    history_days: int = 90  # 历史窗口


class TrendPoint(BaseModel):
    date: date
    qty: float


class SkuTrendsDTO(BaseModel):
    """详情页趋势曲线响应 — 历史(实际销量) + 预测(逐日)."""

    calc_run_id: str
    msku: str
    mall_id: int | None
    history: list[TrendPoint] = Field(default_factory=list)
    forecast: list[TrendPoint] = Field(default_factory=list)
