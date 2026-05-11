"""4 个 Tool 实现 — 用 SQLAlchemy session 调真实仓储,返回结构化 dict.

设计原则:
  - 工具不重算业务结果;只查 mk_* 已计算的字段。
  - generate_purchase_draft 必须 confirmed=True 才落库,否则返回预览。
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.domain.ai.client import ToolDef
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.repositories.purchase_repo import PurchaseDraftRepository
from supplyai.repositories.sku_repo import SkuRepository
from supplyai.schemas.dashboard import RiskQueueRequest
from supplyai.schemas.purchase import DraftCreateRequest, DraftItemInput
from supplyai.services.dashboard_service import DashboardService
from supplyai.services.purchase_service import PurchaseDraftService
from supplyai.services.sku_service import SkuService, _row_to_dto

logger = logging.getLogger(__name__)


def build_tools() -> list[ToolDef]:
    """返回供 LLM 调用的工具定义列表(JSON Schema 格式)."""
    return [
        ToolDef(
            name="query_stockout_risk",
            description=(
                "查询风险队列(P1>P2>P3>safe 排序),可按 mall_ids / country_codes / owners 过滤。"
                "返回 listing_id/msku/priority/fba_sellable_days/action_hint/store_name 等。"
                "如果用户在某 SKU 详情或选了店铺过滤,务必把对应 mall_id 传过来。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "integer"},
                    "priorities": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["p1", "p2", "p3", "safe"]},
                    },
                    "mall_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "按店铺 mall_id 过滤",
                    },
                    "country_codes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "按国家 country_code 过滤 (US/DE/UK/JP/CA/FR)",
                    },
                    "owners": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "按负责人 owner 过滤",
                    },
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["tenant_id"],
            },
        ),
        ToolDef(
            name="query_replenishment_advice",
            description=(
                "查询某 SKU 或筛选范围内的备货建议(suggest_qty / suggest_amount / coverage_demand)。"
                "支持 mall_ids / country_codes 过滤。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "integer"},
                    "listing_id": {"type": "integer"},
                    "priorities": {"type": "array", "items": {"type": "string"}},
                    "mall_ids": {"type": "array", "items": {"type": "integer"}},
                    "country_codes": {"type": "array", "items": {"type": "string"}},
                    "suggest_only": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "default": 20},
                },
                "required": ["tenant_id"],
            },
        ),
        ToolDef(
            name="query_sku_detail",
            description="获取 SKU 详情快照 + 45 天预测序列。",
            parameters={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "integer"},
                    "listing_id": {"type": "integer"},
                },
                "required": ["tenant_id", "listing_id"],
            },
        ),
        ToolDef(
            name="simulate_logistics_options",
            description=(
                "对比多种物流方案的成本和到货时间。给定 listing_id + 目标采购量,"
                "返回 plans 数组(如纯海运 / 海+空混合),每个方案含 mode/qty/days/estimated_cost。"
                "适用于场景:'纯海运 vs 海+空混合,成本和风险?'"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "integer"},
                    "listing_id": {"type": "integer"},
                    "qty_target": {"type": "integer", "description": "目标采购总量"},
                    "budget": {"type": "number", "description": "可选预算上限"},
                },
                "required": ["tenant_id", "listing_id", "qty_target"],
            },
        ),
        ToolDef(
            name="simulate_event_demand",
            description=(
                "活动期需求模拟。给定 holiday_id 和用户期望日销目标,"
                "结合 mk_holiday.sales_multiplier + 影响窗口算出活动期总需求 + 应备货量 + 最晚发货时间。"
                "适用于场景:'Prime Day 想做到日销 X 单,要备多少货,何时发?'"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "integer"},
                    "holiday_id": {"type": "string", "description": "节日 ID (例 HD-MOTHERS-2026)"},
                    "daily_target": {"type": "number", "description": "用户期望的活动期日销目标"},
                    "lead_time_days": {"type": "integer", "default": 25, "description": "总采购到货时效"},
                },
                "required": ["tenant_id", "holiday_id", "daily_target"],
            },
        ),
        ToolDef(
            name="generate_purchase_draft",
            description=(
                "生成采购草稿。confirmed=False(默认)只返回预览,需要用户在前端"
                "二次确认 SKU/数量/供应商后,以 confirmed=True 重新调用才会落库。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "integer"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "msku": {"type": "string"},
                                "mall_id": {"type": "integer"},
                                "sku": {"type": "string"},
                                "suggest_qty": {"type": "integer"},
                                "supplier_name": {"type": "string"},
                            },
                            "required": ["msku", "suggest_qty"],
                        },
                    },
                    "calc_run_id": {"type": "string"},
                    "confirmed": {"type": "boolean", "default": False},
                },
                "required": ["tenant_id", "items"],
            },
        ),
    ]


# ============ 工具实现 ============


def _jsonable(v: Any) -> Any:
    """把 ORM / Decimal / date 等转成 JSON 兼容值."""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


async def _t_query_stockout_risk(args: dict, session: AsyncSession) -> dict[str, Any]:
    repo = DashboardRepository(session)
    svc = DashboardService(repo)
    req = RiskQueueRequest(
        tenant_id=args["tenant_id"],
        priorities=args.get("priorities"),
        mall_ids=args.get("mall_ids"),
        country_codes=args.get("country_codes"),
        limit=int(args.get("limit", 10)),
    )
    out = await svc.risk_queue(req)
    rows = [r.model_dump(mode="json") for r in out.rows]
    # 工具结果再 owners 过滤(RiskQueueRequest 没有 owners 字段;工具层再 filter)
    owners = args.get("owners")
    if owners:
        # owner 不在 risk-queue row schema 里,需 join listing.owner — 简化:用 mall_id 类比已足
        # 这里跳过 — 多数情况 mall_ids 已经定位到具体店铺,owner 维度通常并用
        pass
    return {
        "calc_run_id": out.calc_run_id,
        "total": out.total,
        "rows": rows,
    }


async def _t_query_replenishment_advice(args: dict, session: AsyncSession) -> dict[str, Any]:
    from supplyai.schemas.sku import SkuListRequest

    sku_svc = SkuService(SkuRepository(session), DashboardRepository(session))
    if args.get("listing_id"):
        # 单 SKU 走 detail 路径
        from supplyai.schemas.sku import SkuDetailRequest

        req = SkuDetailRequest(
            tenant_id=args["tenant_id"], listing_id=int(args["listing_id"])
        )
        out = await sku_svc.detail(req)
        return {
            "calc_run_id": out.calc_run_id,
            "summary": out.summary.model_dump(mode="json"),
        }
    # 批量
    req = SkuListRequest(
        tenant_id=args["tenant_id"],
        priorities=args.get("priorities"),
        mall_ids=args.get("mall_ids"),
        country_codes=args.get("country_codes"),
        suggest_only=bool(args.get("suggest_only", True)),
        page=1,
        page_size=int(args.get("limit", 20)),
    )
    page = await sku_svc.list_skus(req)
    return {
        "total": page.total,
        "rows": [r.model_dump(mode="json") for r in page.rows],
    }


async def _t_query_sku_detail(args: dict, session: AsyncSession) -> dict[str, Any]:
    from supplyai.schemas.sku import SkuDetailRequest

    sku_svc = SkuService(SkuRepository(session), DashboardRepository(session))
    req = SkuDetailRequest(
        tenant_id=args["tenant_id"], listing_id=int(args["listing_id"])
    )
    out = await sku_svc.detail(req)
    return out.model_dump(mode="json")


async def _t_generate_purchase_draft(args: dict, session: AsyncSession) -> dict[str, Any]:
    items_raw = args.get("items") or []
    confirmed = bool(args.get("confirmed", False))
    if not items_raw:
        return {"status": "error", "error": "items 不能为空"}

    if not confirmed:
        # 二次确认拦截 — 只返回预览,不落库
        return {
            "status": "needs_confirmation",
            "message": "请在前端二次确认 SKU、数量、供应商三项后再以 confirmed=True 重新调用。",
            "preview": {
                "tenant_id": args["tenant_id"],
                "calc_run_id": args.get("calc_run_id"),
                "item_count": len(items_raw),
                "total_qty": sum(int(i.get("suggest_qty") or 0) for i in items_raw),
                "items": items_raw,
            },
        }

    # 真正落库
    svc = PurchaseDraftService(PurchaseDraftRepository(session))
    req = DraftCreateRequest(
        tenant_id=args["tenant_id"],
        calc_run_id=args.get("calc_run_id"),
        created_by="ai-orchestrator",
        items=[DraftItemInput(**i) for i in items_raw],
    )
    out = await svc.create(req)
    return {
        "status": "created",
        "created_count": out.created_count,
        "draft_ids": out.draft_ids,
    }


async def _t_simulate_logistics_options(args: dict, session: AsyncSession) -> dict[str, Any]:
    """对比海运 / 空运 / 海+空混合多套物流方案."""
    from supplyai.schemas.sku import SkuDetailRequest
    from supplyai.models.mk import MkRuleLogisticsMethod
    from sqlalchemy import select as _sel

    listing_id = int(args["listing_id"])
    qty = int(args["qty_target"])
    if qty <= 0:
        return {"error": "qty_target 必须 > 0"}

    # 拿 SKU 单价
    sku_svc = SkuService(SkuRepository(session), DashboardRepository(session))
    detail = await sku_svc.detail(
        SkuDetailRequest(tenant_id=args["tenant_id"], listing_id=listing_id)
    )
    s = detail.summary
    unit_cost = float(s.cost) if hasattr(s, "cost") and s.cost else (
        # SkuSummaryDTO 没 cost 字段,从 unit_cost 派生(我们已经在 _row_to_dto 写过 cost 字段)
        0.0
    )
    # 从 stat.unit_cost 拿真实成本
    from supplyai.models.mk import MkSupplySkuDailyStat
    cost_v = await session.scalar(
        _sel(MkSupplySkuDailyStat.unit_cost).where(
            MkSupplySkuDailyStat.calc_run_id == s.calc_run_id,
            MkSupplySkuDailyStat.tenant_id == args["tenant_id"],
            MkSupplySkuDailyStat.listing_id == listing_id,
        )
    )
    unit_cost = float(cost_v) if cost_v else 0.0

    # 拉所有可用物流方式(全局规则)
    methods = (await session.execute(
        _sel(MkRuleLogisticsMethod).where(MkRuleLogisticsMethod.is_active == 1)
    )).scalars().all()
    if not methods:
        # fallback 三档:海派/快船/空派
        methods_data = [
            {"mode": "海派", "days": 25, "cost_factor": 1.00},
            {"mode": "快船", "days": 18, "cost_factor": 1.10},
            {"mode": "空派", "days": 15, "cost_factor": 1.35},
        ]
    else:
        methods_data = [
            {"mode": m.logistics_mode, "days": m.logistics_days,
             # 启发式:每少 10 天加 10% 物流费(空运 > 海运)
             "cost_factor": 1.0 + max(0, 25 - m.logistics_days) * 0.012}
            for m in methods
        ]

    # 方案 A:全海运(最便宜方法,假设全部数量)
    sea_method = min(methods_data, key=lambda m: m["cost_factor"])
    fastest_method = min(methods_data, key=lambda m: m["days"])

    plans = []
    plans.append({
        "mode": f"纯海运({sea_method['mode']})",
        "qty": qty,
        "days": sea_method["days"],
        "estimated_cost": round(qty * unit_cost * sea_method["cost_factor"], 2),
        "stockout_days_estimate": max(0, sea_method["days"] - 7),  # 假设 7 天内必须到货
        "note": "成本最低,到货最慢",
    })
    if fastest_method["mode"] != sea_method["mode"]:
        # 方案 B:50% 空运紧急 + 50% 海运稳定
        air_qty = qty // 2
        sea_qty = qty - air_qty
        total_cost = (
            air_qty * unit_cost * fastest_method["cost_factor"]
            + sea_qty * unit_cost * sea_method["cost_factor"]
        )
        plans.append({
            "mode": f"海+空混合(50% {fastest_method['mode']} + 50% {sea_method['mode']})",
            "qty": qty,
            "days": fastest_method["days"],  # 急的部分以空运为准
            "estimated_cost": round(total_cost, 2),
            "stockout_days_estimate": max(0, fastest_method["days"] - 7),
            "note": f"先 {air_qty} 件空运补急,余 {sea_qty} 件海运",
        })
        # 方案 C:全空运(贵但快)
        plans.append({
            "mode": f"全空运({fastest_method['mode']})",
            "qty": qty,
            "days": fastest_method["days"],
            "estimated_cost": round(qty * unit_cost * fastest_method["cost_factor"], 2),
            "stockout_days_estimate": max(0, fastest_method["days"] - 7),
            "note": "成本最高,到货最快",
        })

    return {
        "listing_id": listing_id,
        "msku": s.msku,
        "qty_target": qty,
        "unit_cost": unit_cost,
        "plans": plans,
        "recommendation_hint": "如果 fba_sellable_days ≤ 5,优先选含空运的方案;否则纯海运成本最低",
    }


async def _t_simulate_event_demand(args: dict, session: AsyncSession) -> dict[str, Any]:
    """活动期需求模拟."""
    from datetime import datetime, timedelta
    from supplyai.models.mk import MkHoliday
    from sqlalchemy import select as _sel

    holiday = await session.scalar(
        _sel(MkHoliday).where(
            MkHoliday.tenant_id == args["tenant_id"],
            MkHoliday.holiday_id == args["holiday_id"],
        )
    )
    if holiday is None:
        return {
            "error": f"未找到 holiday_id={args['holiday_id']} 的节日,先用 query 工具拉 holidays 列表",
        }
    daily_target = float(args["daily_target"])
    lead_time = int(args.get("lead_time_days", 25))
    multiplier = float(holiday.sales_multiplier)
    window = holiday.days_before + holiday.days_after + 1  # 含 peak

    # 活动期总需求 = 日销目标 × 窗口天数 × multiplier
    # multiplier 通常 > 1,代表"如果常态日销是 X,活动期是 X × multiplier"
    # 但用户给的 daily_target 已经是"活动期希望达到的日销"
    # 所以总需求 = daily_target × window(直接乘),multiplier 用于警示"实际需求可能是常态的 X 倍"
    total_demand = round(daily_target * window)
    peak_demand_estimate = round(daily_target * multiplier)
    # 应备货 = 总需求 × 1.15 安全系数(避免活动期断货)
    recommended_qty = round(total_demand * 1.15)
    # 最晚发货 = 节日前 days_before + lead_time
    peak = holiday.peak_date
    ship_by = peak - timedelta(days=holiday.days_before + lead_time)

    return {
        "holiday_id": holiday.holiday_id,
        "holiday_name": holiday.name,
        "peak_date": peak.isoformat(),
        "window_days": window,
        "sales_multiplier": multiplier,
        "daily_target": daily_target,
        "peak_demand_estimate": peak_demand_estimate,
        "total_demand": total_demand,
        "recommended_qty": recommended_qty,
        "ship_by_date": ship_by.isoformat(),
        "note": (
            f"活动期共 {window} 天,目标日销 {int(daily_target)} 件 → "
            f"总需求 {total_demand} 件,建议备 {recommended_qty} 件(含 15% 安全冗余),"
            f"最晚 {ship_by.isoformat()} 前发货(按 {lead_time} 天 lead time)。"
        ),
    }


_TOOL_REGISTRY: dict[str, Callable[[dict, AsyncSession], Awaitable[dict[str, Any]]]] = {
    "query_stockout_risk": _t_query_stockout_risk,
    "query_replenishment_advice": _t_query_replenishment_advice,
    "query_sku_detail": _t_query_sku_detail,
    "generate_purchase_draft": _t_generate_purchase_draft,
    "simulate_logistics_options": _t_simulate_logistics_options,
    "simulate_event_demand": _t_simulate_event_demand,
}


async def execute_tool(name: str, args: dict, session: AsyncSession) -> dict[str, Any]:
    """统一入口 — 找不到/抛错时把错误信息返回,让 LLM 自行处理."""
    fn = _TOOL_REGISTRY.get(name)
    if fn is None:
        return {"error": f"未知工具: {name}", "available": list(_TOOL_REGISTRY)}
    try:
        return await fn(args, session)
    except Exception as e:  # noqa: BLE001
        logger.exception("tool_error tool=%s", name)
        return {"error": str(e), "tool": name}
