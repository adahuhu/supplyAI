"""AI 编排服务 — 解释单 SKU + 通用对话."""
from __future__ import annotations

import logging
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.config import settings
from supplyai.domain.ai.client import AiClient, ChatMessage
from supplyai.domain.ai.foundation import (
    SYSTEM_PROMPT,
    build_explain_prompt,
    classify_status,
)
from supplyai.domain.ai.orchestrator import AiOrchestrator
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.repositories.sku_repo import SkuRepository
from supplyai.schemas.ai import (
    ChatRequest,
    ChatResponseMessage,
    ExplainRequest,
    ExplainResponse,
)
from supplyai.services.sku_service import _row_to_dto
from supplyai.utils.exceptions import (
    AiEmptyMessagesException,
    CalcRunNotFoundException,
    SkuNotFoundException,
)

logger = logging.getLogger(__name__)


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
            explanation = chat_resp.content
        except Exception as e:  # noqa: BLE001
            logger.warning("ai_explain_degraded: %s", e)
            ai_available = False
            explanation = _degraded_explanation(ctx)

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
                if delta.text and not delta.finish_reason:
                    got_any = True
                    yield {"type": "delta", "text": delta.text}
                if delta.finish_reason:
                    status = classify_status(ctx, ai_available=True)
                    yield {
                        "type": "done",
                        "finish_reason": delta.finish_reason,
                        "status": status,
                    }
                    return
            # 流没拿到任何 delta 也没显式 finish_reason → 降级
            if not got_any:
                yield {"type": "delta", "text": _degraded_explanation(ctx)}
            yield {"type": "done", "finish_reason": "stop", "status": "degraded"}
        except Exception as e:  # noqa: BLE001
            logger.warning("ai_explain_stream_degraded: %s", e)
            yield {"type": "delta", "text": _degraded_explanation(ctx)}
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
                    content=resp.content,
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
            return ChatResponseMessage(
                content="[降级] AI 服务暂不可用,请稍后重试或查看结构化数据。",
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
                    if delta.text and not delta.finish_reason:
                        yield {"type": "delta", "text": delta.text}
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
            yield {"type": "error", "message": str(e)}
            yield {"type": "done", "finish_reason": "stop", "tool_iterations": 0}
