"""POST /dashboard/finance — 昨日财务摘要 + 同比."""
from __future__ import annotations

from httpx import AsyncClient


async def test_finance_returns_five_metrics(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/finance", json={"tenant_id": 100228}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for k in ("sales", "gmv", "cost", "expense", "profit"):
        assert k in data
        assert "value" in data[k]
        assert "pct_change" in data[k]


async def test_finance_values_non_negative(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/finance", json={"tenant_id": 100228}
    )
    data = resp.json()
    # 销量/GMV/成本/费用 应 ≥ 0
    assert data["sales"]["value"] >= 0
    assert data["gmv"]["value"] >= 0
    assert data["cost"]["value"] >= 0
    assert data["expense"]["value"] >= 0


async def test_finance_profit_formula(client: AsyncClient) -> None:
    """利润 = GMV - cost - expense,误差 ±1。"""
    resp = await client.post(
        "/api/supplyai/dashboard/finance", json={"tenant_id": 100228}
    )
    d = resp.json()
    expected = d["gmv"]["value"] - d["cost"]["value"] - d["expense"]["value"]
    assert abs(d["profit"]["value"] - expected) <= 1


async def test_finance_includes_as_of_date_and_currency(
    client: AsyncClient,
) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/finance", json={"tenant_id": 100228}
    )
    d = resp.json()
    assert d["as_of_date"]  # YYYY-MM-DD
    assert d["currency"] == "USD"


async def test_finance_pct_change_can_be_null_or_number(
    client: AsyncClient,
) -> None:
    """pct_change 可以是 None(无前日数据)或数值."""
    resp = await client.post(
        "/api/supplyai/dashboard/finance", json={"tenant_id": 100228}
    )
    for k in ("sales", "gmv", "cost", "expense", "profit"):
        v = resp.json()[k]["pct_change"]
        assert v is None or isinstance(v, (int, float))
