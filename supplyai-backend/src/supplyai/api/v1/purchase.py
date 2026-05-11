"""采购草稿 API — 全部 POST."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.db import get_db_session
from supplyai.repositories.purchase_repo import PurchaseDraftRepository
from supplyai.schemas.purchase import (
    DraftCreateRequest,
    DraftCreateResponse,
    DraftDTO,
    DraftDetailRequest,
    DraftListRequest,
    DraftListResponse,
    DraftStateRequest,
)
from supplyai.services.purchase_service import PurchaseDraftService

router = APIRouter(prefix="/purchase/draft", tags=["purchase"])


def _build_service(session: AsyncSession) -> PurchaseDraftService:
    return PurchaseDraftService(PurchaseDraftRepository(session))


@router.post("/create", response_model=DraftCreateResponse)
async def create_draft(
    req: DraftCreateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DraftCreateResponse:
    """从 SKU 建议批量生成采购草稿."""
    result = await _build_service(session).create(req)
    await session.commit()
    return result


@router.post("/list", response_model=DraftListResponse)
async def list_drafts(
    req: DraftListRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DraftListResponse:
    """采购草稿列表."""
    return await _build_service(session).list_drafts(req)


@router.post("/detail", response_model=DraftDTO)
async def draft_detail(
    req: DraftDetailRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DraftDTO:
    """采购草稿详情."""
    return await _build_service(session).detail(
        tenant_id=req.tenant_id, draft_id=req.draft_id
    )


@router.post("/confirm", response_model=DraftDTO)
async def confirm_draft(
    req: DraftStateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DraftDTO:
    """状态机: draft → confirmed."""
    result = await _build_service(session).transition(
        tenant_id=req.tenant_id, draft_id=req.draft_id, target_state="confirmed"
    )
    await session.commit()
    return result


@router.post("/redirect", response_model=DraftDTO)
async def redirect_draft(
    req: DraftStateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DraftDTO:
    """状态机: draft/confirmed → redirected(等同放弃/转手动)."""
    result = await _build_service(session).transition(
        tenant_id=req.tenant_id, draft_id=req.draft_id, target_state="redirected"
    )
    await session.commit()
    return result
