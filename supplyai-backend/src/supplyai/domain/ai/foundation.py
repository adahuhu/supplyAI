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
你是一位有 10 年以上经验的 Amazon 跨境电商高级运营专家，深度参与过多个品类的备货规划、\
库存管控和物流策略。你被集成在 SupplyAI 系统里，帮助运营团队在真实数据的基础上做出更好的决策。

你说话的方式：
- 像老运营跟同事讲话一样，直接说重点，不废话，但该解释的背景会说清楚。
- 会主动点出风险的"严重性"：不只说"FBA 只剩 5 天"，还会说"按这个销速，周五就能断货，
  如果这周不发货，后面补救成本会很高"。
- 数字不孤立存在——一定带上"这意味着什么"：比如"发货 120 件，按当前日销能撑约 40 天，
  刚好覆盖下一批海运到仓前的窗口"。
- 有时会主动给出一个判断或倾向性建议，而不是把选项全部抛给用户——
  比如"我建议优先用空派补这一单，虽然成本高些，但现在用海运已经来不及了"。
- 如果用户的问题本身有误区，会温和地指出来，比如"你问的是采购量，
  但我理解你可能更关心的是发货量——这两个口径不一样，我来分别说一下"。

【数据边界 — 必须遵守，不可违反】
1. 所有数字必须来自系统当前快照，不允许估猜、编造或跨批次混用数据。
2. 系统没有给出某个数字时，不能凭经验"补"一个，必须说明"系统当前没有这个数据"。
3. 建议采购量、FBA 可售天数、断货日期等系统已算好的结果，直接引用，不自行重算。
4. 任何字段为空或缺失时，明确告知用户，不假装数据完整。
5. 涉及生成采购草稿，必须先列出 SKU、数量、供应商三项，提示用户在前端二次确认，
   不允许自然语言直接触发草稿落库。
6. 回答中禁止出现数据库表名、字段名、内部 ID、快照编号等技术词汇，一律改用业务语言。

【供应链知识 — FBA 头程发货口径】
- 发货到 FBA 的目标库存 = 头程物流天数（空派约 10-15 天，海运约 30-45 天）× 日销 + 安全库存天数 × 日销。
- 建议发货量 = 目标 FBA 库存 - 当前 FBA 可售 - 当前 FBA 在途。
- 这与"备货采购"是两件事：采购看全链路总库存够不够；发货看 FBA 侧缺口有多大。
- 举例：日销 5 件，海运 35 天 + 安全 14 天 = 目标 245 件；FBA 可售 20 件 + 在途 50 件 = 已有 70 件；
  则建议发货 175 件。

【风险等级参考】
   P1：FBA 可售 ≤ 7 天（断货警报，需立即安排发货或空派补货）
   P2：FBA 可售 8-15 天（本周内必须行动，否则断货风险极高）
   P3：FBA 可售 16-30 天（计划期，纳入下次常规备货节奏）
   安全：FBA 可售 > 30 天（暂时无需操心，关注销量变化即可）

输出语言：中文。风格：运营专家口吻，结论先行，数字带单位，有判断，有温度。"""


def build_explain_prompt(dto: Any, *, calc_run_id: str) -> str:
    """从 SKU summary 构造 explain prompt，缺失字段标 '缺失'."""
    _ = calc_run_id  # 只用于调用方锁定快照，不写入用户可见 prompt。

    def _v(value: Any) -> str:
        if value is None:
            return "缺失"
        return str(value)

    def _vf(value: Any, digits: int = 1) -> str:
        if value is None:
            return "缺失"
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return str(value)

    # 库存结构
    fba_avail = getattr(dto, "fba_available", None)
    fba_inbound = getattr(dto, "fba_inbound", None)
    local_actual = getattr(dto, "local_actual", None)
    total_stock = getattr(dto, "total_stock", None)

    # 销售节奏
    future_daily = getattr(dto, "future_daily", None)
    sales_7d = getattr(dto, "sales_7d", None)
    yesterday_sales = getattr(dto, "yesterday_sales", None)

    # 参数
    safety_days = getattr(dto, "safety_days", None)
    lead_time_days = getattr(dto, "lead_time_days", None)

    return (
        "基于同一系统快照解释以下 SKU 的库存风险、建议采购与建议发货情况。\n"
        "快照编号仅用于内部口径锁定，不要在回答中提及。\n\n"
        "【SKU 基本信息】\n"
        f"  MSKU: {_v(getattr(dto, 'msku', None))}\n"
        f"  ASIN: {_v(getattr(dto, 'asin', None))}\n"
        f"  店铺: {_v(getattr(dto, 'store_name', None))}\n"
        f"  风险等级: {_v(getattr(dto, 'priority', None))}\n\n"
        "【库存结构（当前快照）】\n"
        f"  FBA 可售库存: {_v(fba_avail)} 件\n"
        f"  FBA 在途入库: {_v(fba_inbound)} 件（已发往 FBA，尚未上架）\n"
        f"  国内仓实际库存: {_v(local_actual)} 件\n"
        f"  参与计算总库存: {_v(total_stock)} 件\n\n"
        "【销售与预测】\n"
        f"  昨日销量: {_v(yesterday_sales)} 件\n"
        f"  近 7 天总销量: {_v(sales_7d)} 件\n"
        f"  预测日销（系统计算）: {_vf(future_daily, 2)} 件/天\n"
        f"  预测来源: {_v(getattr(dto, 'forecast_source', None))}\n\n"
        "【时效参数】\n"
        f"  FBA 可售天数: {_vf(getattr(dto, 'fba_sellable_days', None), 1)} 天\n"
        f"  预计断货日: {_v(getattr(dto, 'stockout_date', None))}\n"
        f"  安全库存天数: {_v(safety_days)} 天\n"
        f"  供应商备货周期（含头程）: {_v(lead_time_days)} 天\n\n"
        "【采购建议（全链路口径）】\n"
        f"  覆盖周期需求: {_vf(getattr(dto, 'coverage_demand', None), 1)} 件\n"
        f"  建议采购量: {_v(getattr(dto, 'suggest_qty', None))} 件\n"
        f"  建议采购时间: {_v(getattr(dto, 'purchase_date', None))}\n"
        f"  建议采购金额: {_vf(getattr(dto, 'suggest_amount_base', None), 2)} "
        f"{_v(getattr(dto, 'base_currency', None))}\n\n"
        "请根据以上快照，用自然、简洁的中文给出：\n"
        "1. 当前库存风险解读（紧不紧，为什么）\n"
        "2. 建议采购的核心依据（一句话点明关键因素）\n"
        "3. 一条明确的行动建议（具体到件数或时间节点）\n"
        "如有字段标记为'缺失'，在回答中明确指出，不要假装数据完整。"
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
    "risk_level": "风险等级",
    "immediate": "紧急",
    "urgent": "紧急",
    "safe": "安全",
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
    out = re.sub(r"([\u4e00-\u9fff])\s+(紧急|安全|风险等级)", r"\1\2", out)
    out = re.sub(r"(紧急|安全|风险等级)\s+([\u4e00-\u9fff])", r"\1\2", out)
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
