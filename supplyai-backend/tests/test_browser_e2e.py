"""真浏览器 E2E — Playwright 驱动 Chromium 操作真实 React 页面.

与 test_e2e_workflows.py 的区别:
  - 这里启子进程跑后端 (uvicorn) + 前端 (python http.server)
  - Chromium 打开 SupplyAI.html,真实加载 Babel + React + 所有 jsx
  - 通过 click / fill / wait_for_selector 模拟用户动作
  - 验证 DOM 真渲染 + UI 状态机真切换 + 数据真显示

跑法:
  uv run pytest tests/test_browser_e2e.py -v

CI 注意:需要 chromium。本地首次:
  uv run playwright install chromium

涉及 AI 抽屉的用例需要真 SUPPLY_DASH_API_KEY,
否则 /ai/explain 报错(我们不再有 mock 兜底)— 因此那些用例 skipif。
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

# ── 端口选用与项目根 ─────────────────────────────────────
BACKEND_PORT = 8001  # 与 dev :8000 错开,避免冲突
FRONTEND_PORT = 5174  # 与 dev :5173 错开

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "supplyai-backend"
FRONTEND_DIR = PROJECT_ROOT / "SupplyAI"

E2E_DB = BACKEND_DIR / "data" / "supplyai-browser-e2e.db"
SEED_DB = BACKEND_DIR / "data" / "supplyai.db"

FRONTEND_URL = (
    f"http://127.0.0.1:{FRONTEND_PORT}/SupplyAI.html"
    f"?api=http://127.0.0.1:{BACKEND_PORT}/api/supplyai"
)

# 整个文件统一打 browser marker,默认 pytest 不跑(与 pytest-asyncio 冲突)
# 显式跑: uv run pytest -m browser
pytestmark = pytest.mark.browser

REAL_AI_AVAILABLE = bool(
    os.environ.get("SUPPLY_DASH_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")
)


def _wait_port(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError(f"port {port} not up after {timeout}s")


# ── Session 级:启停后端 + 前端服务 ─────────────────────


@pytest.fixture(scope="session", autouse=True)
def _services():
    """整套 session 共享一对 backend+frontend 子进程."""
    # 1. 准备隔离 DB(从 seed DB 复制),不脏开发库
    if SEED_DB.exists():
        shutil.copy(SEED_DB, E2E_DB)
    else:
        pytest.skip(f"seed DB not found: {SEED_DB}")

    backend_env = {
        **os.environ,
        "AI_PROVIDER": "dashscope",
        "DATABASE_URL": f"sqlite+aiosqlite:///./data/{E2E_DB.name}",
        "SUPPLY_DASH_VERIFY_SSL": "false",
    }

    backend = subprocess.Popen(
        [
            "uv", "run", "uvicorn", "supplyai.main:app",
            "--host", "127.0.0.1", "--port", str(BACKEND_PORT),
            "--no-access-log",
        ],
        cwd=BACKEND_DIR,
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    frontend = subprocess.Popen(
        [
            sys.executable, "-m", "http.server",
            str(FRONTEND_PORT), "--bind", "127.0.0.1",
        ],
        cwd=FRONTEND_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_port(BACKEND_PORT)
        _wait_port(FRONTEND_PORT)
        yield
    finally:
        backend.terminate()
        frontend.terminate()
        try:
            backend.wait(timeout=3)
        except subprocess.TimeoutExpired:
            backend.kill()
        try:
            frontend.wait(timeout=3)
        except subprocess.TimeoutExpired:
            frontend.kill()
        # 删 e2e DB
        if E2E_DB.exists():
            E2E_DB.unlink()


# 关掉 conftest 自动 monkeypatch ai factory(那个只对 in-process 测试有用,
# 而且 monkeypatch 是 function-scope,在浏览器测试里也无害)
# Playwright 的 page fixture 已由 pytest-playwright 提供。


# ── 浏览器 E2E 用例 ─────────────────────────────────────


@pytest.fixture
def page(page: Page) -> Page:
    """加大默认超时 — Babel-in-browser 首次加载 jsx 需要几秒."""
    page.set_default_timeout(20_000)
    return page


def _wait_for_online(page: Page) -> None:
    """等 Dashboard 主 hero "今日工作摘要" 出现,证明 bootstrap 完成、Dashboard 已 mount.

    旧版用 Topbar "后端已连接" 文案做信号,但产品方已要求移除该状态文字(2026-05-12 review Q1),
    改用 Dashboard 内必出现的稳定文案。
    """
    page.goto(FRONTEND_URL)
    expect(page.get_by_text("今日工作摘要")).to_be_visible(timeout=20_000)


# ════════════════════════════════════════════════════════
# Browser Epic 1 — 启动 / 连接 / 路由
# ════════════════════════════════════════════════════════


def test_b_us_1_1_page_loads_and_dashboard_renders(page: Page) -> None:
    """B-US-1.1: 打开 SupplyAI.html,等 Dashboard 渲染完(说明 bootstrap 拉真数据成功).

    Topbar 已不再露出"后端已连接"字样(2026-05-12 Q1),所以改用 Dashboard 内的稳定文案。
    """
    page.goto(FRONTEND_URL)
    expect(page.locator("body")).to_contain_text("SupplyAI", timeout=10_000)
    expect(page.get_by_text("今日工作摘要")).to_be_visible(timeout=20_000)


def test_b_us_1_2_sidebar_navigation_works(page: Page) -> None:
    """B-US-1.2: 左侧栏所有入口可点,正确切换到对应页面.

    As a  最终用户
    I want 点左侧"备货计划"/"采购草稿"等入口能跳到对应页
    So that 路由 + 导航是真的接通的
    """
    _wait_for_online(page)

    # 点"备货计划"
    page.get_by_role("button", name="备货计划").click()
    expect(page.locator("h1, .h1").filter(has_text="备货计划")).to_be_visible()

    # 点"采购草稿"
    page.get_by_role("button", name="采购草稿").click()
    expect(page.locator("h1, .h1").filter(has_text="采购草稿")).to_be_visible()

    # 回工作台
    page.get_by_role("button", name="工作台").click()
    expect(page.locator("h1, .h1").filter(has_text="分析工作台")).to_be_visible()


# ════════════════════════════════════════════════════════
# Browser Epic 2 — 备货列表真渲染
# ════════════════════════════════════════════════════════


def test_b_us_2_1_list_renders_real_rows_from_backend(page: Page) -> None:
    """B-US-2.1: 备货列表应该真渲染 48 行(seed 数据).

    As a  最终用户
    I want 列表能看到真实 SKU 数据(不是空状态)
    So that 我知道前后端通信 + 适配器把 snake_case 转 camelCase 都没崩
    """
    _wait_for_online(page)
    page.get_by_role("button", name="备货计划").click()

    # 表格数据行真渲染(数据行 ≥ 40,留余裕避免脆性)
    expect(page.locator("table tbody tr").first).to_be_visible(timeout=10_000)
    rows = page.locator("table tbody tr")
    assert rows.count() >= 40, f"列表行数太少:{rows.count()}"

    # 至少一行包含真实 MSKU 前缀
    first_row_text = rows.first.text_content() or ""
    assert "MS" in first_row_text, "未渲染 MSKU"


def test_b_us_2_2_filter_p1_narrows_list_to_12(page: Page) -> None:
    """B-US-2.2: 点 P1 筛选标签,列表确实收窄到只剩 P1.

    As a  运营负责人
    I want 点风险筛选标签后,列表立刻收窄
    So that 我能验证前端 useMemo 真的按 priority 过滤
    """
    _wait_for_online(page)
    page.get_by_role("button", name="备货计划").click()
    expect(page.locator("table tbody tr").first).to_be_visible(timeout=10_000)
    all_count = page.locator("table tbody tr").count()

    # 点 "P1 紧急" 标签
    page.get_by_role("button", name=re.compile(r"P1.*紧急")).first.click()

    # 等列表稳定后断言:必然变少 + 每行 priority chip 都是 P1
    page.wait_for_timeout(500)
    rows = page.locator("table tbody tr")
    n = rows.count()
    assert 1 <= n < all_count, f"P1 筛选后应收窄(实得 {n}/{all_count})"
    # 全行只剩 P1 chip
    p1_chip = page.locator("table tbody tr .chip", has_text=re.compile(r"P1"))
    assert p1_chip.count() == n, f"P1 筛选后每行都应是 P1,实际 P1 chip={p1_chip.count()}/{n}"


# ════════════════════════════════════════════════════════
# Browser Epic 3 — SKU 详情页真渲染
# ════════════════════════════════════════════════════════


def test_b_us_3_1_click_row_navigates_to_detail(page: Page) -> None:
    """B-US-3.1: 列表点任一行进入 SKU 详情,看到 MSKU/ASIN 等基础字段.

    As a  运营负责人
    I want 点行进详情,看到对应 SKU 的 MSKU/ASIN 等基础字段
    So that 路由参数传递 + adapter 字段映射都对
    """
    _wait_for_online(page)
    page.get_by_role("button", name="备货计划").click()
    expect(page.locator("table tbody tr").first).to_be_visible(timeout=10_000)

    # 点击第一行的商品列(避开 sticky checkbox td 的 stopPropagation)
    page.locator("table tbody tr").first.locator("td").nth(1).click()

    # 详情页关键标识(独立于具体行选了哪条):breadcrumb + MSKU 标签 + ASIN 标签
    expect(page.get_by_text("返回列表")).to_be_visible(timeout=10_000)
    expect(page.get_by_text("MSKU:", exact=False)).to_be_visible()
    expect(page.get_by_text("ASIN:", exact=False)).to_be_visible()
    # 风险等级 chip 也必须渲染
    expect(page.locator("body")).to_contain_text(re.compile(r"P\d|safe"))


# ════════════════════════════════════════════════════════
# Browser Epic 4 — 错误页(无后端)
# ════════════════════════════════════════════════════════


def test_b_us_4_1_error_page_shown_when_backend_unreachable(page: Page) -> None:
    """B-US-4.1: 把 ?api= 指到不存在的端口,应显示"无法连接后端"错误页.

    As a  最终用户
    I want 后端挂时看到明确错误指示 + 重试按钮(而不是假数据)
    So that 我知道现在数据是不可靠的,要找运维
    """
    page.goto(
        f"http://127.0.0.1:{FRONTEND_PORT}/SupplyAI.html"
        f"?api=http://127.0.0.1:65499/api/supplyai"
    )
    # ConnectionError 卡片
    expect(page.get_by_text("无法连接后端")).to_be_visible(timeout=15_000)
    expect(page.get_by_role("button", name="重试")).to_be_visible()


# ════════════════════════════════════════════════════════
# Browser Epic 5 — AI 抽屉(需真 DashScope key,否则 skip)
# ════════════════════════════════════════════════════════


@pytest.mark.slow
@pytest.mark.skipif(
    not REAL_AI_AVAILABLE,
    reason="需要 SUPPLY_DASH_API_KEY 跑真 LLM(本套不再有 mock 兜底)",
)
def test_b_us_5_1_open_ai_drawer_shows_explanation(page: Page) -> None:
    """B-US-5.1: 在 SKU 详情页点"AI 分析",抽屉应自动出现解释文字.

    As a  最终用户
    I want 打开 AI 抽屉就看到当前 SKU 的风险解读(由 Qwen 生成)
    So that 我不用切到别的工具找解释
    """
    _wait_for_online(page)
    page.get_by_role("button", name="备货计划").click()
    expect(page.locator("table tbody tr").first).to_be_visible(timeout=10_000)
    page.locator("table tbody tr").first.click()
    expect(page.get_by_text("返回列表")).to_be_visible(timeout=10_000)

    # 点 AI 分析按钮 — 用 title 属性匹配最稳(图标按钮也带 title)
    page.locator('button[title="AI 分析"]').first.click()

    # 步 1:抽屉真打开 — header 出现
    expect(page.get_by_text("SKU 分析助手")).to_be_visible(timeout=10_000)

    # 步 2:Qwen 真实回答出现(/ai/explain 调用,可能 5-10 秒)
    # 等 history 里出现非空文本气泡(过滤掉 header 自身)
    page.wait_for_function(
        """() => {
            // 找有 'AI 解释' 标题的 bubble
            const bubbles = Array.from(document.querySelectorAll('div'));
            return bubbles.some(d => d.textContent && d.textContent.includes('AI 解释'));
        }""",
        timeout=45_000,
    )
