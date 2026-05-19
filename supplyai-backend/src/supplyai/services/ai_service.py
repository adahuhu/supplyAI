"""AI 编排服务 — 解释单 SKU + 通用对话."""
from __future__ import annotations

import logging
import math
import re
from datetime import date
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.config import settings
from supplyai.domain.ai.client import AiClient, ChatMessage
from supplyai.domain.ai.foundation import (
    SYSTEM_PROMPT,
    build_explain_prompt,
    classify_status,
    sanitize_user_ai_text,
)
from supplyai.domain.ai.orchestrator import AiOrchestrator
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.repositories.sku_repo import SkuRepository
from supplyai.schemas.ai import (
    ChatRequest,
    ChatResponseMessage,
    DecisionCardRequest,
    DecisionCardResponse,
    ExplainRequest,
    ExplainResponse,
)
from supplyai.schemas.dashboard import (
    DashboardSnapshotRequest,
    HolidaysRequest,
    RiskQueueRequest,
)
from supplyai.schemas.sku import SkuDetailRequest, SkuListRequest, SkuSummaryDTO
from supplyai.services.dashboard_service import DashboardService
from supplyai.services.sku_service import SkuService, _row_to_dto
from supplyai.utils.exceptions import (
    AiEmptyMessagesException,
    CalcRunNotFoundException,
    SkuNotFoundException,
)

logger = logging.getLogger(__name__)


def _sku_card_row(s: SkuSummaryDTO) -> dict:
    return {
        "id": str(s.id),
        "listingId": s.listing_id,
        "mallId": s.mall_id,
        "mall_id": s.mall_id,
        "msku": s.msku,
        "sku": s.sku,
        "asin": s.asin,
        "name": s.product_name,
        "store": s.store_name,
        "country": {"code": s.country_code} if s.country_code else None,
        "priority": s.priority,
        "fbaSellable": s.fba_sellable_days,
        "stockoutDate": s.stockout_date.isoformat() if s.stockout_date else None,
        "suggest": s.suggest,
        "suggestQty": s.suggest_qty,
        "suggestAmountBase": s.suggest_amount_base,
        "baseCurrency": s.base_currency,
        "futureDaily": s.future_daily,
        "coverageDemand": s.coverage_demand,
        "totalStock": s.total_stock,
        "safeDays": s.safety_days,
        "purchaseLeadTime": s.lead_time_days,
        "labelIds": s.label_ids,
        "tags": s.tags,
    }


def _sales_leader_row(s: SkuSummaryDTO, score: float) -> dict:
    sales_7d = int(s.sales_7d or 0)
    future_daily = float(s.future_daily or 0)
    fba_days = float(s.fba_sellable_days or 0)
    margin = float(s.gross_margin or 0)
    suggest_qty = int(s.suggest_qty or 0)
    risks: list[str] = []
    if fba_days < 7:
        risks.append(f"FBA 可售仅 {fba_days:.2f} 天")
    if suggest_qty > 0:
        risks.append(f"需补 {suggest_qty} 件")
    if margin < 0:
        risks.append("毛利为负")
    if not risks:
        risks.append("库存可支撑继续放量")

    recommendation = "重点推广"
    if fba_days < 7:
        recommendation = "先补货再推广"
    elif margin < 0:
        recommendation = "谨慎推广,先复核成本"
    elif sales_7d >= 100 and future_daily >= 10:
        recommendation = "优先加码"

    row = _sku_card_row(s)
    row.update(
        {
            "sales7d": sales_7d,
            "yesterdaySales": s.yesterday_sales,
            "futureDaily": round(future_daily, 2),
            "grossMargin": round(margin * 100, 2) if margin else None,
            "score": round(score, 2),
            "recommendation": recommendation,
            "reasons": [
                f"近 7 天销量 {sales_7d} 件",
                f"预测日销 {future_daily:.2f} 件",
                f"FBA 可售 {fba_days:.2f} 天",
                *risks[:2],
            ],
        }
    )
    return row


def _norm_tag(value: str | None) -> str:
    return re.sub(r"[\s_\-]+", "", str(value or "").lower())


def _sku_matches_holiday_tag(holiday, sku: SkuSummaryDTO) -> bool:
    if holiday is None:
        return False
    name = holiday.name or ""
    keys = [
        holiday.id,
        holiday.name,
        "大促",
        "promo" if "promo" in name.lower() else "",
        "Prime Day" if "prime" in name.lower() else "",
        "Memorial Day" if "memorial" in name.lower() else "",
    ]
    normalized_keys = [_norm_tag(k) for k in keys if _norm_tag(k)]
    tags = [_norm_tag(t) for t in sku.tags if _norm_tag(t)]
    return any(
        tag in key or key in tag
        for tag in tags
        for key in normalized_keys
    )


def _rule_impact_row(s: SkuSummaryDTO, *, target_safety_days: int) -> dict:
    current_safety = int(s.safety_days or 14)
    lead = int(s.lead_time_days or 0)
    daily = float(s.future_daily or 0)
    total_stock = int(s.total_stock or 0)
    current_suggest = int(s.suggest_qty or 0)
    next_coverage = daily * (lead + target_safety_days)
    next_suggest = (
        current_suggest
        if current_safety == target_safety_days
        else math.ceil(max(0, next_coverage - total_stock))
    )
    row = _sku_card_row(s)
    row.update(
        {
            "currentSafeDays": current_safety,
            "targetSafeDays": target_safety_days,
            "nextCoverageDemand": next_coverage,
            "nextSuggestQty": next_suggest,
            "qtyDelta": next_suggest - current_suggest,
        }
    )
    return row


def _degraded_explanation(ctx: dict) -> str:
    """AI 不可用时,基于结构化规则生成兜底解释."""
    parts = [
        f"[降级模式] SKU {ctx.get('msku')} 风险等级 {ctx.get('priority', 'unknown')}。"
    ]
    if ctx.get("fba_sellable_days") is not None:
        parts.append(f"FBA 可售 {ctx['fba_sellable_days']} 天。")
    if ctx.get("suggest_qty"):
        amt = ctx.get("suggest_amount_base")
        cur = ctx.get("base_currency") or "USD"
        amt_str = f",预计 {amt} {cur}" if amt else ""
        parts.append(f"建议采购 {ctx['suggest_qty']} 件{amt_str}。")
    return "".join(parts)


def _ctx_listing_id(ctx: dict | None) -> int | None:
    if not isinstance(ctx, dict):
        return None
    sku_ctx = ctx.get("sku")
    raw = None
    if isinstance(sku_ctx, dict):
        raw = sku_ctx.get("listing_id") or sku_ctx.get("listingId")
    raw = raw or ctx.get("listing_id") or ctx.get("listingId")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _fmt_date(v: date | None) -> str:
    return v.isoformat() if v else "暂未生成"


def _fmt_num(v: float | int | None, digits: int = 2) -> str:
    if v is None:
        return "—"
    if isinstance(v, int) or float(v).is_integer():
        return str(int(v))
    return f"{float(v):.{digits}f}"


def _local_sku_chat_text(question: str, dto: SkuSummaryDTO) -> str:
    """模型不可用时,基于 SKU 快照生成确定性回答."""
    q = question or ""
    title = f"{dto.msku} · {dto.store_name or ''}".strip(" ·")
    purchase_date = _fmt_date(dto.purchase_date)
    stockout_date = _fmt_date(dto.stockout_date)
    suggest_qty = int(dto.suggest_qty or 0)
    fba_days = _fmt_num(dto.fba_sellable_days)
    planning_stock = dto.planning_stock if dto.planning_stock is not None else dto.fba_available
    coverage = _fmt_num(dto.coverage_demand)
    future_daily = _fmt_num(dto.future_daily)

    if re.search(r"下次|什么时候|采购时间|备货时间|何时|多久", q):
        if dto.suggest and dto.purchase_date:
            return (
                f"{title} 的建议采购时间是 {purchase_date},建议采购 {suggest_qty} 件。\n"
                f"依据是:FBA 可售约 {fba_days} 天,预计断货日 {stockout_date};"
                f"覆盖周期需求 {coverage} 件,当前参与库存 {planning_stock or 0} 件。"
            )
        return (
            f"{title} 当前暂未生成新的采购时间。"
            f"当前 FBA 可售约 {fba_days} 天,预计断货日 {stockout_date},"
            f"系统建议采购量为 {suggest_qty} 件。"
        )

    if re.search(r"为什么|原因|怎么来|依据|因素", q):
        return (
            f"{title} 当前风险等级为 {(dto.priority or '').upper()},核心原因是 "
            f"FBA 可售约 {fba_days} 天、预测日销 {future_daily} 件、"
            f"参与库存 {planning_stock or 0} 件,覆盖周期需求 {coverage} 件。"
            f"因此系统给出的建议采购量是 {suggest_qty} 件。"
        )

    if re.search(r"采购量|补多少|买多少|数量", q):
        return (
            f"{title} 当前建议采购 {suggest_qty} 件。"
            f"计算口径为覆盖周期需求 {coverage} 件 - 参与库存 {planning_stock or 0} 件,"
            f"并按整件向上取整。"
        )

    return (
        f"{title} 当前 FBA 可售约 {fba_days} 天,预计断货日 {stockout_date},"
        f"建议采购时间 {purchase_date},建议采购 {suggest_qty} 件。"
        "以上来自当前 SKU 备货快照。"
    )


class AiService:
    def __init__(
        self,
        ai_client: AiClient,
        sku_repo: SkuRepository,
        dashboard_repo: DashboardRepository,
        session: AsyncSession | None = None,
    ) -> None:
        self._ai = ai_client
        self._sku_repo = sku_repo
        self._dashboard_repo = dashboard_repo
        self._session = session

    async def _build_explain_inputs(self, req: ExplainRequest):
        """共享 explain 准备逻辑 — 拿 calc_run_id / dto / ctx / prompt."""
        calc_run_id = req.calc_run_id or await self._dashboard_repo.latest_calc_run_id(
            req.tenant_id
        )
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)
        row = await self._sku_repo.get_one(
            calc_run_id=calc_run_id, tenant_id=req.tenant_id, listing_id=req.listing_id
        )
        if row is None:
            raise SkuNotFoundException(req.listing_id)
        stat, lps, mall_name = row
        dto = _row_to_dto(stat, lps, mall_name)
        ctx = {
            "msku": dto.msku,
            "asin": dto.asin,
            "store_name": dto.store_name,
            "priority": dto.priority,
            "fba_sellable_days": dto.fba_sellable_days,
            "stockout_date": dto.stockout_date.isoformat() if dto.stockout_date else None,
            "suggest_qty": dto.suggest_qty,
            "suggest_amount_base": dto.suggest_amount_base,
            "base_currency": dto.base_currency,
        }
        prompt = build_explain_prompt(dto, calc_run_id=calc_run_id)
        return calc_run_id, ctx, prompt

    async def _build_local_chat_fallback(
        self, req: ChatRequest, user_msgs: list[ChatMessage]
    ) -> str:
        """外部模型不可用时的本地回答,避免把供应商 503 暴露给用户."""
        question = user_msgs[-1].content if user_msgs else ""
        listing_id = _ctx_listing_id(req.context)
        if listing_id:
            calc_run_id = await self._dashboard_repo.latest_calc_run_id(req.tenant_id)
            if calc_run_id:
                row = await self._sku_repo.get_one(
                    calc_run_id=calc_run_id,
                    tenant_id=req.tenant_id,
                    listing_id=listing_id,
                )
                if row is not None:
                    stat, lps, mall_name = row
                    dto = _row_to_dto(stat, lps, mall_name)
                    return sanitize_user_ai_text(_local_sku_chat_text(question, dto))
        return (
            "AI 分析服务暂时不可用。我已保留当前页面的结构化分析结果,"
            "你可以先参考上方风险卡片、采购建议和计算依据;"
            "等服务恢复后再继续追问更开放的问题。"
        )

    async def explain(self, req: ExplainRequest) -> ExplainResponse:
        _calc_run_id, ctx, prompt = await self._build_explain_inputs(req)
        ai_available = True
        explanation: str
        try:
            chat_resp = await self._ai.chat(
                messages=[
                    ChatMessage(role="system", content=SYSTEM_PROMPT),
                    ChatMessage(role="user", content=prompt),
                ]
            )
            explanation = sanitize_user_ai_text(chat_resp.content)
        except Exception as e:  # noqa: BLE001
            logger.warning("ai_explain_degraded: %s", e)
            ai_available = False
            explanation = sanitize_user_ai_text(_degraded_explanation(ctx))

        status = classify_status(ctx, ai_available=ai_available)

        return ExplainResponse(
            explanation=explanation,
            context=ctx,
            model=settings.ai_model,
            status=status,
        )

    async def explain_stream(self, req: ExplainRequest) -> AsyncIterator[dict]:
        """流式版 explain — yield meta/delta/done 事件.

        事件:
          {"type":"meta","context":{...},"model":"..."}    # 首帧:SKU 上下文
          {"type":"delta","text":"..."}                    # 逐 token
          {"type":"done","finish_reason":"stop","status":"ok"}
          {"type":"error","message":"..."}                 # 异常 / 降级
        """
        try:
            _calc_run_id, ctx, prompt = await self._build_explain_inputs(req)
        except Exception as e:  # noqa: BLE001
            yield {"type": "error", "message": str(e)}
            yield {"type": "done", "finish_reason": "stop", "status": "degraded"}
            return

        yield {"type": "meta", "context": ctx, "model": settings.ai_model}

        try:
            got_any = False
            msgs = [
                ChatMessage(role="system", content=SYSTEM_PROMPT),
                ChatMessage(role="user", content=prompt),
            ]
            async for delta in self._ai.chat_stream(messages=msgs):
                if delta.reasoning_text and not delta.finish_reason:
                    got_any = True
                    yield {
                        "type": "reasoning_delta",
                        "text": sanitize_user_ai_text(delta.reasoning_text),
                    }
                if delta.text and not delta.finish_reason:
                    got_any = True
                    yield {"type": "delta", "text": sanitize_user_ai_text(delta.text)}
                if delta.finish_reason:
                    if delta.reasoning_text:
                        yield {
                            "type": "reasoning_delta",
                            "text": sanitize_user_ai_text(delta.reasoning_text),
                        }
                    if delta.text:
                        yield {"type": "delta", "text": sanitize_user_ai_text(delta.text)}
                    status = classify_status(ctx, ai_available=True)
                    yield {
                        "type": "done",
                        "finish_reason": delta.finish_reason,
                        "status": status,
                    }
                    return
            # 流没拿到任何 delta 也没显式 finish_reason → 降级
            if not got_any:
                yield {"type": "delta", "text": sanitize_user_ai_text(_degraded_explanation(ctx))}
            yield {"type": "done", "finish_reason": "stop", "status": "degraded"}
        except Exception as e:  # noqa: BLE001
            logger.warning("ai_explain_stream_degraded: %s", e)
            yield {"type": "delta", "text": sanitize_user_ai_text(_degraded_explanation(ctx))}
            yield {"type": "done", "finish_reason": "stop", "status": "degraded"}

    async def chat(self, req: ChatRequest) -> ChatResponseMessage:
        """通过 Orchestrator 跑完整对话(含工具调度循环)."""
        if not req.messages:
            raise AiEmptyMessagesException()

        max_turns = settings.ai_history_turns
        history = req.messages[-max_turns:] if len(req.messages) > max_turns else req.messages
        user_msgs = [ChatMessage(role=m.role, content=m.content) for m in history]

        try:
            if self._session is None:
                # 没有 DB session 时退到无工具的简单模式
                resp = await self._ai.chat(
                    messages=[ChatMessage(role="system", content=SYSTEM_PROMPT), *user_msgs]
                )
                return ChatResponseMessage(
                    content=sanitize_user_ai_text(resp.content),
                    model=settings.ai_model,
                    finish_reason=resp.finish_reason,
                    status="ok",
                )
            orch = AiOrchestrator(
                self._ai,
                session=self._session,
                tenant_id=req.tenant_id,
                context=req.context or None,
            )
            out = await orch.run(user_msgs)
            return ChatResponseMessage(
                content=out.content,
                model=settings.ai_model,
                finish_reason=out.finish_reason,
                status="ok",
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("ai_chat_degraded: %s", e)
            content = await self._build_local_chat_fallback(req, user_msgs)
            return ChatResponseMessage(
                content=content,
                model=settings.ai_model,
                finish_reason="stop",
                status="degraded",
            )

    async def chat_stream(self, req: ChatRequest) -> AsyncIterator[dict]:
        """流式 chat — yield orchestrator 事件 dict.

        与非流式 chat() 一致的预处理(降级/上下文/历史截断),最终通过 orchestrator.run_stream
        逐 event 输出。错误时 yield 一个 error 事件,再 yield done。
        """
        if not req.messages:
            raise AiEmptyMessagesException()

        max_turns = settings.ai_history_turns
        history = req.messages[-max_turns:] if len(req.messages) > max_turns else req.messages
        user_msgs = [ChatMessage(role=m.role, content=m.content) for m in history]

        try:
            if self._session is None:
                # 无 session — 直接走 ai_client.chat_stream(单轮,不调工具)
                msgs = [ChatMessage(role="system", content=SYSTEM_PROMPT), *user_msgs]
                async for delta in self._ai.chat_stream(messages=msgs):
                    if delta.reasoning_text and not delta.finish_reason:
                        yield {
                            "type": "reasoning_delta",
                            "text": sanitize_user_ai_text(delta.reasoning_text),
                        }
                    if delta.text and not delta.finish_reason:
                        yield {"type": "delta", "text": sanitize_user_ai_text(delta.text)}
                    if delta.finish_reason:
                        yield {
                            "type": "done",
                            "finish_reason": delta.finish_reason,
                            "tool_iterations": 0,
                        }
                        return
                return

            orch = AiOrchestrator(
                self._ai,
                session=self._session,
                tenant_id=req.tenant_id,
                context=req.context or None,
            )
            async for event in orch.run_stream(user_msgs):
                yield event
        except Exception as e:  # noqa: BLE001
            logger.warning("ai_chat_stream_degraded: %s", e)
            content = await self._build_local_chat_fallback(req, user_msgs)
            yield {"type": "delta", "text": sanitize_user_ai_text(content)}
            yield {
                "type": "done",
                "finish_reason": "stop",
                "tool_iterations": 0,
                "status": "degraded",
            }

    async def decision_card(self, req: DecisionCardRequest) -> DecisionCardResponse:
        """结构化 AI 决策卡片.

        这里不使用前端本地规则或 mock 数据。所有卡片都从后端服务读取最新
        calc_run_id、SKU 快照、节日、物流方式或规则数据后生成。
        """
        if self._session is None:
            return DecisionCardResponse(
                content="后端会话不可用，无法生成真实链路决策卡。",
                scenario=req.scenario,
                card={"type": "error", "message": "backend session unavailable"},
                status="degraded",
            )

        if req.scenario == "risk_queue":
            return await self._decision_risk_queue(req)
        if req.scenario == "sales_leaders":
            return await self._decision_sales_leaders(req)
        if req.scenario == "holiday_readiness":
            return await self._decision_holiday_readiness(req)
        if req.scenario == "plan_comparison":
            return await self._decision_plan_comparison(req)
        if req.scenario == "rule_impact":
            return await self._decision_rule_impact(req)
        if req.scenario == "single_sku_replenishment":
            return await self._decision_single_sku_replenishment(req)
        return DecisionCardResponse(
            content="暂不支持该决策场景。",
            scenario=req.scenario,
            card={"type": "error", "message": "unsupported scenario"},
            status="degraded",
        )

    async def _decision_risk_queue(self, req: DecisionCardRequest) -> DecisionCardResponse:
        ctx = req.context or {}
        dash_svc = DashboardService(self._dashboard_repo)
        snapshot = await dash_svc.snapshot(
            DashboardSnapshotRequest(
                tenant_id=req.tenant_id,
                mall_ids=ctx.get("mall_ids"),
                country_codes=ctx.get("country_codes"),
                owners=ctx.get("owners"),
            )
        )
        risk = await dash_svc.risk_queue(
            RiskQueueRequest(
                tenant_id=req.tenant_id,
                priorities=ctx.get("priorities"),
                mall_ids=ctx.get("mall_ids"),
                country_codes=ctx.get("country_codes"),
                limit=int(ctx.get("limit") or 30),
            )
        )
        rows = [
            {
                "id": str(r.listing_id),
                "listingId": r.listing_id,
                "mallId": r.mall_id,
                "mall_id": r.mall_id,
                "msku": r.msku,
                "sku": r.sku,
                "name": r.product_name,
                "store": r.store_name,
                "country": {"code": r.country_code} if r.country_code else None,
                "priority": r.priority,
                "fbaSellable": r.fba_sellable_days,
                "stockoutDate": r.stockout_date.isoformat() if r.stockout_date else None,
                "suggest": r.suggest_qty > 0,
                "suggestQty": r.suggest_qty,
                "suggestAmountBase": r.suggest_amount_base,
                "baseCurrency": r.base_currency,
            }
            for r in risk.rows
        ]
        action_items = [
            {"id": r["id"], "qty": r["suggestQty"]}
            for r in rows
            if int(r.get("suggestQty") or 0) > 0
        ][:50]
        card = {
            "type": "risk_queue",
            "scope": "global",
            "source": "backend",
            "calcRunId": snapshot.calc_run_id,
            "severity": "p1",
            "title": "高风险 SKU 队列",
            "summary": f"当前 {snapshot.risk_counts.p1} 个 P1，优先处理预计断货最近的 SKU。",
            "metrics": [
                {"label": "P1 紧急", "value": snapshot.risk_counts.p1, "unit": "个"},
                {"label": "7 天内断货", "value": snapshot.stockout_7_count, "unit": "个"},
                {"label": "建议采购", "value": snapshot.suggest_total_qty, "unit": "件"},
                {
                    "label": "预计采购额",
                    "value": snapshot.suggest_total_amount.base.amount,
                    "currency": snapshot.suggest_total_amount.base.currency,
                },
            ],
            "riskCounts": snapshot.risk_counts.model_dump(),
            "rows": rows[:6],
            "actionItems": action_items,
        }
        return DecisionCardResponse(
            content="已通过后端风险队列接口读取最新计算批次并生成高风险 SKU 队列。",
            scenario=req.scenario,
            card=card,
            calc_run_id=snapshot.calc_run_id,
        )

    async def _decision_sales_leaders(self, req: DecisionCardRequest) -> DecisionCardResponse:
        ctx = req.context or {}
        sku_svc = SkuService(self._sku_repo, self._dashboard_repo)
        page = await sku_svc.list_skus(
            SkuListRequest(
                tenant_id=req.tenant_id,
                mall_ids=ctx.get("mall_ids"),
                country_codes=ctx.get("country_codes"),
                tags=ctx.get("tags"),
                page=1,
                page_size=200,
                sort_by="priority",
            )
        )
        candidates = [
            s for s in page.rows
            if (s.sales_7d or 0) > 0 or (s.future_daily or 0) > 0
        ]
        scored = []
        for s in candidates:
            sales_7d = float(s.sales_7d or 0)
            future_daily = float(s.future_daily or 0)
            fba_days = float(s.fba_sellable_days or 0)
            margin = float(s.gross_margin or 0)
            stock_penalty = 0.65 if fba_days < 7 else 0.85 if fba_days < 15 else 1.0
            margin_bonus = 1.12 if margin >= 0.2 else 1.0 if margin >= 0 else 0.65
            score = (sales_7d * 0.65 + future_daily * 7 * 0.35) * stock_penalty * margin_bonus
            scored.append((score, s))
        scored.sort(
            key=lambda item: (
                -item[0],
                -(item[1].sales_7d or 0),
                -(item[1].future_daily or 0),
            )
        )
        leaders = scored[:6]
        rows = [_sales_leader_row(s, score) for score, s in leaders]
        total_sales = sum(int(s.sales_7d or 0) for _, s in scored)
        leader_sales = sum(int(r.get("sales7d") or 0) for r in rows)
        push_ready = sum(1 for r in rows if r.get("recommendation") in {"重点推广", "优先加码"})
        calc_run_id = leaders[0][1].calc_run_id if leaders else await self._dashboard_repo.latest_calc_run_id(req.tenant_id)
        card = {
            "type": "sales_leaders",
            "scope": "global",
            "source": "backend",
            "calcRunId": calc_run_id,
            "severity": "p3",
            "title": "销量领先 SKU 与主推建议",
            "summary": f"基于全部 {page.total} 个 SKU,按近 7 天销量、预测日销、库存可支撑性和毛利筛选主推对象。",
            "metrics": [
                {"label": "参与 SKU", "value": page.total, "unit": "个"},
                {"label": "近7天总销量", "value": total_sales, "unit": "件"},
                {"label": "Top SKU销量", "value": leader_sales, "unit": "件"},
                {"label": "可直接主推", "value": push_ready, "unit": "个"},
            ],
            "evidence": [
                {"label": "排序口径", "value": "近7天销量 + 预测日销 + 库存 + 毛利"},
                {"label": "库存约束", "value": "FBA 可售不足 7 天不直接加码"},
                {"label": "推荐原则", "value": "热卖且库存健康优先,高风险先补货"},
            ],
            "rows": rows,
            "actionItems": [{"id": r["id"], "qty": r["suggestQty"]} for r in rows if r.get("suggest")],
        }
        return DecisionCardResponse(
            content="已基于全部 SKU 快照生成销量领先 SKU 与主推建议。",
            scenario=req.scenario,
            card=card,
            calc_run_id=calc_run_id,
        )

    async def _decision_holiday_readiness(self, req: DecisionCardRequest) -> DecisionCardResponse:
        ctx = req.context or {}
        dash_svc = DashboardService(self._dashboard_repo)
        holidays = await dash_svc.holidays(
            HolidaysRequest(
                tenant_id=req.tenant_id,
                country_code=ctx.get("country_code"),
            )
        )
        snapshot = await dash_svc.snapshot(DashboardSnapshotRequest(tenant_id=req.tenant_id))
        today = snapshot.as_of.date()
        def _holiday_date(v: str) -> date:
            return date.fromisoformat(v)
        future = [
            h for h in holidays.holidays
            if h.peak_date and _holiday_date(h.peak_date) >= today
        ]
        future.sort(key=lambda h: _holiday_date(h.peak_date))
        holiday = future[0] if future else None

        sku_svc = SkuService(self._sku_repo, self._dashboard_repo)
        page = await sku_svc.list_skus(
            SkuListRequest(
                tenant_id=req.tenant_id,
                country_codes=[holiday.country_code] if holiday and holiday.country_code else None,
                page=1,
                page_size=50,
            )
        )
        tagged_skus = [s for s in page.rows if _sku_matches_holiday_tag(holiday, s)]
        tagged_skus.sort(
            key=lambda s: (
                {"p1": 0, "p2": 1, "p3": 2, "safe": 3}.get(s.priority, 9),
                s.stockout_date or date.max,
            )
        )
        rows = [_sku_card_row(s) for s in tagged_skus[:6]]
        multiplier = float(holiday.sales_multiplier) if holiday else 1.0
        base_demand = sum(float(s.get("coverageDemand") or 0) for s in rows)
        promo_demand = base_demand * multiplier
        total_stock = sum(float(s.get("totalStock") or 0) for s in rows)
        gap = max(0, promo_demand - total_stock)
        suggest_qty = sum(int(s.get("suggestQty") or 0) for s in rows if s.get("suggest"))
        holiday_peak = _holiday_date(holiday.peak_date) if holiday else None
        days_until = (holiday_peak - today).days if holiday_peak else None
        card = {
            "type": "holiday_readiness",
            "scope": "global",
            "source": "backend",
            "calcRunId": snapshot.calc_run_id,
            "severity": "p2" if days_until is not None and days_until <= 14 else "p3",
            "title": f"{holiday.flag or ''} {holiday.name}" if holiday else "大促备货",
            "summary": (
                f"{holiday.name} 距离 {max(0, days_until or 0)} 天，当前通过标签关联 {len(tagged_skus)} 个 SKU。"
                if holiday else "当前暂无已配置的大促节点。"
            ),
            "holiday": holiday.model_dump(mode="json") if holiday else None,
            "metrics": [
                {"label": "倒计时", "value": max(0, days_until) if days_until is not None else "—", "unit": "天" if days_until is not None else ""},
                {"label": "关联 SKU", "value": len(tagged_skus), "unit": "个"},
                {"label": "销量系数", "value": f"{multiplier:.2f}".rstrip("0").rstrip("."), "prefix": "×"},
                {"label": "建议采购", "value": suggest_qty or math.ceil(gap), "unit": "件"},
            ],
            "evidence": [
                {"label": "活动覆盖需求", "value": f"{promo_demand:.2f} 件"},
                {"label": "当前总库存", "value": f"{total_stock:.0f} 件"},
                {"label": "活动缺口", "value": f"{gap:.2f} 件"},
                {"label": "峰值日期", "value": holiday.peak_date if holiday else "—"},
            ],
            "rows": rows,
            "actionItems": [{"id": s["id"], "qty": s["suggestQty"]} for s in rows if s.get("suggest")],
        }
        return DecisionCardResponse(
            content="已通过后端节日和 SKU 快照数据生成大促备货卡片。",
            scenario=req.scenario,
            card=card,
            calc_run_id=snapshot.calc_run_id,
        )

    async def _decision_plan_comparison(self, req: DecisionCardRequest) -> DecisionCardResponse:
        from sqlalchemy import select
        from supplyai.models.mk import MkRuleLogisticsMethod

        ctx = req.context or {}
        sku_svc = SkuService(self._sku_repo, self._dashboard_repo)
        listing_id = ctx.get("listing_id")
        if listing_id:
            detail = await sku_svc.detail(
                SkuDetailRequest(tenant_id=req.tenant_id, listing_id=int(listing_id))
            )
            summary = detail.summary
        else:
            page = await sku_svc.list_skus(
                SkuListRequest(
                    tenant_id=req.tenant_id,
                    priorities=["p1", "p2"],
                    page=1,
                    page_size=1,
                )
            )
            if not page.rows:
                raise SkuNotFoundException(0)
            summary = page.rows[0]

        methods = (
            await self._session.execute(
                select(MkRuleLogisticsMethod).where(MkRuleLogisticsMethod.is_active == 1)
            )
        ).scalars().all()
        if not methods:
            return DecisionCardResponse(
                content="未配置真实物流方式，无法生成方案对比。",
                scenario=req.scenario,
                card={"type": "error", "message": "缺少真实物流方式配置"},
                calc_run_id=summary.calc_run_id,
                status="partial",
            )

        qty = int(ctx.get("qty_target") or summary.suggest_qty or 0)
        if qty <= 0:
            qty = max(1, math.ceil(float(summary.coverage_demand or 0) - float(summary.total_stock or 0)))
        unit_cost = float(summary.suggest_amount_base or 0) / qty if qty > 0 and summary.suggest_amount_base else 0.0
        sellable_days = float(summary.fba_sellable_days or 0)
        fastest_days = min(int(m.logistics_days) for m in methods)
        options = []
        for m in sorted(methods, key=lambda x: (x.logistics_days, x.logistics_mode)):
            days = int(m.logistics_days)
            estimated_cost = round(qty * unit_cost, 2) if unit_cost else None
            gap = max(0, days - sellable_days)
            options.append(
                {
                    "key": str(m.id),
                    "name": m.logistics_mode,
                    "etaDays": days,
                    "amount": estimated_cost,
                    "gapDays": gap,
                    "risk": "高" if gap >= 14 else "中" if gap > 0 else "低",
                    "note": "按已配置物流方式测算",
                    "recommended": days == fastest_days if sellable_days <= 7 else gap == 0,
                }
            )
        if not any(o["recommended"] for o in options):
            options[0]["recommended"] = True
        recommended = next(o for o in options if o["recommended"])
        card = {
            "type": "plan_comparison",
            "scope": "sku" if listing_id else "global",
            "source": "backend",
            "calcRunId": summary.calc_run_id,
            "severity": "p2",
            "title": f"{summary.msku} 运输方案对比",
            "sku": _sku_card_row(summary),
            "recommended": recommended,
            "metrics": [
                {"label": "推荐方案", "value": recommended["name"]},
                {"label": "首批到货", "value": recommended["etaDays"], "unit": "天"},
                {"label": "缺货窗口", "value": round(recommended["gapDays"], 2), "unit": "天"},
                {"label": "建议采购", "value": qty, "unit": "件"},
            ],
            "evidence": [
                {"label": "FBA 可售", "value": f"{sellable_days:.2f} 天"},
                {"label": "预计断货", "value": summary.stockout_date.isoformat() if summary.stockout_date else "—"},
                {"label": "当前总库存", "value": f"{summary.total_stock or 0} 件"},
                {"label": "覆盖需求", "value": f"{float(summary.coverage_demand or 0):.2f} 件"},
            ],
            "options": options,
            "actionItems": [{"id": str(summary.id), "qty": qty}],
        }
        return DecisionCardResponse(
            content="已通过后端 SKU 快照和真实物流方式配置生成方案对比卡片。",
            scenario=req.scenario,
            card=card,
            calc_run_id=summary.calc_run_id,
        )

    async def _decision_rule_impact(self, req: DecisionCardRequest) -> DecisionCardResponse:
        ctx = req.context or {}
        target_safety_days = int(ctx.get("target_safety_days") or 21)
        sku_svc = SkuService(self._sku_repo, self._dashboard_repo)
        listing_id = ctx.get("listing_id")
        if listing_id:
            detail = await sku_svc.detail(
                SkuDetailRequest(tenant_id=req.tenant_id, listing_id=int(listing_id))
            )
            summaries = [detail.summary]
            scope = "sku"
        else:
            page = await sku_svc.list_skus(
                SkuListRequest(
                    tenant_id=req.tenant_id,
                    priorities=["p1", "p2"],
                    page=1,
                    page_size=int(ctx.get("limit") or 5),
                )
            )
            summaries = page.rows
            scope = "global"

        rows = [_rule_impact_row(s, target_safety_days=target_safety_days) for s in summaries]
        target = rows[0] if rows else None
        total_delta = sum(int(r["qtyDelta"]) for r in rows)
        current_safety = int(target["currentSafeDays"]) if target else 14
        action_text = "提高" if target_safety_days > current_safety else "降低" if target_safety_days < current_safety else "保持"
        calc_run_id = summaries[0].calc_run_id if summaries else None
        card = {
            "type": "rule_impact",
            "scope": scope,
            "source": "backend",
            "calcRunId": calc_run_id,
            "severity": "p3",
            "title": f"安全天数 {target_safety_days} 天规则影响",
            "sku": target,
            "targetSafeDays": target_safety_days,
            "actionText": action_text,
            "metrics": [
                {"label": "安全天数", "value": f"{current_safety} → {target_safety_days}", "unit": "天"},
                {"label": "采购量变化", "value": f"+{total_delta}" if total_delta >= 0 else str(total_delta), "unit": "件"},
                {"label": "影响 SKU", "value": len(rows), "unit": "个"},
                {"label": "主 SKU 新采购", "value": int(target["nextSuggestQty"]) if target else 0, "unit": "件"},
            ],
            "evidence": [
                {"label": "主 SKU", "value": target["msku"] if target else "—"},
                {"label": "未来日销", "value": f"{float(target['futureDaily'] or 0):.2f} 件/天" if target else "—"},
                {
                    "label": "覆盖需求",
                    "value": (
                        f"{float(target['coverageDemand'] or 0):.2f} → "
                        f"{float(target['nextCoverageDemand'] or 0):.2f} 件"
                    ) if target else "—",
                },
                {"label": "风险等级", "value": f"{str(target['priority']).upper()} · 应用后需重新计算" if target else "—"},
            ],
            "rows": rows,
        }
        return DecisionCardResponse(
            content="已通过后端最新计算批次和规则参数生成安全天数影响卡片。",
            scenario=req.scenario,
            card=card,
            calc_run_id=calc_run_id,
        )

    async def _decision_single_sku_replenishment(self, req: DecisionCardRequest) -> DecisionCardResponse:
        ctx = req.context or {}
        listing_id = ctx.get("listing_id")
        sku_svc = SkuService(self._sku_repo, self._dashboard_repo)
        if listing_id:
            detail = await sku_svc.detail(
                SkuDetailRequest(tenant_id=req.tenant_id, listing_id=int(listing_id))
            )
            s = detail.summary
        else:
            page = await sku_svc.list_skus(
                SkuListRequest(
                    tenant_id=req.tenant_id,
                    priorities=["p1", "p2"],
                    suggest_only=True,
                    page=1,
                    page_size=1,
                )
            )
            if not page.rows:
                raise SkuNotFoundException(0)
            s = page.rows[0]

        content = (
            f"该 SKU 处于 {s.priority.upper()} 风险，FBA 可售仅 {float(s.fba_sellable_days or 0):.2f} 天，"
            f"预计于 {s.stockout_date.isoformat() if s.stockout_date else '—'} 断货。\n"
            f"基于全链路库存计算，建议采购 {int(s.suggest_qty or 0)} 件以覆盖 "
            f"{float(s.coverage_demand or 0):.2f} 件的覆盖周期需求。\n"
            f"请在前端确认采购计划：SKU {s.msku}，数量 {int(s.suggest_qty or 0)} 件，供应商待补充。"
        )
        return DecisionCardResponse(
            content=content,
            scenario=req.scenario,
            card={"type": "risk_advice", "source": "backend", "calcRunId": s.calc_run_id},
            calc_run_id=s.calc_run_id,
        )
