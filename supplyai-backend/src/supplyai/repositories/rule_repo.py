"""规则仓储."""
from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.models.mk import MkReplenishmentRule


class RuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, *, tenant_id: int, rule_id: str
    ) -> MkReplenishmentRule | None:
        return await self._session.scalar(
            select(MkReplenishmentRule).where(
                MkReplenishmentRule.tenant_id == tenant_id,
                MkReplenishmentRule.rule_id == rule_id,
            )
        )

    async def list_rules(
        self,
        *,
        tenant_id: int,
        scope_types: list[str] | None,
        mall_id: int | None,
        enabled_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[MkReplenishmentRule], int]:
        filters = [MkReplenishmentRule.tenant_id == tenant_id]
        if scope_types:
            filters.append(MkReplenishmentRule.scope_type.in_(scope_types))
        if mall_id is not None:
            filters.append(MkReplenishmentRule.mall_id == mall_id)
        if enabled_only:
            filters.append(MkReplenishmentRule.enabled == 1)

        total = await self._session.scalar(
            select(func.count(MkReplenishmentRule.rule_id)).where(*filters)
        )
        rows = (
            await self._session.execute(
                select(MkReplenishmentRule)
                .where(*filters)
                .order_by(desc(MkReplenishmentRule.updated_at))
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return list(rows), int(total or 0)

    async def upsert(self, rule: MkReplenishmentRule) -> MkReplenishmentRule:
        self._session.add(rule)
        await self._session.flush()
        return rule
