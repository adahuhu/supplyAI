"""AI API — POST /ai/explain + /ai/chat."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
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
