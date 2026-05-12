"""AI API — POST /ai/explain + /ai/chat + /ai/chat/stream (SSE)."""
from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.db import get_db_session
from supplyai.domain.ai import get_ai_client
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.repositories.sku_repo import SkuRepository
from supplyai.schemas.ai import (
    ChatRequest,
    ChatResponseMessage,
    ExplainRequest,
    ExplainResponse,
)
from supplyai.services.ai_service import AiService

router = APIRouter(prefix="/ai", tags=["ai"])


def _build_service(session: AsyncSession) -> AiService:
    return AiService(
        ai_client=get_ai_client(),
        sku_repo=SkuRepository(session),
        dashboard_repo=DashboardRepository(session),
        session=session,
    )


@router.post("/explain", response_model=ExplainResponse)
async def explain_sku(
    req: ExplainRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExplainResponse:
    """对单 SKU 给出风险/建议的中文解释."""
    return await _build_service(session).explain(req)


@router.post("/chat", response_model=ChatResponseMessage)
async def ai_chat(
    req: ChatRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ChatResponseMessage:
    """通用对话 — 走 AiOrchestrator 调度循环,工具可触发数据查询/草稿生成预览."""
    out = await _build_service(session).chat(req)
    # 工具循环里若有 generate_purchase_draft confirmed=True 会落库,提交事务
    await session.commit()
    return out


@router.post("/chat/stream")
async def ai_chat_stream(
    req: ChatRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """流式对话 — SSE 格式输出.

    事件:
      data: {"type":"tool_start","name":"...","arguments":{...}}
      data: {"type":"tool_end","name":"...","ok":true,"summary":"返回 N 条"}
      data: {"type":"delta","text":"..."}
      data: {"type":"done","finish_reason":"stop","tool_iterations":1}

    每行 data: 加 \\n\\n 结尾,符合 EventStream 规范。
    """
    # 流启动前的同步校验 — 否则 exception 在流开始后抛会破坏 SSE
    from supplyai.utils.exceptions import AiEmptyMessagesException
    if not req.messages:
        raise AiEmptyMessagesException()

    svc = _build_service(session)

    async def event_gen():
        try:
            async for event in svc.chat_stream(req):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        finally:
            # 工具循环中可能落库,流结束时统一提交
            try:
                await session.commit()
            except Exception:  # noqa: BLE001
                pass

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 关掉 nginx buffering
        },
    )
