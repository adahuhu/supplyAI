# Smart Decision: 决策卡片 + LLM 解释协同

## 背景

当前 AI 对话有两条割裂的路径：
1. **5 种场景卡片**：前端正则分类 → 后端直查库 → JSON 卡片渲染（秒出、精确，但无解释）
2. **自由对话**：LLM + Orchestrator + 4 个 Tool → 流式文本（有推理，但慢且卡片依赖正则提取）

问题：
- 场景卡片只有数据没有解释，用户不知道"为什么"
- 卡片数据不进入 chat history，追问时 LLM 无法引用
- 前端正则分类硬编码，同义表达（如"哪些货快卖完了"）匹配不到

## 目标

让决策卡片和 LLM 解释协同：卡片秒出 → LLM 异步解释"为什么" → 卡片数据进入对话上下文支持追问。

## 设计

### 新端点

`POST /api/supplyai/ai/smart-decision/stream` — SSE 流式

**请求体**（与现有 `/ai/chat/stream` 格式一致）：

```json
{
  "tenant_id": 100228,
  "messages": [
    { "role": "user", "content": "哪些货快卖完了" }
  ],
  "context": {
    "current_page": "dashboard",
    "filters": { "mall_id": 1001 },
    "sku": { "msku": "MS40060", "listing_id": 1000003 }
  }
}
```

### SSE 事件协议

**命中场景时：**

```
event: classify    → {"type":"classify","scenario":"risk_queue","method":"regex"|"llm"}
event: card        → {"type":"card","scenario":"risk_queue","card":{...},"summary":"..."}
event: reasoning_delta → {"type":"reasoning_delta","text":"..."}   (可选)
event: delta       → {"type":"delta","text":"从风险队列来看，"}     (card_explain=true 时)
event: done        → {"type":"done","finish_reason":"stop","scenario":"risk_queue"}
```

**未命中场景时（退化到 chat）：**

```
event: tool_start  → {"type":"tool_start","name":"query_stockout_risk",...}
event: tool_end    → {"type":"tool_end","name":"query_stockout_risk","ok":true,...}
event: delta       → {"type":"delta","text":"..."}
event: done        → {"type":"done","finish_reason":"stop","tool_iterations":1}
```

与现有 `/ai/chat/stream` 事件完全一致，前端可统一处理。

### 配置开关

`.env` 新增：

```dotenv
SUPPLY_CARD_EXPLAIN=true
```

- `true`（默认）：卡片渲染后追加 LLM 流式解释
- `false`：出卡即止，与当前行为一致

`config.py` / `settings` 新增 `card_explain: bool = True`。

### 后端分类逻辑（两级策略）

**第一级：正则（0ms）**

```python
SCENARIO_PATTERNS = {
    "risk_queue":                r"高风险|必须补货|紧急度|风险队列|优先级",
    "holiday_readiness":         r"大促|节日|Prime|活动备货|母亲节|黑五|圣诞",
    "plan_comparison":           r"方案对比|海运|空运|海空|海\+空|混合",
    "rule_impact":               r"规则模拟|安全天数|改成|调整|规则影响",
    "single_sku_replenishment":  r"挑一个|单个SKU|还能卖多久|要不要补",
}
```

命中即返回，不走 LLM。

**第二级：LLM 轻量调用（1-2s）**

```
system: 你是意图分类器。用户问题属于以下哪个场景？只返回场景名，不解释。
  - risk_queue: 查看风险SKU、补货优先级、断货排序
  - holiday_readiness: 大促备货、节日缺口、活动准备
  - plan_comparison: 运输方案比较、海运空运对比、物流成本
  - rule_impact: 规则参数调整影响、安全天数变化
  - single_sku_replenishment: 单个SKU补货建议
  - none: 以上都不是

user: {用户消息}
```

参数：`max_tokens=20`，`temperature=0`，不传 tools。3 秒超时保护，超时视为 `none`。

### 后端编排 — SmartDecisionService

新建 `supplyai-backend/src/supplyai/services/smart_decision_service.py`。

依赖：
- `AiService`：复用 `decision_card()` 生成卡片
- `AiClient`：LLM 分类 + LLM 解释流式生成
- `AiService.chat_stream()`：未命中场景时退化

核心方法：

```python
async def stream(self, req: SmartDecisionRequest) -> AsyncIterator[dict]:
    text = req.messages[-1].content
    scenario, method = await self._classify(text)

    if scenario:
        yield {"type": "classify", "scenario": scenario, "method": method}

        card_resp = await self._ai_service.decision_card(
            DecisionCardRequest(tenant_id=req.tenant_id, scenario=scenario, context=ctx)
        )
        summary = self._build_card_summary(card_resp)
        yield {"type": "card", "scenario": scenario, "card": card_resp.card, "summary": summary}

        if settings.card_explain:
            async for delta in self._ai_client.chat_stream(messages=explain_msgs):
                # yield reasoning_delta / delta / done
            return

        yield {"type": "done", "finish_reason": "stop", "scenario": scenario}
        return

    # 未命中 — 退化到 Orchestrator chat
    async for event in self._ai_service.chat_stream(req.to_chat_request()):
        yield event
```

**`_build_card_summary()`**：将卡片 JSON 压缩为 200-400 字文本摘要，供 LLM 解释引用和注入 chat history。每种卡片类型有对应的摘要模板。

**解释用 system prompt（`CARD_EXPLAIN_PROMPT`）**：

```
你是供应链分析师。基于以下决策卡片数据，用 2-3 句话解释：
1. 当前最紧急的风险是什么
2. 为什么建议这样处理
3. 有什么需要注意的
简洁直接，不要重复数据本身，重点是归因和建议。
```

### 前端改动

**`api.jsx`**：新增 `aiSmartDecisionStream(messages, context, onEvent)` 方法，URL 指向 `/ai/smart-decision/stream`，实现与现有 `aiChatStream` 一致。

**`ai.jsx`**：

1. `GlobalAIPanel.sendToBackend` 和 `SKUAIPanel.sendToBackend`：删除前端正则分类分支，统一调 `aiSmartDecisionStream`
2. `onEvent` 回调增加 `classify` 和 `card` 事件处理：
   - `classify`：显示分类状态（如"识别为: 高风险队列"）
   - `card`：渲染卡片 + 把 summary 存入 history + 预备空的解释 bubble
   - `done`：如果最后一条 bubble 为空（`card_explain=false`），清理掉
3. 删除 `decisionScenarioForQuestion()`、`backendDecisionForQuestion()`、`localCardForQuestion()`

**对话上下文连贯**：`card` 事件的 `summary` 作为 `{ role: 'ai', text: summary }` 存入 history，后续追问时自动带入 messages，LLM 可自然引用卡片数据。不需要额外机制。

### 错误处理

| 环节 | 失败场景 | 处理 |
|------|---------|------|
| LLM 分类 | API 超时(>3s)/异常 | 跳过分类，退化到 Orchestrator chat |
| 卡片生成 | calc_run 不存在/SKU 找不到 | yield error 事件 + 退化到 chat |
| LLM 解释 | API 超时/流中断 | yield done 提前结束，卡片已出不受影响 |

原则：卡片已推送就不回滚。解释失败只影响解释。

### 测试

新增 `tests/test_smart_decision.py`：

| 用例 | 验证 |
|------|------|
| 正则命中 "哪些 SKU 必须补货" | classify(regex) → card → delta(解释) → done |
| 正则未命中 + LLM 命中 "哪些货快卖完了" | classify(llm) → card → delta → done |
| 两级都未命中 "你好" | 直接 chat delta → done |
| `card_explain=false` | classify → card → done（无 delta） |
| LLM 分类超时 | 3s 内退化到 chat |
| 卡片生成失败 | error → 退化到 chat |
| 追问引用卡片 | history 含 summary，LLM 回答涉及卡片内容 |

### 不改动的部分

- 所有卡片渲染组件（`RiskQueueCard` / `HolidayReadinessCard` 等）
- `StructuredAICard` 分发逻辑
- `AiService` 现有方法（`explain` / `explain_stream` / `chat` / `chat_stream` / `decision_card`）
- SKU AI 的 `/ai/explain/stream` 流程
- 现有 `/ai/chat/stream` 和 `/ai/decision-card` 端点保留，不删除

### 文件清单

| 文件 | 操作 |
|------|------|
| `supplyai-backend/src/supplyai/services/smart_decision_service.py` | 新建 |
| `supplyai-backend/src/supplyai/schemas/ai.py` | 新增 SmartDecisionRequest |
| `supplyai-backend/src/supplyai/api/v1/ai.py` | 新增 `/ai/smart-decision/stream` 路由 |
| `supplyai-backend/src/supplyai/config.py` | 新增 `card_explain` 配置 |
| `supplyai-backend/env.example` | 新增 `SUPPLY_CARD_EXPLAIN` |
| `supplyai-backend/tests/test_smart_decision.py` | 新建 |
| `SupplyAI/api.jsx` | 新增 `aiSmartDecisionStream` |
| `SupplyAI/ai.jsx` | 改 sendToBackend，删前端分类函数 |
