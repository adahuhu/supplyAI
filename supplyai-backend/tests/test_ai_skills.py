"""Foundation Skills + AiAnswer.status 测试.

约束(技术方案 §7.5):
  - AI 只解释系统已计算结果,不重算建议采购量 / 可售天数
  - 口径锁定到同一系统快照
  - 预计断货 = FBA 侧;采购时间 = 全链路
  - 缺失值 / 估算 / 多币种必须显式说明
  - 采购草稿动作必须二次确认 SKU/数量/供应商

status:
  - ok       — 完整回答
  - partial  — 部分数据缺失但可回答
  - degraded — AI 不可用,返回结构化规则解释作为兜底
"""
from __future__ import annotations

from httpx import AsyncClient

from supplyai.domain.ai.foundation import (
    SYSTEM_PROMPT,
    build_explain_prompt,
    classify_status,
    sanitize_user_ai_text,
)


# ============ Foundation Skills system prompt ============


def test_system_prompt_includes_calc_run_id_constraint() -> None:
    """system prompt 必须告诉模型口径锁定同一系统快照."""
    assert "系统快照" in SYSTEM_PROMPT
    assert "口径" in SYSTEM_PROMPT or "同一" in SYSTEM_PROMPT
    assert "calc_run_id" not in SYSTEM_PROMPT
    assert "mk_" not in SYSTEM_PROMPT


def test_system_prompt_includes_no_recompute_constraint() -> None:
    """system prompt 必须禁止 AI 自行重算 suggest_qty 等."""
    assert "不" in SYSTEM_PROMPT  # 必有否定约束
    assert any(kw in SYSTEM_PROMPT for kw in ["不重算", "不自行计算", "不重新计算"])
    assert "suggest_qty" in SYSTEM_PROMPT or "建议采购量" in SYSTEM_PROMPT


def test_system_prompt_includes_fba_vs_total_caliber() -> None:
    """预计断货 = FBA 口径;采购时间 = 全链路口径."""
    assert "FBA" in SYSTEM_PROMPT
    assert "断货" in SYSTEM_PROMPT


def test_system_prompt_requires_disclosure_of_missing() -> None:
    """缺失/估算/多币种必须显式说明."""
    assert "缺失" in SYSTEM_PROMPT or "estimate" in SYSTEM_PROMPT.lower()


def test_system_prompt_requires_purchase_double_confirm() -> None:
    """采购动作要求二次确认."""
    assert "确认" in SYSTEM_PROMPT
    assert "供应商" in SYSTEM_PROMPT or "采购草稿" in SYSTEM_PROMPT


# ============ build_explain_prompt 上下文注入 ============


class _FakeDto:
    msku = "MS40060"
    asin = "B000000048"
    store_name = "Sakura-JP01"
    priority = "p1"
    fba_sellable_days = 1.99
    suggest_qty = 923
    suggest_amount_base = 36.61
    base_currency = "USD"
    stockout_date = None
    coverage_demand = 30.0
    forecast_source = "default"
    total_stock = 30


def test_explain_prompt_carries_structured_context() -> None:
    """prompt 必须把关键字段都喂给模型,不能让模型猜."""
    p = build_explain_prompt(_FakeDto(), calc_run_id="DEMO-123")
    for token in ["MS40060", "B000000048", "p1", "1.99", "923"]:
        assert str(token) in p, f"prompt 缺字段:{token}"
    assert "DEMO-123" not in p
    assert "calc_run_id" not in p


def test_explain_prompt_marks_missing_fields() -> None:
    """关键字段为 None 时必须显式标注缺失,不能默默填 0."""
    class Empty:
        msku = "MS-X"
        asin = None
        store_name = None
        priority = "safe"
        fba_sellable_days = None
        suggest_qty = 0
        suggest_amount_base = None
        base_currency = None
        stockout_date = None
        coverage_demand = None
        forecast_source = None
        total_stock = None

    p = build_explain_prompt(Empty(), calc_run_id="DEMO-X")
    assert "缺失" in p or "未知" in p or "—" in p


def test_sanitize_user_ai_text_hides_internal_names() -> None:
    text = "基于 mk_supply_sku_daily_stat 和 rl_fba_shipment_item, calc_run_id=R1, suggest_qty=20。"
    cleaned = sanitize_user_ai_text(text)
    for raw in ["mk_supply_sku_daily_stat", "rl_fba_shipment_item", "calc_run_id", "suggest_qty"]:
        assert raw not in cleaned
    assert "备货分析结果" in cleaned
    assert "FBA 发货记录" in cleaned


# ============ classify_status 分级 ============


def test_status_ok_when_all_present() -> None:
    sku_ctx = {
        "fba_sellable_days": 5.0,
        "suggest_qty": 100,
        "stockout_date": "2026-05-15",
    }
    assert classify_status(sku_ctx, ai_available=True) == "ok"


def test_status_partial_when_field_missing() -> None:
    sku_ctx = {
        "fba_sellable_days": None,
        "suggest_qty": 0,
        "stockout_date": None,
    }
    assert classify_status(sku_ctx, ai_available=True) == "partial"


def test_status_degraded_when_ai_unavailable() -> None:
    sku_ctx = {
        "fba_sellable_days": 5.0,
        "suggest_qty": 100,
        "stockout_date": "2026-05-15",
    }
    assert classify_status(sku_ctx, ai_available=False) == "degraded"


# ============ /ai/explain 返回 status 字段 ============


async def test_explain_response_includes_status_field(client: AsyncClient) -> None:
    """API 响应必须带 status,前端用它决定降级展示."""
    resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1},
    )
    listing_id = resp.json()["rows"][0]["id"]

    explain = await client.post(
        "/api/supplyai/ai/explain",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    assert explain.status_code == 200
    data = explain.json()
    assert "status" in data
    assert data["status"] in {"ok", "partial", "degraded"}


async def test_chat_response_includes_status_field(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/ai/chat",
        json={
            "tenant_id": 100228,
            "messages": [{"role": "user", "content": "风险如何"}],
        },
    )
    assert resp.status_code == 200
    assert "status" in resp.json()
