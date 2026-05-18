"""规则应用服务."""
from __future__ import annotations

import secrets
from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, func, select

from supplyai.models.mk import MkForecastRule, MkReplenishmentRule
from supplyai.repositories.rule_repo import RuleRepository
from supplyai.schemas.rule import (
    ForecastRuleDTO,
    ForecastRuleListRequest,
    ForecastRuleListResponse,
    ForecastRuleUpsertRequest,
    RuleDTO,
    RuleLogisticsMethodDTO,
    RuleListRequest,
    RuleListResponse,
    RuleUpsertRequest,
)
from supplyai.utils.exceptions import RuleInvalidScopeException, RuleNotFoundException


def _new_rule_id() -> str:
    """生成的规则 ID 用 'RULE-T-{timestamp}-' 前缀,避免与 seed 'RULE-GLOBAL-*' 等冲突."""
    return f"RULE-T-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}"


def _validate_scope(req: RuleUpsertRequest) -> None:
    if req.scope_type == "store" and req.mall_id is None:
        raise RuleInvalidScopeException("store 范围必须指定 mall_id。")
    if req.scope_type == "sku":
        if req.mall_id is None or not req.msku:
            raise RuleInvalidScopeException(
                "sku 范围必须同时指定 mall_id 和 msku。"
            )


def _to_rule_dto(
    rule: MkReplenishmentRule,
    logistics_methods: list[RuleLogisticsMethodDTO] | None = None,
) -> RuleDTO:
    return RuleDTO(
        rule_id=rule.rule_id,
        tenant_id=rule.tenant_id,
        scope_type=rule.scope_type,
        mall_id=rule.mall_id,
        msku=rule.msku,
        safety_days=rule.safety_days,
        purchase_duration_days=rule.purchase_duration_days,
        delivery_days=rule.delivery_days,
        qc_days=rule.qc_days,
        rule_version=rule.rule_version,
        enabled=bool(rule.enabled),
        updated_by=rule.updated_by,
        updated_at=rule.updated_at,
        logistics_methods=logistics_methods or [],
    )


def _normalize_logistics_methods(
    methods: list[RuleLogisticsMethodDTO] | None,
) -> list[tuple[str, int]] | None:
    if methods is None:
        return None
    seen: set[str] = set()
    normalized: list[tuple[str, int]] = []
    for item in methods:
        mode = item.mode.strip()
        if not mode or mode in seen:
            continue
        seen.add(mode)
        normalized.append((mode, max(0, int(item.days))))
    return normalized


class RuleService:
    def __init__(self, repo: RuleRepository) -> None:
        self._repo = repo

    async def list_rules(self, req: RuleListRequest) -> RuleListResponse:
        rows, total = await self._repo.list_rules(
            tenant_id=req.tenant_id,
            scope_types=req.scope_types,
            mall_id=req.mall_id,
            msku=req.msku,
            enabled_only=req.enabled_only,
            page=req.page,
            page_size=req.page_size,
        )
        logistics_by_rule = await self._repo.list_logistics_methods(
            [r.rule_id for r in rows]
        )
        return RuleListResponse(
            rows=[
                _to_rule_dto(
                    r,
                    [
                        RuleLogisticsMethodDTO(
                            mode=m.logistics_mode,
                            days=m.logistics_days,
                        )
                        for m in logistics_by_rule.get(r.rule_id, [])
                    ],
                )
                for r in rows
            ],
            total=total,
            page=req.page,
            page_size=req.page_size,
        )

    async def upsert(self, req: RuleUpsertRequest) -> RuleDTO:
        _validate_scope(req)
        if req.rule_id:
            rule = await self._repo.get(
                tenant_id=req.tenant_id, rule_id=req.rule_id
            )
            if rule is None:
                raise RuleNotFoundException(req.rule_id)
        else:
            rule = await self._repo.get_by_scope(
                tenant_id=req.tenant_id,
                scope_type=req.scope_type,
                mall_id=req.mall_id,
                msku=req.msku,
            )
            if rule is None:
                rule = MkReplenishmentRule(
                    rule_id=_new_rule_id(),
                    tenant_id=req.tenant_id,
                    source_type="mock",
                )

        rule.scope_type = req.scope_type
        rule.mall_id = req.mall_id
        rule.msku = req.msku
        rule.safety_days = req.safety_days
        rule.purchase_duration_days = req.purchase_duration_days
        rule.delivery_days = req.delivery_days
        rule.qc_days = req.qc_days
        rule.rule_version = req.rule_version
        rule.enabled = 1 if req.enabled else 0
        rule.updated_by = req.updated_by

        await self._repo.upsert(rule)
        normalized_methods = _normalize_logistics_methods(req.logistics_methods)
        if normalized_methods is not None:
            await self._repo.replace_logistics_methods(rule.rule_id, normalized_methods)
        methods = [
            RuleLogisticsMethodDTO(mode=mode, days=days)
            for mode, days in (normalized_methods or [])
        ]
        return _to_rule_dto(rule, methods)

    async def disable(self, *, tenant_id: int, rule_id: str) -> RuleDTO:
        rule = await self._repo.get(tenant_id=tenant_id, rule_id=rule_id)
        if rule is None:
            raise RuleNotFoundException(rule_id)
        rule.enabled = 0
        return _to_rule_dto(rule)


def _new_forecast_rule_id() -> str:
    return f"FORECAST-T-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}"


def _validate_forecast_scope(req: ForecastRuleUpsertRequest) -> None:
    if req.scope_type == "store" and req.mall_id is None:
        raise RuleInvalidScopeException("store 范围必须指定 mall_id。")
    if req.scope_type == "sku":
        if req.mall_id is None or not req.msku:
            raise RuleInvalidScopeException(
                "sku 范围必须同时指定 mall_id 和 msku。"
            )


def _forecast_scope_filters(
    *,
    tenant_id: int,
    scope_type: str,
    mall_id: int | None,
    msku: str | None,
) -> list:
    filters = [
        MkForecastRule.tenant_id == tenant_id,
        MkForecastRule.scope_type == scope_type,
    ]
    filters.append(
        MkForecastRule.mall_id.is_(None)
        if mall_id is None
        else MkForecastRule.mall_id == mall_id
    )
    filters.append(
        MkForecastRule.msku.is_(None)
        if msku is None
        else MkForecastRule.msku == msku
    )
    return filters


def _to_forecast_dto(r: MkForecastRule) -> ForecastRuleDTO:
    return ForecastRuleDTO(
        rule_id=r.rule_id,
        tenant_id=r.tenant_id,
        scope_type=r.scope_type,
        mall_id=r.mall_id,
        msku=r.msku,
        forecast_mode=r.forecast_mode,
        fixed_daily_sales=float(r.fixed_daily_sales) if r.fixed_daily_sales is not None else None,
        default_daily_sales=float(r.default_daily_sales) if r.default_daily_sales is not None else None,
        weight_3d=r.weight_3d,
        weight_7d=r.weight_7d,
        weight_15d=r.weight_15d,
        weight_30d=r.weight_30d,
        denoise_enabled=bool(r.denoise_enabled),
        abnormal_dates_json=r.abnormal_dates_json,
        abnormal_sales_rule_json=r.abnormal_sales_rule_json,
    )


class ForecastRuleService:
    def __init__(self, session) -> None:
        self._session = session

    async def list_rules(
        self, req: ForecastRuleListRequest
    ) -> ForecastRuleListResponse:
        filters = [MkForecastRule.tenant_id == req.tenant_id]
        if req.scope_types:
            filters.append(MkForecastRule.scope_type.in_(req.scope_types))
        if req.mall_id is not None:
            filters.append(MkForecastRule.mall_id == req.mall_id)
        if req.msku is not None:
            filters.append(MkForecastRule.msku == req.msku)
        total = await self._session.scalar(
            select(func.count(MkForecastRule.rule_id)).where(*filters)
        )
        rows = (
            await self._session.execute(
                select(MkForecastRule)
                .where(*filters)
                .order_by(desc(MkForecastRule.updated_at))
                .offset((req.page - 1) * req.page_size)
                .limit(req.page_size)
            )
        ).scalars().all()
        return ForecastRuleListResponse(
            rows=[_to_forecast_dto(r) for r in rows],
            total=int(total or 0),
            page=req.page,
            page_size=req.page_size,
        )

    async def upsert(self, req: ForecastRuleUpsertRequest) -> ForecastRuleDTO:
        _validate_forecast_scope(req)
        if req.rule_id:
            rule = await self._session.scalar(
                select(MkForecastRule).where(
                    MkForecastRule.tenant_id == req.tenant_id,
                    MkForecastRule.rule_id == req.rule_id,
                )
            )
            if rule is None:
                raise RuleNotFoundException(req.rule_id)
        else:
            rule = await self._session.scalar(
                select(MkForecastRule)
                .where(
                    *_forecast_scope_filters(
                        tenant_id=req.tenant_id,
                        scope_type=req.scope_type,
                        mall_id=req.mall_id,
                        msku=req.msku,
                    )
                )
                .order_by(desc(MkForecastRule.updated_at))
                .limit(1)
            )
            if rule is None:
                rule = MkForecastRule(
                    rule_id=_new_forecast_rule_id(),
                    tenant_id=req.tenant_id,
                    source_type="mock",
                )
                self._session.add(rule)

        rule.scope_type = req.scope_type
        rule.mall_id = req.mall_id
        rule.msku = req.msku
        rule.forecast_mode = req.forecast_mode
        rule.fixed_daily_sales = (
            Decimal(str(req.fixed_daily_sales)) if req.fixed_daily_sales is not None else None
        )
        rule.default_daily_sales = (
            Decimal(str(req.default_daily_sales)) if req.default_daily_sales is not None else None
        )
        rule.weight_3d = req.weight_3d
        rule.weight_7d = req.weight_7d
        rule.weight_15d = req.weight_15d
        rule.weight_30d = req.weight_30d
        rule.denoise_enabled = 1 if req.denoise_enabled else 0
        rule.abnormal_dates_json = req.abnormal_dates_json
        rule.abnormal_sales_rule_json = req.abnormal_sales_rule_json
        rule.updated_by = req.updated_by
        await self._session.flush()
        return _to_forecast_dto(rule)
