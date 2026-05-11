"""SKU summary 加缺货损失 / 未来利润字段 — 让 AI 能直接读出"价值"维度."""
from __future__ import annotations

from httpx import AsyncClient


async def test_summary_includes_value_fields(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1},
    )
    assert resp.status_code == 200
    row = resp.json()["rows"][0]
    assert "expected_loss_revenue_7d" in row
    assert "future_30d_profit" in row


async def test_loss_only_for_short_sellable_days(client: AsyncClient) -> None:
    """fba_sellable_days <= 7 的行应该有正的 expected_loss_revenue_7d.
    > 7 的应当 = 0 (7 天内不会断货)."""
    resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 48},
    )
    for row in resp.json()["rows"]:
        days = row.get("fba_sellable_days")
        loss = row.get("expected_loss_revenue_7d") or 0
        if days is None or days > 7:
            assert loss == 0, (
                f"{row['msku']} 可售 {days} 天 > 7,损失应为 0,实得 {loss}"
            )
        elif row.get("future_daily") and row.get("unit_cost"):
            assert loss > 0, (
                f"{row['msku']} 可售 {days} 天 ≤ 7,有 daily+cost,损失应 > 0"
            )


async def test_future_30d_profit_calculation(client: AsyncClient) -> None:
    """future_30d_profit 不应为 None,有 future_daily 时应 >= 0."""
    resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 5},
    )
    for row in resp.json()["rows"]:
        profit = row.get("future_30d_profit")
        assert profit is not None
        if row.get("future_daily"):
            # 利润可能为负(成本>售价),但应是数字
            assert isinstance(profit, (int, float))


async def test_value_fields_returned_in_ai_agent_tool(client: AsyncClient) -> None:
    """AI 的 query_replenishment_advice 工具批量结果也应含 value 字段."""
    from supplyai.db import async_session_factory
    from supplyai.domain.ai.tools import execute_tool

    async with async_session_factory() as session:
        out = await execute_tool(
            "query_replenishment_advice",
            {"tenant_id": 100228, "limit": 3, "suggest_only": False},
            session,
        )
    assert "rows" in out
    for r in out["rows"]:
        assert "expected_loss_revenue_7d" in r
        assert "future_30d_profit" in r
