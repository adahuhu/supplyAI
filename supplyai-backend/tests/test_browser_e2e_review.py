"""真浏览器端到端 — 2026-05-12 飞书 review Q1-Q9 验证.

覆盖问题:
  Q1 删除 Topbar "后端已连接"
  Q2 CreatePOModal 按钮文案"生成采购计划"
  Q3 备货计划勾选样式(batch action bar 卡片化)
  Q4 列表不再有"预计到货"列
  Q5 规则中心销量预测预测趋势图能渲染
  Q6 从单 SKU 进入规则中心保存不报缺 mall_id/msku
  Q7 排除异常销量改为双输入(阈值 X + 默认 Y)
  Q8 销量预测无"样本天数"
  Q9 SKU 详情天数显示精确到 2 位(不出现 9 个 9 这种 float 误差)

跑法:
  uv run pytest -m browser tests/test_browser_e2e_review.py -v

依赖共享 fixture _services / page,来自 test_browser_e2e.py。
"""
from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

# 复用 sibling 模块里的 fixture(_services / FRONTEND_URL)
from tests.test_browser_e2e import FRONTEND_URL, _services  # noqa: F401

pytestmark = pytest.mark.browser


def _wait_dashboard(page: Page) -> None:
    page.goto(FRONTEND_URL)
    expect(page.get_by_text("今日工作摘要")).to_be_visible(timeout=20_000)


def _goto_list(page: Page) -> None:
    """切到备货计划列表."""
    page.get_by_role("button", name="备货计划").first.click()
    expect(page.locator("h1, .h1").get_by_text("备货计划")).to_be_visible(timeout=10_000)


def _open_rules_no_ctx(page: Page) -> None:
    """从备货计划页面点击"规则中心"按钮打开 RulesModal(无 ctx)."""
    page.get_by_role("button", name="规则中心").click()
    expect(page.get_by_text("规则设置", exact=True)).to_be_visible(timeout=10_000)


# ════════════════════════════════════════════════════════
# Q1 — Topbar 不再出现"后端已连接"
# ════════════════════════════════════════════════════════
def test_q1_topbar_no_backend_connected_label(page: Page) -> None:
    _wait_dashboard(page)
    # Dashboard 已渲染 = 后端连通;此时不应有"后端已连接"四个字
    assert page.get_by_text("后端已连接").count() == 0, \
        "Q1: '后端已连接'文案应被移除"


# ════════════════════════════════════════════════════════
# Q2 — 采购计划按钮文案
# ════════════════════════════════════════════════════════
def test_q2_create_po_navigates_to_drafts(page: Page) -> None:
    """Q2: 勾选后点"生成采购计划"应跳转到采购计划页(drafts)."""
    _wait_dashboard(page)
    _goto_list(page)
    rows = page.locator("table.t tbody tr")
    expect(rows.first).to_be_visible()
    rows.first.locator("input[type=checkbox]").check()
    # 点击 batch action bar 里"生成采购计划（1）"按钮
    page.locator("button.btn.primary").filter(has_text="生成采购计划").first.click()
    # 应跳转到采购计划创建页(section 内的标题 div)
    expect(page.locator("section").get_by_text("创建采购计划")).to_be_visible(timeout=10_000)


# ════════════════════════════════════════════════════════
# Q3 — 勾选样式(batch action bar 用卡片式 / sticky 列 box-shadow)
# ════════════════════════════════════════════════════════
def test_q3_selected_state_batch_bar_visible(page: Page) -> None:
    _wait_dashboard(page)
    _goto_list(page)
    rows = page.locator("table.t tbody tr")
    rows.first.locator("input[type=checkbox]").check()
    # batch action bar 包含"已选" 和 数字
    expect(page.get_by_text("已选 1 项", exact=False)).to_be_visible()
    # 选中行的 sticky 列(checkbox td)依然可见
    first_cell = rows.first.locator("td").first
    expect(first_cell).to_be_visible()


# ════════════════════════════════════════════════════════
# Q4 — 列表不再有"预计到货"列
# ════════════════════════════════════════════════════════
def test_q4_list_no_estimated_arrival_column(page: Page) -> None:
    _wait_dashboard(page)
    _goto_list(page)
    expect(page.locator("table.t thead")).to_be_visible(timeout=10_000)
    headers_text = page.locator("table.t thead").inner_text()
    assert "预计到货" not in headers_text, "Q4: 列表表头不应有'预计到货'列"
    # 仍保留上次发货/上次采购两列
    assert "上次发货" in headers_text
    assert "上次采购" in headers_text


# ════════════════════════════════════════════════════════
# Q5 — 规则中心销量预测 tab 预测趋势图可见
# ════════════════════════════════════════════════════════
def test_q5_forecast_chart_renders(page: Page) -> None:
    _wait_dashboard(page)
    _goto_list(page)
    _open_rules_no_ctx(page)
    page.get_by_role("button", name="销量预测").click()
    # ChartArea SVG 应渲染
    expect(page.get_by_text("预测趋势图", exact=True)).to_be_visible()
    expect(page.get_by_text("历史前 7 天 · 预测后 30 天")).to_be_visible()


# ════════════════════════════════════════════════════════
# Q6 — 从单 SKU 进入规则保存不报缺 mall_id/msku
# ════════════════════════════════════════════════════════
def test_q6_save_rule_from_single_sku_no_scope_error(page: Page) -> None:
    _wait_dashboard(page)
    _goto_list(page)
    # 第一行 "规则设置" 图标按钮(每行右侧 sticky 操作列)
    rows = page.locator("table.t tbody tr")
    expect(rows.first).to_be_visible()
    rows.first.locator("button[title='规则设置']").click()
    expect(page.get_by_text("规则设置", exact=True)).to_be_visible(timeout=10_000)
    # 点保存(默认 batch scope + ctx.sku 已传)
    page.locator("button.btn.primary").get_by_text("保存", exact=True).first.click()
    # 不应出现"未指定 mall_id 和 msku"
    # toast 可能出现"规则已保存"或"计算中…",但绝不应是 sku 范围错误
    page.wait_for_timeout(2000)
    body_text = page.locator("body").inner_text()
    assert "sku 范围必须指定" not in body_text, "Q6: 单 SKU 入口保存不应报缺 mall/msku"
    assert "未指定 mall_id" not in body_text


# ════════════════════════════════════════════════════════
# Q7 — 排除异常销量改"超过 X 默认 Y"
# ════════════════════════════════════════════════════════
def test_q7_abnormal_sales_two_inputs(page: Page) -> None:
    _wait_dashboard(page)
    _goto_list(page)
    _open_rules_no_ctx(page)
    page.get_by_role("button", name="销量预测").click()
    # 双输入框 placeholder 应可见(独有,避免文本歧义)
    expect(page.get_by_placeholder("如 200")).to_be_visible()
    expect(page.get_by_placeholder("如 80")).to_be_visible()
    expect(page.get_by_text("则默认为", exact=True)).to_be_visible()
    # 旧的 checkbox 文案"自动识别（3σ 离群）"应消失
    assert page.get_by_text("自动识别").count() == 0, "Q7: 旧 checkbox 应被移除"


# ════════════════════════════════════════════════════════
# Q8 — 销量预测 PreviewKV 不再出现"样本天数"
# ════════════════════════════════════════════════════════
def test_q8_no_sample_days_kv(page: Page) -> None:
    _wait_dashboard(page)
    _goto_list(page)
    _open_rules_no_ctx(page)
    page.get_by_role("button", name="销量预测").click()
    expect(page.get_by_text("预测趋势图", exact=True)).to_be_visible()
    body = page.locator("body").inner_text()
    assert "样本天数" not in body, "Q8: '样本天数'应被移除"


# ════════════════════════════════════════════════════════
# Q9 — SKU 详情数字小数点精确到 2 位
# ════════════════════════════════════════════════════════
def test_q9_sku_detail_numbers_two_decimals(page: Page) -> None:
    _wait_dashboard(page)
    _goto_list(page)
    rows = page.locator("table.t tbody tr")
    expect(rows.first).to_be_visible()
    # 点商品名所在的 sticky 列(避开 checkbox 列的 stopPropagation)
    rows.first.locator("td").nth(1).click()
    expect(page.locator(".h3", has_text="关键指标")).to_be_visible(timeout=15_000)
    body = page.locator("body").inner_text()
    import re
    long_floats = re.findall(r"\d+\.9{9,}\d*", body)
    assert not long_floats, f"Q9: 出现长 float 误差: {long_floats}"
    long_days = re.findall(r"\d+\.\d{3,}\s*天", body)
    assert not long_days, f"Q9: 天数超过 2 位小数: {long_days}"


# ════════════════════════════════════════════════════════
# 2026-05-12 v2 review — 3 new issues
# ════════════════════════════════════════════════════════
def test_rq1_rules_modal_wider(page: Page) -> None:
    """R-Q1: 规则配置弹框加宽到至少 1080px."""
    _wait_dashboard(page)
    _goto_list(page)
    _open_rules_no_ctx(page)
    # Modal 的容器(react-renders <div onClick=stopPropagation 在 ui.jsx Modal>)
    modal = page.locator("div.h2", has_text="规则设置").locator("xpath=ancestor::div[contains(@style, 'border-radius')][1]")
    box = modal.bounding_box()
    assert box is not None and box["width"] >= 1080, f"R-Q1: 弹框宽度应 ≥1080,当前 {box}"


def test_rq2_exclude_date_inputs_editable(page: Page) -> None:
    """R-Q2: 排除异常时间应可填写 date + reason."""
    _wait_dashboard(page)
    _goto_list(page)
    _open_rules_no_ctx(page)
    page.get_by_role("button", name="销量预测").click()
    # 点添加 → 新行可见;或者已有种子行
    page.get_by_role("button", name="添加时间段").click()
    # 至少 2 个 type=date 输入
    date_inputs = page.locator("input[type=date]")
    assert date_inputs.count() >= 2, "R-Q2: 应至少有 2 个 date input"
    # 第一个 date 应可写
    first_date = date_inputs.first
    first_date.fill("2026-06-01")
    assert first_date.input_value() == "2026-06-01"
    # reason input 占位"原因(如 Prime Day)"
    expect(page.get_by_placeholder("原因(如 Prime Day)").first).to_be_visible()


def test_rq3_tab_switch_does_not_change_final_daily(page: Page) -> None:
    """R-Q3: 切换 fixed/dynamic/default tab 时,'最终未来平均日销' 不应变化."""
    _wait_dashboard(page)
    _goto_list(page)
    _open_rules_no_ctx(page)
    page.get_by_role("button", name="销量预测").click()
    # 拿到"最终未来平均日销"的数值
    kv = page.locator("text=最终未来平均日销").locator("xpath=following-sibling::*[1]")
    expect(kv).to_be_visible(timeout=10_000)
    initial = kv.inner_text().strip()
    # 切换三个 mode 都不应改变
    for label in ["固定日销量", "默认日销", "动态销量"]:
        page.get_by_role("button", name=label).click()
        page.wait_for_timeout(200)
        cur = kv.inner_text().strip()
        assert cur == initial, f"R-Q3: 切换到 {label} 后 finalDaily 变了:{initial} → {cur}"
