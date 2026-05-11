"""健康检查端点测试."""
from __future__ import annotations

from httpx import AsyncClient


async def test_root(client: AsyncClient) -> None:
    """根路径返回基本信息."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SupplyAI Backend"
    assert "version" in data
    assert "docs" in data


async def test_health(client: AsyncClient) -> None:
    """/_health 检查所有组件状态."""
    response = await client.get("/api/supplyai/_health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "components" in data
    assert any(c["name"] == "database" for c in data["components"])
    assert any(c["name"] == "cache" for c in data["components"])
    assert any(c["name"] == "ai" for c in data["components"])


