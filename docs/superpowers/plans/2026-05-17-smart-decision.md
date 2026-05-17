# Smart Decision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify AI decision cards and LLM explanations into a single streaming endpoint with two-tier intent classification, card data in chat context, and configurable post-card LLM explanation.

**Architecture:** New `POST /ai/smart-decision/stream` SSE endpoint backed by `SmartDecisionService`. Two-tier classification (regex → LLM fallback) routes to existing `AiService.decision_card()`, then optionally streams LLM explanation. Unmatched intents fall through to existing `AiService.chat_stream()`. Frontend replaces per-panel regex routing with a single `aiSmartDecisionStream` call.

**Tech Stack:** Python 3.13 / FastAPI / Pydantic / SQLAlchemy async / SSE / React 18 (Babel-in-browser)

**Spec:** `docs/superpowers/specs/2026-05-17-smart-decision-design.md`

---

### Task 1: Add `card_explain` config + env

**Files:**
- Modify: `supplyai-backend/src/supplyai/config.py:80-83`
- Modify: `supplyai-backend/env.example:81`

- [ ] **Step 1: Add `card_explain` field to Settings**

In `supplyai-backend/src/supplyai/config.py`, after `dashscope_enable_thinking` (line ~83), add:

```python
    # 决策卡片后是否追加 LLM 流式解释 — 默认 true
    # - true:  卡片渲染后,LLM 异步生成 2-3 句归因解释
    # - false: 出卡即止,与旧版行为一致
    card_explain: bool = Field(
        default=True,
        validation_alias=AliasChoices("SUPPLY_CARD_EXPLAIN", "card_explain"),
    )
```

- [ ] **Step 2: Add to env.example**

In `supplyai-backend/env.example`, after the `SUPPLY_DASH_ENABLE_THINKING` block (line ~81), add:

```dotenv

# 决策卡片解释开关 — 默认 true
# - true:  场景卡片渲染后,LLM 自动追加 2-3 句归因解释(流式)
# - false: 出卡即止,不调 LLM 解释(与旧版行为一致,省 token)
SUPPLY_CARD_EXPLAIN=true
```

- [ ] **Step 3: Verify config loads**

Run: `cd supplyai-backend && uv run python -c "from supplyai.config import settings; print(f'card_explain={settings.card_explain}')"`

Expected: `card_explain=True`

- [ ] **Step 4: Commit**

```bash
git add supplyai-backend/src/supplyai/config.py supplyai-backend/env.example
git commit -m "feat: add SUPPLY_CARD_EXPLAIN config for post-card LLM explanation toggle"
```

---

### Task 2: Add `SmartDecisionRequest` schema

**Files:**
- Modify: `supplyai-backend/src/supplyai/schemas/ai.py`

- [ ] **Step 1: Add SmartDecisionRequest to schemas/ai.py**

At the end of `supplyai-backend/src/supplyai/schemas/ai.py`, add:

```python
class SmartDecisionRequest(BaseModel):
    """POST /ai/smart-decision/stream 请求体 — 与 ChatRequest 格式一致."""

    tenant_id: int
    messages: list[ChatRequestMessage] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)

    def to_chat_request(self) -> ChatRequest:
        """退化到 chat 时,直接转换为 ChatRequest."""
        return ChatRequest(
            tenant_id=self.tenant_id,
            messages=self.messages,
            context=self.context,
        )
```

- [ ] **Step 2: Verify import**

Run: `cd supplyai-backend && uv run python -c "from supplyai.schemas.ai import SmartDecisionRequest; print('OK')"`

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add supplyai-backend/src/supplyai/schemas/ai.py
git commit -m "feat: add SmartDecisionRequest schema"
```

---

### Task 3: Create SmartDecisionService with tests (TDD)

**Files:**
- Create: `supplyai-backend/src/supplyai/services/smart_decision_service.py`
- Create: `supplyai-backend/tests/test_smart_decision.py`

- [ ] **Step 1: Write failing tests**

Create `supplyai-backend/tests/test_smart_decision.py`:

```python
"""SmartDecisionService 测试 — 分类 + 卡片 + 解释 + 退化."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from supplyai.domain.ai.client import ChatMessage, ChatResponse, StreamDelta
from supplyai.schemas.ai import ChatRequestMessage, SmartDecisionRequest
from supplyai.services.smart_decision_service import SmartDecisionService

TENANT = 100228


def _make_req(text: str) -> SmartDecisionRequest:
    return SmartDecisionRequest(
        tenant_id=TENANT,
        messages=[ChatRequestMessage(role="user", content=text)],
    )


async def _collect(service: SmartDecisionService, req: SmartDecisionRequest) -> list[dict]:
    return [ev async for ev in service.stream(req)]


# ── 分类测试 ────────────────────────────────

class TestClassify:
    """两级分类:正则优先,LLM 兜底."""

    def test_regex_hits_risk_queue(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("哪些SKU必须补货")
        assert scenario == "risk_queue"
        assert method == "regex"

    def test_regex_hits_holiday(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("大促要备哪些货")
        assert scenario == "holiday_readiness"
        assert method == "regex"

    def test_regex_hits_plan_comparison(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("海运和空运对比")
        assert scenario == "plan_comparison"
        assert method == "regex"

    def test_regex_hits_rule_impact(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("安全天数改成21天")
        assert scenario == "rule_impact"
        assert method == "regex"

    def test_regex_hits_single_sku(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("挑一个高风险SKU")
        assert scenario == "single_sku_replenishment"
        assert method == "regex"

    def test_regex_misses(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("哪些货快卖完了")
        assert scenario is None

    @pytest.mark.asyncio
    async def test_llm_classify_returns_scenario(self):
        """LLM 分类返回有效 scenario."""
        mock_client = AsyncMock()
        mock_client.chat.return_value = ChatResponse(content="risk_queue", finish_reason="stop")
        svc = SmartDecisionService.__new__(SmartDecisionService)
        svc._ai_client = mock_client
        scenario, method = await svc._classify_llm("哪些货快卖完了")
        assert scenario == "risk_queue"
        assert method == "llm"

    @pytest.mark.asyncio
    async def test_llm_classify_returns_none(self):
        """LLM 返回 none → 未命中."""
        mock_client = AsyncMock()
        mock_client.chat.return_value = ChatResponse(content="none", finish_reason="stop")
        svc = SmartDecisionService.__new__(SmartDecisionService)
        svc._ai_client = mock_client
        scenario, method = await svc._classify_llm("你好")
        assert scenario is None

    @pytest.mark.asyncio
    async def test_llm_classify_timeout_returns_none(self):
        """LLM 超时 → 视为 none."""
        mock_client = AsyncMock()
        mock_client.chat.side_effect = asyncio.TimeoutError()
        svc = SmartDecisionService.__new__(SmartDecisionService)
        svc._ai_client = mock_client
        scenario, method = await svc._classify_llm("哪些货快卖完了")
        assert scenario is None


# ── 流式编排测试 ────────────────────────────

class TestStream:
    """完整流式编排:分类 → 卡片 → 解释 → done."""

    @pytest.mark.asyncio
    async def test_regex_hit_with_explain(self, client):
        """正则命中 → classify + card + delta(解释) + done."""
        req = _make_req("哪些SKU必须补货?按紧急度排序")
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        assert resp.status_code == 200
        events = _parse_sse(resp.text)
        types = [e["type"] for e in events]
        assert "classify" in types
        assert "card" in types
        assert "done" in types
        classify_ev = next(e for e in events if e["type"] == "classify")
        assert classify_ev["scenario"] == "risk_queue"
        assert classify_ev["method"] == "regex"
        card_ev = next(e for e in events if e["type"] == "card")
        assert card_ev["card"]["type"] == "risk_queue"
        assert "summary" in card_ev
        assert len(card_ev["summary"]) > 20

    @pytest.mark.asyncio
    async def test_card_explain_off(self, client, monkeypatch):
        """card_explain=false → classify + card + done, 无 delta."""
        monkeypatch.setattr("supplyai.services.smart_decision_service.settings.card_explain", False)
        req = _make_req("风险队列")
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        events = _parse_sse(resp.text)
        types = [e["type"] for e in events]
        assert "classify" in types
        assert "card" in types
        assert "done" in types
        assert "delta" not in types

    @pytest.mark.asyncio
    async def test_no_scenario_falls_through_to_chat(self, client):
        """两级都未命中 → 退化到 chat(无 classify/card)."""
        req = _make_req("你好,请自我介绍")
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        events = _parse_sse(resp.text)
        types = [e["type"] for e in events]
        assert "classify" not in types
        assert "card" not in types
        assert "delta" in types
        assert "done" in types

    @pytest.mark.asyncio
    async def test_card_summary_in_history_enables_followup(self, client):
        """追问:带 summary 的 history → LLM 能引用卡片内容."""
        req = SmartDecisionRequest(
            tenant_id=TENANT,
            messages=[
                ChatRequestMessage(role="user", content="风险队列"),
                ChatRequestMessage(role="assistant", content="风险队列: P1=12个, Top SKU: MS40060(p1)"),
                ChatRequestMessage(role="user", content="第一个为什么是P1"),
            ],
        )
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        events = _parse_sse(resp.text)
        types = [e["type"] for e in events]
        # 追问不匹配场景,走 chat
        assert "delta" in types
        assert "done" in types


def _parse_sse(text: str) -> list[dict]:
    """解析 SSE 文本为 event list."""
    import json
    events = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd supplyai-backend && uv run pytest tests/test_smart_decision.py -v 2>&1 | head -30`

Expected: ImportError or ModuleNotFoundError for `smart_decision_service`

- [ ] **Step 3: Create SmartDecisionService**

Create `supplyai-backend/src/supplyai/services/smart_decision_service.py`:

```python
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
    "risk_queue": re.compile(r"高风险|必须补货|紧急度|风险队列|优先级"),
    "holiday_readiness": re.compile(r"大促|节日|Prime|活动备货|母亲节|黑五|圣诞"),
    "plan_comparison": re.compile(r"方案对比|海运|空运|海空|海\+空|混合"),
    "rule_impact": re.compile(r"规则模拟|安全天数|改成|调整|规则影响"),
    "single_sku_replenishment": re.compile(r"挑一个|单个SKU|还能卖多久|要不要补"),
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

    # ── 分类 ──────────────────────────────

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

    # ── 卡片摘要 ──────────────────────────

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
            return (
                f'方案对比 · {card.get("title","")}: {options_desc}'
            )

        if card_type == "rule_impact":
            metrics = {m["label"]: m.get("value", "") for m in card.get("metrics", [])}
            return (
                f'规则影响 · {card.get("title","")}: '
                f'安全天数{metrics.get("安全天数","")}, '
                f'采购量变化{metrics.get("采购量变化","")}件, '
                f'影响SKU {metrics.get("影响 SKU","")}个'
            )

        # single_sku_replenishment 和其他 fallback
        return resp.content or str(card)[:400]

    # ── 流式编排 ──────────────────────────

    async def stream(self, req: SmartDecisionRequest) -> AsyncIterator[dict]:
        """主流程:分类 → 卡片 → 解释 → 退化 chat."""
        if not req.messages:
            yield {"type": "error", "message": "messages 不能为空"}
            yield {"type": "done", "finish_reason": "stop"}
            return

        text = req.messages[-1].content
        scenario, method = await self._classify(text)

        if scenario:
            yield {"type": "classify", "scenario": scenario, "method": method}

            # 生成卡片
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
                # 退化到 chat
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

            # LLM 解释(受开关控制)
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

        # 未命中场景 — 退化到 Orchestrator chat
        async for event in self._ai_service.chat_stream(req.to_chat_request()):
            yield event
```

- [ ] **Step 4: Run classify tests (unit tests, no DB needed)**

Run: `cd supplyai-backend && uv run pytest tests/test_smart_decision.py::TestClassify -v`

Expected: All 9 classify tests PASS

- [ ] **Step 5: Add smart-decision/stream route**

In `supplyai-backend/src/supplyai/api/v1/ai.py`, add import and route:

At the top, add to imports:

```python
from supplyai.schemas.ai import (
    ChatRequest,
    ChatResponseMessage,
    DecisionCardRequest,
    DecisionCardResponse,
    ExplainRequest,
    ExplainResponse,
    SmartDecisionRequest,
)
from supplyai.services.smart_decision_service import SmartDecisionService
```

After the existing `ai_chat_stream` route, add:

```python
def _build_smart_service(session: AsyncSession) -> SmartDecisionService:
    return SmartDecisionService(
        ai_client=get_ai_client(),
        ai_service=_build_service(session),
    )


@router.post("/smart-decision/stream")
async def ai_smart_decision_stream(
    req: SmartDecisionRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Smart Decision — 分类 + 卡片 + LLM 解释 统一 SSE 流.

    事件:
      data: {"type":"classify","scenario":"...","method":"regex"|"llm"}
      data: {"type":"card","scenario":"...","card":{...},"summary":"..."}
      data: {"type":"delta","text":"..."}
      data: {"type":"done","finish_reason":"stop","scenario":"..."}
    未命中场景时退化到 chat(tool_start/tool_end/delta/done).
    """
    svc = _build_smart_service(session)

    async def event_gen():
        try:
            async for event in svc.stream(req):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        finally:
            try:
                await session.commit()
            except Exception:  # noqa: BLE001
                pass

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

- [ ] **Step 6: Patch conftest for smart_decision_service import**

In `supplyai-backend/tests/conftest.py`, the existing `_patch_ai_factory` patches `supplyai.api.v1.ai.get_ai_client`. The new route also calls `get_ai_client`, so the existing patch already covers it (both `_build_service` and `_build_smart_service` call the module-level `get_ai_client`). No change needed.

- [ ] **Step 7: Run full stream tests**

Run: `cd supplyai-backend && uv run pytest tests/test_smart_decision.py -v`

Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add supplyai-backend/src/supplyai/services/smart_decision_service.py \
       supplyai-backend/src/supplyai/api/v1/ai.py \
       supplyai-backend/tests/test_smart_decision.py
git commit -m "feat: add SmartDecisionService with two-tier classify + card + explain stream"
```

---

### Task 4: Frontend — add `aiSmartDecisionStream` to api.jsx

**Files:**
- Modify: `SupplyAI/api.jsx`

- [ ] **Step 1: Add aiSmartDecisionStream method**

In `SupplyAI/api.jsx`, after the existing `aiChatStream` method (around line 198), add:

```javascript
    /**
     * Smart Decision 流(/ai/smart-decision/stream).
     * 事件类型:classify / card / reasoning_delta / delta / tool_start / tool_end / done / error
     */
    aiSmartDecisionStream(messages, context, onEvent) {
      const body = { tenant_id: TENANT_ID, messages };
      if (context) body.context = context;
      return streamSSE('/ai/smart-decision/stream', body, onEvent);
    },
```

- [ ] **Step 2: Commit**

```bash
git add SupplyAI/api.jsx
git commit -m "feat: add aiSmartDecisionStream to frontend API layer"
```

---

### Task 5: Frontend — rewire GlobalAIPanel to use smart-decision

**Files:**
- Modify: `SupplyAI/ai.jsx`

- [ ] **Step 1: Add SCENARIO_LABEL map**

Near the existing `TOOL_LABEL` map (around line 1007), add:

```javascript
const SCENARIO_LABEL = {
  risk_queue: '高风险队列',
  holiday_readiness: '大促备货',
  plan_comparison: '方案对比',
  rule_impact: '规则影响',
  single_sku_replenishment: '单SKU补货',
};
```

- [ ] **Step 2: Rewrite GlobalAIPanel.sendToBackend**

Replace the `sendToBackend` function inside `GlobalAIPanel` (around line 1075-1139). The current function has two branches: one for `decisionScenarioForQuestion` match and one for chat. Replace the entire function with:

```javascript
  const sendToBackend = async (text) => {
    setHistory(h => [...h, { role: 'user', text }]);
    setThinking(true);
    setToolStatus('');
    try {
      const msgs = [];
      for (const m of history) {
        if (m.role === 'user' && m.text) msgs.push({ role: 'user', content: m.text });
        else if (m.role === 'ai' && m.text) msgs.push({ role: 'assistant', content: m.text });
      }
      msgs.push({ role: 'user', content: text });
      const context = { current_page: 'dashboard' };
      if (dashFilters) {
        const filters = {};
        if (dashFilters.store) filters.mall_id = parseInt(dashFilters.store, 10);
        if (dashFilters.country) filters.country_code = dashFilters.country;
        if (dashFilters.owner) filters.owner = dashFilters.owner;
        if (Object.keys(filters).length) context.filters = filters;
      }

      // 用于追加解释文本的 streaming bubble
      let explanationStarted = false;
      const startExplanationBubble = () => {
        if (!explanationStarted) {
          explanationStarted = true;
          setHistory(h => [...h, { role: 'ai', text: '', reasoning: '', streaming: true }]);
        }
      };
      const appendDelta = (delta) => {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.role === 'ai') {
            next[next.length - 1] = { ...last, text: (last.text || '') + delta };
          }
          return next;
        });
      };
      const appendReasoning = (delta) => {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.role === 'ai') {
            next[next.length - 1] = { ...last, reasoning: (last.reasoning || '') + delta };
          }
          return next;
        });
      };

      await window.api.aiSmartDecisionStream(msgs, context, (ev) => {
        if (ev.type === 'classify') {
          setToolStatus(SCENARIO_LABEL[ev.scenario] || ev.scenario);
        } else if (ev.type === 'card') {
          setToolStatus('');
          // 卡片进 history(带 summary 文本 + card 对象)
          setHistory(h => [...h, { role: 'ai', text: ev.summary, card: ev.card }]);
        } else if (ev.type === 'reasoning_delta') {
          startExplanationBubble();
          appendReasoning(ev.text || '');
        } else if (ev.type === 'delta') {
          startExplanationBubble();
          appendDelta(ev.text || '');
        } else if (ev.type === 'tool_start') {
          setToolStatus(TOOL_LABEL[ev.name] || ev.name);
        } else if (ev.type === 'tool_end') {
          setToolStatus('');
        } else if (ev.type === 'error') {
          startExplanationBubble();
          appendDelta('\n⚠️ ' + (ev.message || '调用失败'));
        } else if (ev.type === 'done') {
          setHistory(h => {
            const next = h.slice();
            const last = next[next.length - 1];
            // 如果最后一条是空的 streaming bubble(card_explain=false),删掉
            if (last && last.streaming && !last.text && !last.reasoning) {
              return next.slice(0, -1);
            }
            return next.map(m => m.streaming ? { ...m, streaming: false } : m);
          });
        }
      });
    } catch (err) {
      setHistory(h => [...h, { role: 'ai', text: '⚠️ ' + err.message }]);
    } finally {
      setThinking(false);
      setToolStatus('');
    }
  };
```

- [ ] **Step 3: Handle card in history rendering**

In the `GlobalAIPanel` JSX where history messages are rendered (the `.map` over history), find where `{ role: 'ai' }` messages are rendered. The existing code already handles `card` via `StructuredAICard`. Check that a message with both `text` and `card` renders the card via `StructuredAICard`. If the existing rendering already checks `m.card`, no change needed. If not, add card rendering similar to the existing `BackendDecisionCard` path.

- [ ] **Step 4: Delete unused frontend functions**

Remove these three functions from `ai.jsx`:
- `decisionScenarioForQuestion` (around line 467-473)
- `backendDecisionForQuestion` (around line 475-492)
- `localCardForQuestion` (around line 1028-1032)

Also remove any `parseSafetyDaysTarget` if it was only used by `backendDecisionForQuestion`.

- [ ] **Step 5: Commit**

```bash
git add SupplyAI/ai.jsx
git commit -m "feat: rewire GlobalAIPanel to use smart-decision/stream"
```

---

### Task 6: Frontend — rewire SKUAIPanel to use smart-decision

**Files:**
- Modify: `SupplyAI/ai.jsx`

- [ ] **Step 1: Rewrite SKUAIPanel.sendToBackend**

Find the `sendToBackend` inside `SKUAIPanel` (around line 1290-1340). It has the same two-branch pattern as `GlobalAIPanel`. Replace it with the same smart-decision approach, but with SKU context:

```javascript
  const sendToBackend = async (text) => {
    setHistory(h => [...h, { role: 'user', text }]);
    setThinking(true);
    setToolStatus('');
    try {
      const msgs = [];
      for (const m of history) {
        if (m.role === 'user' && m.text) msgs.push({ role: 'user', content: m.text });
        else if (m.role === 'ai' && m.text) msgs.push({ role: 'assistant', content: m.text });
      }
      msgs.push({ role: 'user', content: text });
      const context = {
        current_page: 'sku',
        sku: {
          msku: sku.msku,
          listing_id: sku.listingId,
          mall_id: sku.mallId,
          store_name: sku.store,
          country_code: sku.country?.code,
        },
      };

      let explanationStarted = false;
      const startExplanationBubble = () => {
        if (!explanationStarted) {
          explanationStarted = true;
          setHistory(h => [...h, { role: 'ai', text: '', reasoning: '', streaming: true }]);
        }
      };
      const appendDelta = (delta) => {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.role === 'ai') {
            next[next.length - 1] = { ...last, text: (last.text || '') + delta };
          }
          return next;
        });
      };
      const appendReasoning = (delta) => {
        setHistory(h => {
          const next = h.slice();
          const last = next[next.length - 1];
          if (last && last.role === 'ai') {
            next[next.length - 1] = { ...last, reasoning: (last.reasoning || '') + delta };
          }
          return next;
        });
      };

      await window.api.aiSmartDecisionStream(msgs, context, (ev) => {
        if (ev.type === 'classify') {
          setToolStatus(SCENARIO_LABEL[ev.scenario] || ev.scenario);
        } else if (ev.type === 'card') {
          setToolStatus('');
          setHistory(h => [...h, { role: 'ai', text: ev.summary, card: ev.card }]);
        } else if (ev.type === 'reasoning_delta') {
          startExplanationBubble();
          appendReasoning(ev.text || '');
        } else if (ev.type === 'delta') {
          startExplanationBubble();
          appendDelta(ev.text || '');
        } else if (ev.type === 'tool_start') {
          setToolStatus(TOOL_LABEL[ev.name] || ev.name);
        } else if (ev.type === 'tool_end') {
          setToolStatus('');
        } else if (ev.type === 'error') {
          startExplanationBubble();
          appendDelta('\n⚠️ ' + (ev.message || '调用失败'));
        } else if (ev.type === 'done') {
          setHistory(h => {
            const next = h.slice();
            const last = next[next.length - 1];
            if (last && last.streaming && !last.text && !last.reasoning) {
              return next.slice(0, -1);
            }
            return next.map(m => m.streaming ? { ...m, streaming: false } : m);
          });
        }
      });
    } catch (err) {
      setHistory(h => [...h, { role: 'ai', text: '⚠️ ' + err.message }]);
    } finally {
      setThinking(false);
      setToolStatus('');
    }
  };
```

- [ ] **Step 2: Commit**

```bash
git add SupplyAI/ai.jsx
git commit -m "feat: rewire SKUAIPanel to use smart-decision/stream"
```

---

### Task 7: Run all existing tests (regression check)

**Files:** None (verification only)

- [ ] **Step 1: Run backend test suite**

Run: `cd supplyai-backend && uv run pytest --ignore=tests/test_browser_e2e.py --ignore=tests/test_browser_e2e_review.py -v 2>&1 | tail -20`

Expected: All existing tests PASS (no regressions)

- [ ] **Step 2: Run smart decision tests**

Run: `cd supplyai-backend && uv run pytest tests/test_smart_decision.py -v`

Expected: All smart decision tests PASS

- [ ] **Step 3: Run browser E2E tests**

Run: `cd supplyai-backend && uv run pytest -m browser -v`

Expected: All 19 browser tests PASS

- [ ] **Step 4: Commit (if any test fixes needed)**

```bash
git add -A
git commit -m "fix: test adjustments for smart-decision integration"
```

---

### Task 8: Browser E2E verification of smart-decision flow

**Files:**
- Modify: `supplyai-backend/tests/test_browser_e2e.py` (add 1 test)

- [ ] **Step 1: Add browser E2E test for smart-decision card + explanation**

At the end of `supplyai-backend/tests/test_browser_e2e.py`, before the AI drawer test, add:

```python
def test_b_us_6_1_smart_decision_card_renders_in_global_ai(page: Page) -> None:
    """B-US-6.1: 全局 AI 输入场景问题,应渲染决策卡片."""
    _wait_for_online(page)

    # 打开全局 AI
    page.keyboard.press("Meta+j")
    expect(page.get_by_text("补货决策")).to_be_visible(timeout=10_000)

    # 输入场景问题
    input_el = page.locator("textarea").last
    input_el.fill("哪些SKU必须补货")
    input_el.press("Enter")

    # 等待卡片渲染(风险分布 or Top 风险 SKU)
    expect(page.get_by_text("风险分布").or_(page.get_by_text("Top 风险"))).to_be_visible(timeout=30_000)
```

- [ ] **Step 2: Run the new browser test**

Run: `cd supplyai-backend && uv run pytest -m browser tests/test_browser_e2e.py::test_b_us_6_1_smart_decision_card_renders_in_global_ai -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add supplyai-backend/tests/test_browser_e2e.py
git commit -m "test: add browser E2E for smart-decision card rendering"
```
