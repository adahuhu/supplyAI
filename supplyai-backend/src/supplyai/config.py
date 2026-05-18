"""应用配置 — pydantic-settings 从 .env 加载。"""
from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def _normalize_dashscope_url(url: str) -> str:
    """阿里云百炼自部署 endpoint 常见形态:
        - .../api/v1            ← 阿里云原生协议(我们不用)
        - .../compatible-mode/v1 ← OpenAI 兼容(我们用这个)
    用户环境变量给 /api/v1 时自动切到 /compatible-mode/v1,避免改环境配置。
    """
    if not url:
        return url
    cleaned = url.rstrip("/")
    if cleaned.endswith("/api/v1"):
        return cleaned[: -len("/api/v1")] + "/compatible-mode/v1"
    return cleaned


class Settings(BaseSettings):
    """应用配置.

    从 .env 文件 + 环境变量加载;支持本地 / 生产两套形态。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== 应用基础 =====
    app_env: Literal["local", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["console", "json"] = "console"

    # ===== 数据库 =====
    database_url: str = "sqlite+aiosqlite:///./data/supplyai.db"

    # ===== AI 服务 =====
    ai_provider: Literal["dashscope", "openai"] = "dashscope"
    ai_model: str = "qwen3.6-plus"
    ai_max_input_tokens: int = 4000
    ai_max_output_tokens: int = 1024
    ai_history_turns: int = 8
    # 同时接受 SUPPLY_DASH_API_KEY (用户当前机器环境变量) 和 DASHSCOPE_API_KEY (传统命名)
    dashscope_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SUPPLY_DASH_API_KEY", "DASHSCOPE_API_KEY", "dashscope_api_key"),
    )
    # OpenAI 兼容模式 endpoint;默认走官方公网,SUPPLY_DASH_URL 可覆盖
    # 自动把 /api/v1 → /compatible-mode/v1(阿里云自部署 endpoint 兼容)
    dashscope_base_url: str = Field(
        default=DEFAULT_DASHSCOPE_URL,
        validation_alias=AliasChoices("SUPPLY_DASH_URL", "DASHSCOPE_BASE_URL", "dashscope_base_url"),
    )

    @field_validator("dashscope_base_url")
    @classmethod
    def _normalize_url(cls, v: str) -> str:
        return _normalize_dashscope_url(v)

    # 自部署 endpoint 证书可能与 hostname 不匹配,允许关闭 SSL 校验
    # SUPPLY_DASH_VERIFY_SSL=false 时跳过证书校验(仅本地开发用)
    dashscope_verify_ssl: bool = Field(
        default=True,
        validation_alias=AliasChoices("SUPPLY_DASH_VERIFY_SSL", "dashscope_verify_ssl"),
    )

    # Qwen3.x 的 reasoning_content(思维链)展示:默认开启,
    # 前端会把 reasoning 在折叠面板里实时展示,延迟到首条 reasoning_delta(~0.5-1s)。
    # 如需 cost/latency 优先,可 SUPPLY_DASH_ENABLE_THINKING=false 直接跳过思考阶段。
    dashscope_enable_thinking: bool = Field(
        default=True,
        validation_alias=AliasChoices("SUPPLY_DASH_ENABLE_THINKING", "dashscope_enable_thinking"),
    )

    # 决策卡片后是否追加 LLM 流式解释 — 默认 true
    # - true:  卡片渲染后,LLM 异步生成 2-3 句归因解释
    # - false: 出卡即止,与旧版行为一致
    card_explain: bool = Field(
        default=True,
        validation_alias=AliasChoices("SUPPLY_CARD_EXPLAIN", "card_explain"),
    )

    # ===== 缓存 =====
    cache_backend: Literal["memory", "redis"] = "memory"
    cache_default_ttl: int = 60
    redis_url: str | None = None

    # ===== 后台任务 =====
    task_runner: Literal["local", "celery"] = "local"

    # ===== 多租户 =====
    default_tenant_id: int = 100228
    default_base_currency: str = "USD"

    # ===== 鉴权（Phase 4 启用） =====
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"

    # ===== 导出 =====
    export_dir: str = "./data/exports"
    export_sync_threshold: int = 5000  # 行数 ≤ 此值同步生成,否则异步

    @property
    def is_local(self) -> bool:
        return self.app_env == "local"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


# 单例（应用启动时初始化）
settings = Settings()
