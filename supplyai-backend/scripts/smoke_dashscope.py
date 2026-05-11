"""一次性脚本:用真实 DashScope API key 跑两个最小用例.

前提: 环境变量 SUPPLY_DASH_API_KEY (与 SUPPLY_DASH_URL,可选) 已配置。

跑法:
    uv run python scripts/smoke_dashscope.py

会打两个请求:
  1. 单轮文本(无工具)
  2. 带工具(query_stockout_risk)的对话,触发 Orchestrator 调度循环
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

from supplyai.config import settings
from supplyai.db import async_session_factory
from supplyai.domain.ai.client import ChatMessage
from supplyai.domain.ai.factory import get_ai_client
from supplyai.domain.ai.orchestrator import AiOrchestrator


async def main() -> int:
    if settings.ai_provider != "dashscope":
        print(
            "❌ AI_PROVIDER 当前是",
            settings.ai_provider,
            "— 请先 export AI_PROVIDER=dashscope 再跑",
        )
        return 1
    if not settings.dashscope_api_key:
        print("❌ SUPPLY_DASH_API_KEY 未读到。检查环境变量是否已 export。")
        return 1

    print(f"✓ provider={settings.ai_provider} model={settings.ai_model}")
    print(f"✓ base_url={settings.dashscope_base_url}")
    print(f"✓ api_key={settings.dashscope_api_key[:6]}…(长度 {len(settings.dashscope_api_key)})")

    client = get_ai_client()

    # 1) 单轮文本
    print("\n────── [1] 单轮文本 ──────")
    resp = await client.chat(
        messages=[
            ChatMessage(role="system", content="你是供应链分析助手,中文回答。"),
            ChatMessage(role="user", content="一句话告诉我,FBA 可售 5 天属于哪个风险等级。"),
        ]
    )
    print(f"finish_reason={resp.finish_reason}")
    print(f"content: {resp.content}")

    # 2) 带工具 + 真实 DB 的 Orchestrator 调度
    print("\n────── [2] 工具调度循环 ──────")
    async with async_session_factory() as session:
        orch = AiOrchestrator(client, session=session, tenant_id=100228, max_iterations=3)
        out = await orch.run([
            ChatMessage(
                role="user",
                content="列出当前最紧急的 3 个 SKU,告诉我它们的 MSKU 和 FBA 可售天数。",
            )
        ])
    print(f"tool_iterations={out.tool_iterations} finish_reason={out.finish_reason}")
    print(f"content:\n{out.content}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
