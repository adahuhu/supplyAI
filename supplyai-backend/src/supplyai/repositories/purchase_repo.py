"""采购草稿仓储."""
from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.models.mk import MkPurchaseDraft


class PurchaseDraftRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(self, drafts: list[MkPurchaseDraft]) -> None:
        if not drafts:
            return
        self._session.add_all(drafts)
        await self._session.flush()

    async def get(self, *, tenant_id: int, draft_id: str) -> MkPurchaseDraft | None:
        return await self._session.scalar(
            select(MkPurchaseDraft).where(
                MkPurchaseDraft.tenant_id == tenant_id,
                MkPurchaseDraft.draft_id == draft_id,
            )
        )

    async def list_drafts(
        self,
        *,
        tenant_id: int,
        statuses: list[str] | None,
        calc_run_id: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[MkPurchaseDraft], int]:
        filters = [MkPurchaseDraft.tenant_id == tenant_id]
        if statuses:
            filters.append(MkPurchaseDraft.status.in_(statuses))
        if calc_run_id:
            filters.append(MkPurchaseDraft.calc_run_id == calc_run_id)

        total = await self._session.scalar(
            select(func.count(MkPurchaseDraft.draft_id)).where(*filters)
        )
        result = await self._session.execute(
            select(MkPurchaseDraft)
            .where(*filters)
            .order_by(desc(MkPurchaseDraft.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), int(total or 0)
