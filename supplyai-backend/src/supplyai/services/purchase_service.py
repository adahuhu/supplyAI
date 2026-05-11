"""采购草稿应用服务 — CRUD + 状态机.

状态机:
  draft → confirmed     (confirm)
  draft → redirected    (redirect)
  confirmed → redirected (redirect)
其余跳转 → DraftInvalidTransitionException
"""
from __future__ import annotations

import secrets
from datetime import datetime

from supplyai.models.mk import MkPurchaseDraft
from supplyai.repositories.purchase_repo import PurchaseDraftRepository
from supplyai.schemas.purchase import (
    DraftCreateRequest,
    DraftCreateResponse,
    DraftDTO,
    DraftListRequest,
    DraftListResponse,
)
from supplyai.utils.exceptions import (
    DraftInvalidTransitionException,
    DraftNotFoundException,
    InvalidDraftQtyException,
)

_VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"confirmed", "redirected"},
    "confirmed": {"redirected"},
    "redirected": set(),
}


def _new_draft_id() -> str:
    return f"DRAFT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}"


class PurchaseDraftService:
    def __init__(self, repo: PurchaseDraftRepository) -> None:
        self._repo = repo

    async def create(self, req: DraftCreateRequest) -> DraftCreateResponse:
        if any(item.suggest_qty <= 0 for item in req.items):
            raise InvalidDraftQtyException()

        drafts = [
            MkPurchaseDraft(
                draft_id=_new_draft_id(),
                calc_run_id=req.calc_run_id,
                tenant_id=req.tenant_id,
                mall_id=item.mall_id,
                msku=item.msku,
                sku=item.sku,
                suggest_qty=item.suggest_qty,
                supplier_name=item.supplier_name,
                status="draft",
                created_by=req.created_by,
                source_type="mock",
            )
            for item in req.items
        ]
        await self._repo.add_many(drafts)
        return DraftCreateResponse(
            created_count=len(drafts),
            draft_ids=[d.draft_id for d in drafts],
        )

    async def list_drafts(self, req: DraftListRequest) -> DraftListResponse:
        rows, total = await self._repo.list_drafts(
            tenant_id=req.tenant_id,
            statuses=req.statuses,
            calc_run_id=req.calc_run_id,
            page=req.page,
            page_size=req.page_size,
        )
        return DraftListResponse(
            rows=[DraftDTO.model_validate(r) for r in rows],
            total=total,
            page=req.page,
            page_size=req.page_size,
        )

    async def detail(self, *, tenant_id: int, draft_id: str) -> DraftDTO:
        row = await self._repo.get(tenant_id=tenant_id, draft_id=draft_id)
        if row is None:
            raise DraftNotFoundException(draft_id)
        return DraftDTO.model_validate(row)

    async def transition(
        self, *, tenant_id: int, draft_id: str, target_state: str
    ) -> DraftDTO:
        row = await self._repo.get(tenant_id=tenant_id, draft_id=draft_id)
        if row is None:
            raise DraftNotFoundException(draft_id)
        if target_state not in _VALID_TRANSITIONS.get(row.status, set()):
            raise DraftInvalidTransitionException(row.status, target_state)
        row.status = target_state
        return DraftDTO.model_validate(row)
