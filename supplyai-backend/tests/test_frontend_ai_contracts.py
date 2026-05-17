from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AI_JSX = (ROOT / "SupplyAI" / "ai.jsx").read_text(encoding="utf-8")
RULES_JSX = (ROOT / "SupplyAI" / "rules.jsx").read_text(encoding="utf-8")


def test_smart_decision_stream_replaces_frontend_routing() -> None:
    """前端不再自行分类场景,统一走 /ai/smart-decision/stream."""
    # 旧的前端分类函数应已删除
    assert "function decisionScenarioForQuestion" not in AI_JSX
    assert "function backendDecisionForQuestion" not in AI_JSX
    assert "function localCardForQuestion" not in AI_JSX
    # 新的统一入口
    assert "aiSmartDecisionStream" in AI_JSX


def test_rule_impact_apply_copy_matches_global_or_sku_scope() -> None:
    assert "const isGlobalScope = card.scope === 'global'" in AI_JSX
    assert "应用到主 SKU 并重新计算" in AI_JSX
    assert "应用 ${targetSafeDays} 天并重新计算" in AI_JSX


def test_rule_impact_card_is_backend_driven_not_local_snapshot() -> None:
    """卡片由后端 decision_card 生成,前端无本地快照逻辑."""
    assert "card: { type: 'rule_impact', targetSafeDays, sku }" not in AI_JSX
    assert "function makeSnapshotCard" not in AI_JSX
    assert "source: 'local_snapshot'" not in AI_JSX


def test_rules_modal_does_not_hide_recalc_or_refresh_failures() -> None:
    assert "calcResp = await window.api.calcRun({ run_type: 'rule_changed' })" in RULES_JSX
    assert "重新计算失败" in RULES_JSX
    assert "页面刷新失败" in RULES_JSX
    assert "catch (_) { /* 忽略 */ }" not in RULES_JSX
