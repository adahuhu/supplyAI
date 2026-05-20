"""API v1 路由聚合."""
from __future__ import annotations

from fastapi import APIRouter

from supplyai.api.v1 import (
    ai,
    auth,
    calc,
    dashboard,
    exports,
    health,
    notifications,
    purchase,
    rules,
    skus,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(calc.router)
api_v1_router.include_router(dashboard.router)
api_v1_router.include_router(skus.router)
api_v1_router.include_router(purchase.router)
api_v1_router.include_router(exports.router)
api_v1_router.include_router(rules.router)
api_v1_router.include_router(ai.router)
api_v1_router.include_router(notifications.router)
# api_v1_router.include_router(ai.router)
# api_v1_router.include_router(purchase.router)
# api_v1_router.include_router(exports.router)

__all__ = ["api_v1_router"]
