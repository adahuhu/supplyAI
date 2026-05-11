"""验证 SUPPLY_DASH_URL / SUPPLY_DASH_API_KEY 环境变量映射到 settings."""
from __future__ import annotations

import importlib

import pytest


def _reload_config(monkeypatch, env: dict[str, str | None]) -> object:
    """重新导入 config 模块,使 Settings 重新读取环境变量."""
    for k in (
        "SUPPLY_DASH_API_KEY",
        "SUPPLY_DASH_URL",
        "DASHSCOPE_API_KEY",
        "DASHSCOPE_BASE_URL",
    ):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        if v is not None:
            monkeypatch.setenv(k, v)
    import supplyai.config as cfg

    importlib.reload(cfg)
    return cfg.settings


def test_supply_dash_env_keys_are_read(monkeypatch) -> None:
    s = _reload_config(monkeypatch, {
        "SUPPLY_DASH_API_KEY": "sk-real-test",
        "SUPPLY_DASH_URL": "https://example.com/v1",
    })
    assert s.dashscope_api_key == "sk-real-test"
    assert s.dashscope_base_url == "https://example.com/v1"


def test_legacy_dashscope_env_keys_still_work(monkeypatch) -> None:
    """老命名 DASHSCOPE_API_KEY 仍可用."""
    s = _reload_config(monkeypatch, {
        "DASHSCOPE_API_KEY": "sk-legacy",
    })
    assert s.dashscope_api_key == "sk-legacy"


def test_supply_dash_takes_priority_over_legacy(monkeypatch) -> None:
    """同时设置时,SUPPLY_DASH_API_KEY 优先(AliasChoices 顺序决定)."""
    s = _reload_config(monkeypatch, {
        "SUPPLY_DASH_API_KEY": "sk-supply",
        "DASHSCOPE_API_KEY": "sk-legacy",
    })
    assert s.dashscope_api_key == "sk-supply"


def test_default_base_url_when_unset(monkeypatch) -> None:
    s = _reload_config(monkeypatch, {})
    assert s.dashscope_base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert s.dashscope_api_key is None


def test_url_with_api_v1_suffix_normalized_to_compatible_mode(monkeypatch) -> None:
    """阿里云自部署 endpoint /api/v1 自动改写为 /compatible-mode/v1."""
    s = _reload_config(monkeypatch, {
        "SUPPLY_DASH_URL": "https://ws-xxx.cn-beijing.maas.aliyuncs.com/api/v1",
    })
    assert s.dashscope_base_url == "https://ws-xxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"


def test_url_already_compatible_mode_kept_as_is(monkeypatch) -> None:
    s = _reload_config(monkeypatch, {
        "SUPPLY_DASH_URL": "https://ws-xxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    })
    assert s.dashscope_base_url == "https://ws-xxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"


@pytest.fixture(autouse=True, scope="module")
def _restore_settings():
    """模块跑完后,把全局 settings 还原成正常导入状态,避免污染其它测试."""
    yield
    import supplyai.config as cfg

    importlib.reload(cfg)
