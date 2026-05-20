"""日报推送 API."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.db import get_db_session
from supplyai.schemas.notification import (
    NotificationPreviewDTO,
    NotificationPreviewRequest,
    NotificationSendDTO,
    NotificationSendRequest,
    NotificationRole,
)
from supplyai.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/dingtalk/preview", response_model=NotificationPreviewDTO)
async def dingtalk_preview(
    req: NotificationPreviewRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NotificationPreviewDTO:
    """生成钉钉日报卡片预览."""
    return await NotificationService(session).preview(req)


@router.post("/dingtalk/send", response_model=NotificationSendDTO)
async def dingtalk_send(
    req: NotificationSendRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NotificationSendDTO:
    """发送钉钉日报;未配置 Webhook 时返回模拟发送结果."""
    return await NotificationService(session).send(req)


@router.get("/dingtalk/card.svg")
async def dingtalk_card_svg(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_id: int = 100228,
    role: NotificationRole = "boss",
    target_name: str | None = None,
    owners: Annotated[list[str] | None, Query()] = None,
    mall_ids: Annotated[list[int] | None, Query()] = None,
    country_codes: Annotated[list[str] | None, Query()] = None,
    detail_url: str | None = None,
) -> Response:
    """生成可嵌入钉钉 Markdown 的日报卡片图."""
    service = NotificationService(session)
    req = NotificationPreviewRequest(
        tenant_id=tenant_id,
        role=role,
        target_name=target_name,
        owners=owners,
        mall_ids=mall_ids,
        country_codes=country_codes,
        detail_url=detail_url,
    )
    preview = await service.preview(req)
    svg = service.card_svg(preview.report, title=preview.title, subtitle=preview.subtitle)
    return Response(
        content=svg,
        media_type="image/svg+xml; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )
