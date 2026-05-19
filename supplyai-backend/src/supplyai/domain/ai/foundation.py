"""Foundation Skills — 注入到 AI 的硬约束.

技术方案 §7.5 要求 AI 不能"自由发挥",必须遵守:
  1. 口径锁定到同一系统快照,不跨快照混用数据。
  2. 不重新计算建议采购量 / 可售天数 / 断货日期,只解释。
  3. 预计断货 / 可售天数 / 风险等级均使用备货列表同一规则库存口径。
  4. 缺失值 / 估算 / 多币种必须显式说明。
  5. 采购草稿动作必须二次确认 SKU、数量、供应商三项,不能仅凭自然语言落库。
"""
from __future__ import annotations

import re
from typing import Any, Literal

AiStatus = Literal["ok", "partial", "degraded"]


SYSTEM_PROMPT = """\
你是 SupplyAI 供应链分析助手,服务于 Amazon 卖家备货决策。

【硬约束 — 不可违反】
1. 口径锁定:所有引用的数字必须来自同一个系统快照,不允许跨批次混用。
2. 不重算:你只解释系统已经计算好的建议采购量、覆盖周期需求、
   可售天数、断货日期等结果,绝不自行计算建议采购量、可售天数、断货日期。
3. 口径区分:
   - 可售天数使用规则配置后的参与库存。
   - 建议采购时间和建议采购量使用同一规则库存口径。
4. 显式声明缺失:任何字段为 None / 估算 / 多币种折算时,必须在回答里说明
   (例如"单位成本缺失,采购金额未折算")。
5. 采购草稿动作:涉及生成采购草稿时,必须先在回答中列出 SKU、数量、供应商三项,
   并提示用户在前端二次确认,不允许自然语言直接触发草稿落库。
6. 用户可见回答里禁止出现数据库表名、字段名、查询语句、内部快照编号、内部参数名或内部 ID。
   请把所有技术字段、内部编号、下划线命名的信息全部改用业务术语。

【风险等级阈值】
   p1: 可售天数 ≤ 7 天 (紧急)
   p2: 可售天数 8-15 天 (关注)
   p3: 可售天数 16-30 天 (计划)
   safe: 可售天数 > 30 天

输出格式要求:中文,简洁,2-4 句结论 + 关键数字带单位。"""


def build_explain_prompt(dto: Any, *, calc_run_id: str) -> str:
    """从 SKU summary 构造 explain prompt,缺失字段标 '缺失'."""
    _ = calc_run_id  # 只用于调用方锁定快照,不写入用户可见 prompt。

    def _v(value: Any) -> str:
        if value is None:
            return "缺失"
        return str(value)

    return (
        "基于同一系统快照解释以下 SKU 的风险与建议。"
        "系统快照编号仅用于内部口径锁定,不要在回答中提及:\n"
        f"  MSKU={_v(getattr(dto, 'msku', None))}\n"
        f"  ASIN={_v(getattr(dto, 'asin', None))}\n"
        f"  店铺={_v(getattr(dto, 'store_name', None))}\n"
        f"  风险等级={_v(getattr(dto, 'priority', None))}\n"
        f"  可售天数={_v(getattr(dto, 'sellable_days', None))}\n"
        f"  总库存={_v(getattr(dto, 'total_stock', None))}\n"
        f"  覆盖周期需求={_v(getattr(dto, 'coverage_demand', None))}\n"
        f"  预测来源={_v(getattr(dto, 'forecast_source', None))}\n"
        f"  断货日期={_v(getattr(dto, 'stockout_date', None))}\n"
        f"  建议采购={_v(getattr(dto, 'suggest_qty', None))} 件\n"
        f"  建议采购金额(基准币)={_v(getattr(dto, 'suggest_amount_base', None))} "
        f"{_v(getattr(dto, 'base_currency', None))}\n"
        "请遵守系统约束,在 3 句内给出风险解读 + 1 条可操作建议。"
        "如有字段标记为'缺失',必须在回答中明确指出该字段缺失,不要假装数据完整。"
    )


_VISIBLE_TERM_REPLACEMENTS = {
    "mk_supply_sku_daily_stat": "备货分析结果",
    "mk_purchase_draft": "采购计划草稿",
    "mk_holiday": "节日配置",
    "mk_sku_inbound_detail": "在途明细",
    "rl_fba_shipment_item": "FBA 发货记录",
    "rl_amz_sales_daily_report": "销量记录",
    "rl_product": "商品资料",
    "calc_run_id": "系统快照",
    "listing_id": "商品编号",
    "mall_id": "店铺编号",
    "tenant_id": "账号信息",
    "holiday_id": "节日编号",
    "suggest_qty": "建议采购量",
    "suggest_amount": "建议采购金额",
    "coverage_demand": "覆盖周期需求",
    "sellable_days": "可售天数",
    "fba_sellable_days": "可售天数",
    "stockout_date": "预计断货日期",
    "purchase_date": "建议采购日期",
    "forecast_source": "预测来源",
    "unit_cost": "单位成本",
}

_INTERNAL_NAME_PATTERN = re.compile(r"\b(?:mk|rl)_[A-Za-z0-9_]+\b")


def sanitize_user_ai_text(text: str | None) -> str:
    """清洗所有用户可见的 AI 文本,避免泄露内部表名/字段名."""
    if not text:
        return ""
    out = str(text)
    for raw, label in _VISIBLE_TERM_REPLACEMENTS.items():
        out = re.sub(rf"\b{re.escape(raw)}\b", label, out)
    out = _INTERNAL_NAME_PATTERN.sub("系统数据", out)
    out = re.sub(r"\bSQL\b", "数据查询", out, flags=re.IGNORECASE)
    return out


# 决定 status 用的关键字段
_KEY_FIELDS = ("sellable_days", "suggest_qty", "stockout_date")


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
