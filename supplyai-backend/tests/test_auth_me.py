"""POST /auth/me — 当前用户身份 (Phase 1 占位,鉴权未上线前用 default).

未鉴权时返回 default_tenant_id 对应的固定 placeholder 身份。
鉴权上线后改读 JWT claim → rl_user 表。
"""
from __future__ import annotations

from httpx import AsyncClient


async def test_me_returns_user_info(client: AsyncClient) -> None:
    resp = await client.post("/api/supplyai/auth/me", json={})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["tenant_id"] == 100228
    assert data["display_name"]
    assert data["role_label"]


async def test_me_includes_tenant_workspace_label(client: AsyncClient) -> None:
    resp = await client.post("/api/supplyai/auth/me", json={})
    data = resp.json()
    assert data["workspace"]
    assert data["timezone"]
