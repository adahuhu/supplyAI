"""规则仓储."""
from __future__ import annotations

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.models.mk import MkReplenishmentRule, MkRuleLogisticsMethod


def _scope_filters(
    *,
    tenant_id: int,
    scope_type: str,
    mall_id: int | None,
    msku: str | None,
) -> list:
    filters = [
        MkReplenishmentRule.tenant_id == tenant_id,
        MkReplenishmentRule.scope_type == scope_type,
    ]
    filters.append(
        MkReplenishmentRule.mall_id.is_(None)
        if mall_id is None
        else MkReplenishmentRule.mall_id == mall_id
    )
    filters.append(
        MkReplenishmentRule.msku.is_(None)
        if msku is None
        else MkReplenishmentRule.msku == msku
    )
    return filters


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

    async def get_by_scope(
        self,
        *,
        tenant_id: int,
        scope_type: str,
        mall_id: int | None,
        msku: str | None,
    ) -> MkReplenishmentRule | None:
        """返回同一作用域下最新规则,用于前端无 rule_id 保存时覆盖."""
        return await self._session.scalar(
            select(MkReplenishmentRule)
            .where(
                *_scope_filters(
                    tenant_id=tenant_id,
                    scope_type=scope_type,
                    mall_id=mall_id,
                    msku=msku,
                )
            )
            .order_by(desc(MkReplenishmentRule.updated_at))
            .limit(1)
        )

    async def list_rules(
        self,
        *,
        tenant_id: int,
        scope_types: list[str] | None,
        mall_id: int | None,
        msku: str | None,
        enabled_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[MkReplenishmentRule], int]:
        filters = [MkReplenishmentRule.tenant_id == tenant_id]
        if scope_types:
            filters.append(MkReplenishmentRule.scope_type.in_(scope_types))
        if mall_id is not None:
            filters.append(MkReplenishmentRule.mall_id == mall_id)
        if msku is not None:
            filters.append(MkReplenishmentRule.msku == msku)
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

    async def list_logistics_methods(
        self, rule_ids: list[str]
    ) -> dict[str, list[MkRuleLogisticsMethod]]:
        if not rule_ids:
            return {}
        result = await self._session.execute(
            select(MkRuleLogisticsMethod)
            .where(
                MkRuleLogisticsMethod.rule_id.in_(rule_ids),
                MkRuleLogisticsMethod.is_active == 1,
            )
            .order_by(MkRuleLogisticsMethod.rule_id.asc(), MkRuleLogisticsMethod.id.asc())
        )
        out: dict[str, list[MkRuleLogisticsMethod]] = {}
        for row in result.scalars().all():
            out.setdefault(row.rule_id, []).append(row)
        return out

    async def replace_logistics_methods(
        self, rule_id: str, methods: list[tuple[str, int]]
    ) -> None:
        await self._session.execute(
            delete(MkRuleLogisticsMethod).where(MkRuleLogisticsMethod.rule_id == rule_id)
        )
        self._session.add_all(
            [
                MkRuleLogisticsMethod(
                    rule_id=rule_id,
                    logistics_mode=mode,
                    logistics_days=days,
                    is_active=1,
                    source_type="frontend",
                )
                for mode, days in methods
            ]
        )
        await self._session.flush()

    async def upsert(self, rule: MkReplenishmentRule) -> MkReplenishmentRule:
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def disable_same_scope_except(
        self,
        *,
        tenant_id: int,
        scope_type: str,
        mall_id: int | None,
        msku: str | None,
        keep_rule_id: str,
    ) -> None:
        result = await self._session.execute(
            select(MkReplenishmentRule).where(
                *_scope_filters(
                    tenant_id=tenant_id,
                    scope_type=scope_type,
                    mall_id=mall_id,
                    msku=msku,
                ),
                MkReplenishmentRule.rule_id != keep_rule_id,
                MkReplenishmentRule.enabled == 1,
            )
        )
        for row in result.scalars().all():
            row.enabled = 0
        await self._session.flush()
