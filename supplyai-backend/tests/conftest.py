"""pytest 共享 fixtures."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from supplyai.db import async_session_factory
from supplyai.domain.ai import factory as ai_factory
from supplyai.main import app
from supplyai.models.mk import (
    MkCalcRun,
    MkExportTask,
    MkPurchaseDraft,
    MkReplenishmentRule,
    MkSkuForecastDaily,
    MkSupplySkuDailyStat,
)
from tests._ai_stub import StubAiClient


@pytest.fixture(autouse=True)
def _patch_ai_factory(monkeypatch):
    """注入 ai stub,所有 in-process 测试不依赖外网.

    Sync fixture,对 sync(Playwright)和 async 测试都安全。
    Browser E2E 跑独立子进程后端,这个 patch 不影响子进程。
    """
    stub = StubAiClient()
    monkeypatch.setattr(ai_factory, "get_ai_client", lambda: stub)
    import supplyai.api.v1.ai as ai_api
    monkeypatch.setattr(ai_api, "get_ai_client", lambda: stub)
    yield


async def _cleanup_test_data() -> None:
    """清理测试触发的 RUN-/DRAFT-/EXP-/RULE-T- 前缀数据."""
    async with async_session_factory() as session:
        exp_rows = (
            await session.execute(
                select(MkExportTask).where(MkExportTask.task_id.like("EXP-%"))
            )
        ).scalars().all()
        for t in exp_rows:
            if t.file_url:
                p = Path(t.file_url)
                if p.exists():
                    p.unlink()
        await session.execute(
            delete(MkExportTask).where(MkExportTask.task_id.like("EXP-%"))
        )
        await session.execute(
            delete(MkPurchaseDraft).where(MkPurchaseDraft.draft_id.like("DRAFT-%"))
        )
        await session.execute(
            delete(MkReplenishmentRule).where(
                MkReplenishmentRule.rule_id.like("RULE-T-%")
            )
        )
        await session.execute(
            delete(MkSkuForecastDaily).where(
                MkSkuForecastDaily.calc_run_id.like("RUN-%")
            )
        )
        await session.execute(
            delete(MkSupplySkuDailyStat).where(
                MkSupplySkuDailyStat.calc_run_id.like("RUN-%")
            )
        )
        await session.execute(
            delete(MkCalcRun).where(MkCalcRun.calc_run_id.like("RUN-%"))
        )
        await session.commit()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """async HTTP 客户端 + 自动清理.

    把 cleanup 嵌入 client teardown,而不是 autouse — 这样
    Playwright 这种 sync 测试不会卡在 async event loop 冲突上。
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    # teardown: 清理测试数据
    await _cleanup_test_data()
