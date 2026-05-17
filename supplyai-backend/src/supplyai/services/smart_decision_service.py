"""Smart Decision 编排 — 分类 → 卡片 → LLM 解释 → 退化 chat."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, AsyncIterator

from supplyai.config import settings
from supplyai.domain.ai.client import AiClient, ChatMessage
from supplyai.schemas.ai import (
    ChatRequest,
    DecisionCardRequest,
    DecisionCardResponse,
    DecisionScenario,
    SmartDecisionRequest,
)
from supplyai.services.ai_service import AiService

logger = logging.getLogger(__name__)

SCENARIO_PATTERNS: dict[str, re.Pattern] = {
    "single_sku_replenishment": re.compile(r"挑一个|单个SKU|还能卖多久|要不要补"),
    "risk_queue": re.compile(r"高风险|必须补货|紧急度|风险队列|优先级"),
    "holiday_readiness": re.compile(r"大促|节日|Prime|活动备货|母亲节|黑五|圣诞"),
    "plan_comparison": re.compile(r"方案对比|海运|空运|海空|海\+空|混合"),
    "rule_impact": re.compile(r"规则模拟|安全天数|改成|调整|规则影响"),
}

CLASSIFY_SYSTEM_PROMPT = (
    "你是意图分类器。用户问题属于以下哪个场景？只返回场景名，不解释。\n"
    "- risk_queue: 查看风险SKU、补货优先级、断货排序\n"
    "- holiday_readiness: 大促备货、节日缺口、活动准备\n"
    "- plan_comparison: 运输方案比较、海运空运对比、物流成本\n"
    "- rule_impact: 规则参数调整影响、安全天数变化\n"
    "- single_sku_replenishment: 单个SKU补货建议\n"
    "- none: 以上都不是"
)

VALID_SCENARIOS: set[str] = {
    "risk_queue",
    "holiday_readiness",
    "plan_comparison",
    "rule_impact",
    "single_sku_replenishment",
}

CARD_EXPLAIN_PROMPT = (
    "你是供应链分析师。基于以下决策卡片数据，用 2-3 句话解释：\n"
    "1. 当前最紧急的风险是什么\n"
    "2. 为什么建议这样处理\n"
    "3. 有什么需要注意的\n"
    "简洁直接，不要重复数据本身，重点是归因和建议。"
)

LLM_CLASSIFY_TIMEOUT = 3.0


class SmartDecisionService:
    """编排分类 → 卡片 → 解释 → 退化 chat."""

    def __init__(
        self,
        ai_client: AiClient,
        ai_service: AiService,
    ) -> None:
        self._ai_client = ai_client
        self._ai_service = ai_service

    def _classify_regex(self, text: str) -> tuple[str | None, str]:
        """第一级:正则匹配,0ms."""
        for scenario, pattern in SCENARIO_PATTERNS.items():
            if pattern.search(text):
                return scenario, "regex"
        return None, ""

    async def _classify_llm(self, text: str) -> tuple[str | None, str]:
        """第二级:LLM 轻量分类,max_tokens=20,3s 超时."""
        try:
            resp = await asyncio.wait_for(
                self._ai_client.chat(
                    messages=[
                        ChatMessage(role="system", content=CLASSIFY_SYSTEM_PROMPT),
                        ChatMessage(role="user", content=text),
                    ],
                    max_tokens=20,
                    temperature=0,
                ),
                timeout=LLM_CLASSIFY_TIMEOUT,
            )
            scenario = resp.content.strip().lower().replace('"', "").replace("'", "")
            if scenario in VALID_SCENARIOS:
                return scenario, "llm"
        except (asyncio.TimeoutError, Exception) as e:  # noqa: BLE001
            logger.warning("smart_decision_classify_fallback: %s", e)
        return None, ""

    async def _classify(self, text: str) -> tuple[str | None, str]:
        """两级分类:正则优先,未命中走 LLM."""
        scenario, method = self._classify_regex(text)
        if scenario:
            return scenario, method
        return await self._classify_llm(text)

    def _build_card_summary(self, resp: DecisionCardResponse) -> str:
        """将卡片 JSON 压缩为 200-400 字文本摘要."""
        card = resp.card
        card_type = card.get("type", "")

        if card_type == "risk_queue":
            rc = card.get("riskCounts", {})
            rows_desc = "; ".join(
                f'{r["msku"]}({r.get("priority","?")}, 可售{r.get("fbaSellable","?")}天, 建议采购{r.get("suggestQty","?")}件)'
                for r in card.get("rows", [])[:6]
            )
            return (
                f'风险队列: P1={rc.get("p1",0)}个, P2={rc.get("p2",0)}个, '
                f'P3={rc.get("p3",0)}个, 安全={rc.get("safe",0)}个. '
                f"Top SKU: {rows_desc}"
            )

        if card_type == "holiday_readiness":
            metrics = {m["label"]: m.get("value", "") for m in card.get("metrics", [])}
            rows_desc = "; ".join(
                f'{r["msku"]}({r.get("priority","?")})'
                for r in card.get("rows", [])[:6]
            )
            return (
                f'大促备货 · {card.get("title","")}: '
                f'倒计时{metrics.get("倒计时","")}天, '
                f'关联SKU {metrics.get("关联 SKU","")}个, '
                f'建议采购{metrics.get("建议采购","")}件. '
                f"关联SKU: {rows_desc}"
            )

        if card_type == "plan_comparison":
            options_desc = "; ".join(
                f'{o["name"]}({o.get("etaDays","")}天, 风险{o.get("risk","")}'
                f'{", 推荐" if o.get("recommended") else ""})'
                for o in card.get("options", [])
            )
            return f'方案对比 · {card.get("title","")}: {options_desc}'

        if card_type == "rule_impact":
            metrics = {m["label"]: m.get("value", "") for m in card.get("metrics", [])}
            return (
                f'规则影响 · {card.get("title","")}: '
                f'安全天数{metrics.get("安全天数","")}, '
                f'采购量变化{metrics.get("采购量变化","")}件, '
                f'影响SKU {metrics.get("影响 SKU","")}个'
            )

        return resp.content or str(card)[:400]

    async def stream(self, req: SmartDecisionRequest) -> AsyncIterator[dict]:
        """主流程:分类 → 卡片 → 解释 → 退化 chat."""
        if not req.messages:
            yield {"type": "error", "message": "messages 不能为空"}
            yield {"type": "done", "finish_reason": "stop"}
            return

        text = req.messages[-1].content

        # 多轮对话(有 assistant 回复)视为追问,跳过场景分类直接走 chat
        has_prior_context = any(m.role == "assistant" for m in req.messages)
        scenario: str | None = None
        method = ""
        if not has_prior_context:
            scenario, method = await self._classify(text)

        if scenario:
            yield {"type": "classify", "scenario": scenario, "method": method}

            ctx = dict(req.context) if req.context else {}
            try:
                card_resp = await self._ai_service.decision_card(
                    DecisionCardRequest(
                        tenant_id=req.tenant_id,
                        scenario=scenario,  # type: ignore[arg-type]
                        context=ctx,
                    )
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("smart_decision_card_failed: %s", e)
                yield {"type": "error", "message": str(e)}
                async for event in self._ai_service.chat_stream(req.to_chat_request()):
                    yield event
                return

            summary = self._build_card_summary(card_resp)
            yield {
                "type": "card",
                "scenario": scenario,
                "card": card_resp.card,
                "summary": summary,
            }

            if settings.card_explain:
                try:
                    explain_msgs = [
                        ChatMessage(role="system", content=CARD_EXPLAIN_PROMPT),
                        ChatMessage(role="user", content=summary),
                    ]
                    async for delta in self._ai_client.chat_stream(
                        messages=explain_msgs,
                        max_tokens=settings.ai_max_output_tokens,
                    ):
                        if delta.reasoning_text and not delta.finish_reason:
                            yield {"type": "reasoning_delta", "text": delta.reasoning_text}
                        if delta.text and not delta.finish_reason:
                            yield {"type": "delta", "text": delta.text}
                        if delta.finish_reason:
                            if delta.reasoning_text:
                                yield {"type": "reasoning_delta", "text": delta.reasoning_text}
                            if delta.text:
                                yield {"type": "delta", "text": delta.text}
                            yield {
                                "type": "done",
                                "finish_reason": delta.finish_reason,
                                "scenario": scenario,
                            }
                            return
                except Exception as e:  # noqa: BLE001
                    logger.warning("smart_decision_explain_failed: %s", e)

            yield {"type": "done", "finish_reason": "stop", "scenario": scenario}
            return

        async for event in self._ai_service.chat_stream(req.to_chat_request()):
            yield event
