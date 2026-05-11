"""Foundation Skills — 注入到 AI 的硬约束.

技术方案 §7.5 要求 AI 不能"自由发挥",必须遵守:
  1. 口径锁定到同一 calc_run_id,不跨快照混用数据。
  2. 不重新计算 suggest_qty / sellable_days / stockout_date,只解释。
  3. 预计断货 = FBA 侧;采购时间 = 全链路总库存口径。
  4. 缺失值 / 估算 / 多币种必须显式说明。
  5. 采购草稿动作必须二次确认 SKU、数量、供应商三项,不能仅凭自然语言落库。
"""
from __future__ import annotations

from typing import Any, Literal

AiStatus = Literal["ok", "partial", "degraded"]


SYSTEM_PROMPT = """\
你是 SupplyAI 供应链分析助手,服务于 Amazon 卖家备货决策。

【硬约束 — 不可违反】
1. 口径锁定:所有引用的数字必须来自同一个 calc_run_id 快照,不允许跨批次混用。
2. 不重算:你只解释 mk_supply_sku_daily_stat 中已计算的字段
   (suggest_qty / coverage_demand / fba_sellable_days / stockout_date 等),
   绝不自行计算建议采购量、可售天数、断货日期。
3. 口径区分:
   - 预计断货时间(stockout_date)使用 FBA 侧库存(fba_available + fba_inbound)。
   - 建议采购时间(purchase_date)和建议采购量(suggest_qty)使用全链路总库存。
4. 显式声明缺失:任何字段为 None / 估算 / 多币种折算时,必须在回答里说明
   (例如"unit_cost 缺失,采购金额未折算")。
5. 采购草稿动作:涉及生成采购草稿时,必须先在回答中列出 SKU、数量、供应商三项,
   并提示用户在前端二次确认,不允许自然语言直接触发草稿落库。

【风险等级阈值】
   p1: FBA 可售 ≤ 7 天 (紧急)
   p2: FBA 可售 8-15 天 (关注)
   p3: FBA 可售 16-30 天 (计划)
   safe: FBA 可售 > 30 天

输出格式要求:中文,简洁,2-4 句结论 + 关键数字带单位。"""


def build_explain_prompt(dto: Any, *, calc_run_id: str) -> str:
    """从 SKU summary 构造 explain prompt,缺失字段标 '缺失'."""
    def _v(value: Any) -> str:
        if value is None:
            return "缺失"
        return str(value)

    return (
        f"基于 calc_run_id={calc_run_id} 解释以下 SKU 的风险与建议:\n"
        f"  MSKU={_v(getattr(dto, 'msku', None))}\n"
        f"  ASIN={_v(getattr(dto, 'asin', None))}\n"
        f"  店铺={_v(getattr(dto, 'store_name', None))}\n"
        f"  风险等级={_v(getattr(dto, 'priority', None))}\n"
        f"  FBA 可售天数={_v(getattr(dto, 'fba_sellable_days', None))}\n"
        f"  总库存={_v(getattr(dto, 'total_stock', None))}\n"
        f"  覆盖周期需求(coverage_demand)={_v(getattr(dto, 'coverage_demand', None))}\n"
        f"  预测来源(forecast_source)={_v(getattr(dto, 'forecast_source', None))}\n"
        f"  断货日期={_v(getattr(dto, 'stockout_date', None))}\n"
        f"  建议采购={_v(getattr(dto, 'suggest_qty', None))} 件\n"
        f"  建议采购金额(基准币)={_v(getattr(dto, 'suggest_amount_base', None))} "
        f"{_v(getattr(dto, 'base_currency', None))}\n"
        "请遵守系统约束,在 3 句内给出风险解读 + 1 条可操作建议。"
        "如有字段标记为'缺失',必须在回答中明确指出该字段缺失,不要假装数据完整。"
    )


# 决定 status 用的关键字段
_KEY_FIELDS = ("fba_sellable_days", "suggest_qty", "stockout_date")


def classify_status(sku_ctx: dict[str, Any], *, ai_available: bool) -> AiStatus:
    """根据数据完整性 + AI 可用性,派生 AiAnswer.status.

    - AI 不可用 → degraded(降级到结构化规则解释)
    - 关键字段缺失 → partial
    - 都齐全 → ok
    """
    if not ai_available:
        return "degraded"
    missing = [k for k in _KEY_FIELDS if not sku_ctx.get(k)]
    if missing:
        return "partial"
    return "ok"
