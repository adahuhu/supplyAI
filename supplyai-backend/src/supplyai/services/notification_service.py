"""日报推送服务."""
from __future__ import annotations

import base64
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from html import escape
from urllib.parse import parse_qs, quote_plus, urlencode, urlparse

import httpx
from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.config import settings
from supplyai.models.mk import MkListingProductSources, MkSupplySkuDailyStat
from supplyai.models.rl import RlAmzSalesDailyReport, RlMall
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.schemas.notification import (
    NotificationMetric,
    NotificationPreviewDTO,
    NotificationPreviewRequest,
    NotificationReport,
    NotificationRiskSummary,
    NotificationSendDTO,
    NotificationSendRequest,
    NotificationSkuRow,
)
from supplyai.services.dashboard_service import EXPENSE_RATE
from supplyai.utils.exceptions import CalcRunNotFoundException


ROLE_LABELS = {
    "boss": "老板",
    "operator": "运营",
}


class NotificationService:
    """生成经营日报,并按配置推送到钉钉."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._dashboard_repo = DashboardRepository(session)

    async def preview(self, req: NotificationPreviewRequest) -> NotificationPreviewDTO:
        calc_run_id = await self._dashboard_repo.latest_calc_run_id(req.tenant_id)
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)

        d1 = await self._dashboard_repo.latest_sales_date(req.tenant_id)
        if not d1:
            d1 = datetime.utcnow().date().isoformat()
        start_7d = (datetime.strptime(d1, "%Y-%m-%d") - timedelta(days=6)).date().isoformat()

        finance = await self._finance_metrics(req, d1)
        top_skus = await self._top_skus(req, start_7d, d1)
        risk = await self._risk_summary(req, calc_run_id)
        focus_skus = await self._focus_skus(req, calc_run_id, limit=5)
        role_label = ROLE_LABELS[req.role]
        target_name = req.target_name or ("管理层" if req.role == "boss" else self._operator_name(req))
        scope_label = self._scope_label(req)

        summary = self._summary_text(role_label=role_label, risk=risk, top_skus=top_skus)
        action_text = self._action_text(req.role, risk)
        report = NotificationReport(
            role=req.role,
            role_label=role_label,
            target_name=target_name,
            scope_label=scope_label,
            as_of_date=d1,
            finance=finance,
            top_skus=top_skus,
            focus_skus=focus_skus,
            risk=risk,
            summary=summary,
            action_text=action_text,
        )
        detail_url = self._ai_detail_url(
            req.detail_url or settings.public_app_url or "http://127.0.0.1:5173/SupplyAI.html"
        )
        push_date = datetime.now().date().isoformat()
        title = f"SupplyAI 每日经营简报｜{push_date}"
        subtitle = f"{role_label}视角 · {scope_label}"
        card_image_url = self._card_image_url(req, detail_url)
        markdown = self._markdown(
            title=title,
            subtitle=subtitle,
            report=report,
            detail_url=detail_url,
            card_image_url=card_image_url,
        )
        payload = self._dingtalk_action_card(title=title, markdown=markdown, detail_url=detail_url)
        return NotificationPreviewDTO(
            role=req.role,
            role_label=role_label,
            title=title,
            subtitle=subtitle,
            detail_url=detail_url,
            markdown=markdown,
            dingtalk_payload=payload,
            report=report,
        )

    async def send(self, req: NotificationSendRequest) -> NotificationSendDTO:
        preview = await self.preview(req)
        webhook = req.webhook_url or settings.dingtalk_webhook_url
        if not webhook:
            return NotificationSendDTO(
                **preview.model_dump(),
                status="simulated",
                message="未配置钉钉 Webhook,已完成模拟发送。",
                provider_response={"simulated": True},
            )

        signed_url = self._signed_webhook_url(webhook, settings.dingtalk_secret)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(signed_url, json=preview.dingtalk_payload)
        provider_response = self._safe_json(resp)
        if resp.is_success and self._dingtalk_ok(provider_response):
            return NotificationSendDTO(
                **preview.model_dump(),
                status="sent",
                message="钉钉日报已发送。",
                provider_response=provider_response,
            )
        return NotificationSendDTO(
            **preview.model_dump(),
            status="failed",
            message=f"钉钉发送失败: HTTP {resp.status_code}",
            provider_response=provider_response,
        )

    async def _finance_metrics(
        self, req: NotificationPreviewRequest, ymd: str
    ) -> list[NotificationMetric]:
        sales = RlAmzSalesDailyReport
        lps = MkListingProductSources
        filters = [sales.tenant_id == req.tenant_id, sales.year_month_day == ymd]
        if req.mall_ids:
            filters.append(sales.mall_id.in_(req.mall_ids))
        if req.country_codes:
            filters.append(sales.country_code.in_(req.country_codes))
        if req.owners:
            filters.append(lps.owner.in_(req.owners))

        query = (
            select(
                func.coalesce(func.sum(sales.sales_volume), 0),
                func.coalesce(func.sum(sales.sales), 0),
                func.coalesce(
                    func.sum(func.coalesce(sales.sales_volume, 0) * func.coalesce(lps.unit_cost, 0)),
                    0,
                ),
            )
            .select_from(
                sales.__table__.outerjoin(
                    lps.__table__,
                    (sales.tenant_id == lps.tenant_id)
                    & (sales.listing_id == lps.listing_id),
                )
            )
            .where(*filters)
        )
        qty, revenue, cost = (await self._session.execute(query)).one()
        revenue_f = float(revenue or 0)
        cost_f = float(cost or 0)
        expense_f = round(revenue_f * EXPENSE_RATE, 2)
        profit_f = round(revenue_f - cost_f - expense_f, 2)
        return [
            NotificationMetric(label="昨日销量", value=float(qty or 0), unit="件"),
            NotificationMetric(label="收入", value=round(revenue_f, 2), unit="USD"),
            NotificationMetric(label="成本", value=round(cost_f, 2), unit="USD"),
            NotificationMetric(label="费用", value=expense_f, unit="USD"),
            NotificationMetric(label="利润", value=profit_f, unit="USD"),
        ]

    async def _top_skus(
        self, req: NotificationPreviewRequest, start_ymd: str, end_ymd: str
    ) -> list[NotificationSkuRow]:
        sales = RlAmzSalesDailyReport
        lps = MkListingProductSources
        filters = [
            sales.tenant_id == req.tenant_id,
            sales.year_month_day >= start_ymd,
            sales.year_month_day <= end_ymd,
        ]
        if req.mall_ids:
            filters.append(sales.mall_id.in_(req.mall_ids))
        if req.country_codes:
            filters.append(sales.country_code.in_(req.country_codes))
        if req.owners:
            filters.append(lps.owner.in_(req.owners))

        sales_sum = func.coalesce(func.sum(sales.sales_volume), 0)
        revenue_sum = func.coalesce(func.sum(sales.sales), 0)
        query = (
            select(
                sales.listing_id,
                sales.mall_id,
                sales.msku,
                func.coalesce(lps.product_name, sales.item_name),
                RlMall.mall_name,
                sales.country_code,
                sales_sum,
                revenue_sum,
            )
            .select_from(
                sales.__table__
                .outerjoin(
                    lps.__table__,
                    (sales.tenant_id == lps.tenant_id)
                    & (sales.listing_id == lps.listing_id),
                )
                .outerjoin(RlMall.__table__, RlMall.mall_id == sales.mall_id)
            )
            .where(*filters)
            .group_by(
                sales.listing_id,
                sales.mall_id,
                sales.msku,
                lps.product_name,
                sales.item_name,
                RlMall.mall_name,
                sales.country_code,
            )
            .order_by(desc(sales_sum))
            .limit(5)
        )
        rows = (await self._session.execute(query)).all()
        return [
            NotificationSkuRow(
                listing_id=listing_id,
                msku=msku or "—",
                product_name=product_name,
                store_name=store_name,
                country_code=country_code,
                sales_7d=int(qty or 0),
                revenue_7d=round(float(revenue or 0), 2),
                reason=f"近 7 天销量 {int(qty or 0)} 件,收入 ${float(revenue or 0):,.2f}",
            )
            for listing_id, _mall_id, msku, product_name, store_name, country_code, qty, revenue in rows
        ]

    async def _risk_summary(
        self, req: NotificationPreviewRequest, calc_run_id: str
    ) -> NotificationRiskSummary:
        stat = MkSupplySkuDailyStat
        lps = MkListingProductSources
        filters = [
            stat.calc_run_id == calc_run_id,
            stat.tenant_id == req.tenant_id,
            stat.delivery_method == "FBA",
        ]
        if req.mall_ids:
            filters.append(stat.mall_id.in_(req.mall_ids))
        if req.country_codes:
            filters.append(stat.country_code.in_(req.country_codes))
        if req.owners:
            filters.append(lps.owner.in_(req.owners))

        query = select(
            func.coalesce(func.sum(case((stat.risk_level == "p1", 1), else_=0)), 0),
            func.coalesce(func.sum(case((stat.risk_level == "p2", 1), else_=0)), 0),
            func.coalesce(func.sum(case((stat.risk_level == "p3", 1), else_=0)), 0),
            func.coalesce(func.sum(case((stat.suggest_purchase == 1, 1), else_=0)), 0),
            func.coalesce(func.sum(stat.suggest_qty), 0),
            func.coalesce(func.sum(stat.suggest_amount_base), 0),
        )
        if req.owners:
            query = query.join(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
        p1, p2, p3, suggest_count, suggest_qty, suggest_amount = (
            await self._session.execute(query.where(*filters))
        ).one()

        calc_run = await self._dashboard_repo.get_calc_run(calc_run_id)
        as_of = calc_run.run_at if calc_run else datetime.utcnow()
        stockout_since = datetime.combine(
            as_of.date() - timedelta(days=6),
            datetime.min.time(),
        )
        stockout_7 = await self._dashboard_repo.stockout_7_count(
            calc_run_id,
            req.tenant_id,
            mall_ids=req.mall_ids,
            country_codes=req.country_codes,
            owners=req.owners,
            stockout_since=stockout_since,
        )
        return NotificationRiskSummary(
            risk_sku_count=int(p1 or 0) + int(p2 or 0) + int(p3 or 0),
            p1_count=int(p1 or 0),
            p2_count=int(p2 or 0),
            stockout_7_count=stockout_7,
            suggest_sku_count=int(suggest_count or 0),
            suggest_total_qty=int(suggest_qty or 0),
            suggest_total_amount=round(float(suggest_amount or 0), 2),
        )

    async def _focus_skus(
        self, req: NotificationPreviewRequest, calc_run_id: str, *, limit: int
    ) -> list[NotificationSkuRow]:
        stat = MkSupplySkuDailyStat
        lps = MkListingProductSources
        filters = [
            stat.calc_run_id == calc_run_id,
            stat.tenant_id == req.tenant_id,
            stat.delivery_method == "FBA",
            stat.risk_level.in_(["p1", "p2"]),
        ]
        if req.mall_ids:
            filters.append(stat.mall_id.in_(req.mall_ids))
        if req.country_codes:
            filters.append(stat.country_code.in_(req.country_codes))
        if req.owners:
            filters.append(lps.owner.in_(req.owners))
        priority_order = case({"p1": 0, "p2": 1, "p3": 2, "safe": 3}, value=stat.risk_level, else_=99)
        query = (
            select(stat, RlMall.mall_name)
            .outerjoin(RlMall, RlMall.mall_id == stat.mall_id)
            .order_by(priority_order.asc(), stat.sellable_days.asc().nulls_last())
            .limit(limit)
        )
        if req.owners:
            query = query.join(
                lps,
                (lps.tenant_id == stat.tenant_id) & (lps.listing_id == stat.listing_id),
            )
        rows = (await self._session.execute(query.where(*filters))).all()
        out: list[NotificationSkuRow] = []
        for row, store_name in rows:
            sellable_days = float(row.sellable_days) if row.sellable_days is not None else None
            reason = (
                f"{row.risk_level.upper()} 风险,可售 {sellable_days:.2f} 天,建议采购 {row.suggest_qty or 0} 件"
                if sellable_days is not None
                else f"{row.risk_level.upper()} 风险,建议采购 {row.suggest_qty or 0} 件"
            )
            out.append(
                NotificationSkuRow(
                    listing_id=row.listing_id,
                    msku=row.msku,
                    product_name=row.product_name,
                    store_name=store_name,
                    country_code=row.country_code,
                    sales_7d=int(row.sales_7d or 0),
                    revenue_7d=round(float(row.revenue_7d or 0), 2),
                    priority=row.risk_level,
                    sellable_days=sellable_days,
                    stockout_date=row.stockout_date.isoformat() if row.stockout_date else None,
                    suggest_qty=int(row.suggest_qty or 0),
                    reason=reason,
                )
            )
        return out

    def _scope_label(self, req: NotificationPreviewRequest) -> str:
        parts: list[str] = []
        if req.owners:
            parts.append("负责人:" + "、".join(req.owners))
        if req.mall_ids:
            parts.append("店铺:" + "、".join(str(v) for v in req.mall_ids))
        if req.country_codes:
            parts.append("国家:" + "、".join(req.country_codes))
        return "全局经营" if not parts else " / ".join(parts)

    def _operator_name(self, req: NotificationPreviewRequest) -> str:
        if req.owners:
            return "、".join(req.owners)
        return "运营负责人"

    def _summary_text(
        self,
        *,
        role_label: str,
        risk: NotificationRiskSummary,
        top_skus: list[NotificationSkuRow],
    ) -> str:
        leader = top_skus[0].msku if top_skus else "暂无"
        return (
            f"{role_label}今日重点:需建议采购 {risk.suggest_sku_count} 个 SKU,"
            f"P1 紧急 {risk.p1_count} 个,7 天内断货 {risk.stockout_7_count} 个;"
            f"近 7 天销量最高为 {leader}。"
        )

    def _action_text(self, role: str, risk: NotificationRiskSummary) -> str:
        if role == "boss":
            return (
                f"优先审批 P1 高风险 SKU 的采购计划,关注 {risk.suggest_total_qty} 件建议采购量"
                f"和 ${risk.suggest_total_amount:,.2f} 预计采购金额。"
            )
        return "先处理 P1 紧急 SKU,再检查在途延迟和 P2 补货,完成后生成采购计划。"

    def _markdown(
        self,
        *,
        title: str,
        subtitle: str,
        report: NotificationReport,
        detail_url: str,
        card_image_url: str,
    ) -> str:
        metric_map = {m.label: m for m in report.finance}

        def metric_value(label: str) -> float:
            return metric_map[label].value

        def metric(label: str) -> str:
            m = metric_map[label]
            if m.unit == "USD":
                return f"${m.value:,.2f}"
            if m.unit:
                return f"{int(m.value):,} {m.unit}"
            return f"{m.value:,.2f}"

        def money_status(value: float) -> str:
            return "✅ 正利润" if value >= 0 else "⚠️ 亏损"

        def risk_status(count: int, *, danger: int) -> str:
            if count >= danger:
                return "🚨 需优先处理"
            if count > 0:
                return "⚠️ 需关注"
            return "✅ 暂无风险"

        def full_product(value: str | None) -> str:
            return value or "未命名商品"

        def top_line(i: int, sku: NotificationSkuRow) -> str:
            return (
                f"{i}. **{sku.msku}**｜{sku.store_name or '未知店铺'}\n"
                f"   商品: {full_product(sku.product_name)}\n"
                f"   近 7 天销量: **{sku.sales_7d} 件**"
            )

        top_detail = "\n\n".join(
            top_line(i, sku)
            for i, sku in enumerate(report.top_skus[:3], 1)
        ) or "暂无销量数据。"
        top_leader = report.top_skus[0] if report.top_skus else None
        leader_text = (
            f"{top_leader.msku}({top_leader.store_name or '未知店铺'})"
            if top_leader
            else "暂无"
        )
        p1_text = (
            f"当前 P1 紧急 SKU 有 **{report.risk.p1_count} 个**,应先确认补货量、供应商和到货时效。"
            if report.risk.p1_count
            else "当前暂无 P1 紧急 SKU,维持日常监控即可。"
        )
        stockout_text = (
            f"近 7 天内断货 SKU 有 **{report.risk.stockout_7_count} 个**,需跟进是否已产生销售损失。"
            if report.risk.stockout_7_count
            else "近 7 天内暂无断货 SKU。"
        )
        profit_text = "当前经营有利润" if metric_value("利润") >= 0 else "当前利润承压"
        core_lines = "\n\n".join(
            [
                f"1. **昨日销量**: {metric('昨日销量')}｜📦 已出单",
                f"2. **收入**: {metric('收入')}｜💰 收入确认",
                f"3. **成本**: {metric('成本')}｜🧾 成本确认",
                f"4. **费用**: {metric('费用')}｜📌 规则估算",
                f"5. **利润**: {metric('利润')}｜{money_status(metric_value('利润'))}",
            ]
        )
        risk_lines = "\n\n".join(
            [
                (
                    "1. **断货风险**: "
                    f"{report.risk.risk_sku_count} SKU｜"
                    f"{risk_status(report.risk.risk_sku_count, danger=20)}"
                ),
                (
                    "2. **P1 紧急**: "
                    f"{report.risk.p1_count} SKU｜"
                    f"{risk_status(report.risk.p1_count, danger=5)}"
                ),
                (
                    "3. **7 天内断货**: "
                    f"{report.risk.stockout_7_count} SKU｜"
                    f"{risk_status(report.risk.stockout_7_count, danger=1)}"
                ),
                f"4. **建议采购**: {report.risk.suggest_sku_count} SKU｜📋 待确认计划",
            ]
        )
        return (
            f"## 🔎 {title}\n\n"
            f"基于最新库存、销量、在途和补货规则,以下是 {subtitle} 的经营简报:\n\n"
            f"---\n\n"
            f"📊 **核心经营速览**\n\n{core_lines}\n\n"
            f"---\n\n"
            f"⚠️ **今日风险概览**\n\n{risk_lines}\n\n"
            f"---\n\n"
            f"🔥 **近 7 天畅销 SKU Top 3**\n\n{top_detail}\n\n"
            f"---\n\n"
            f"💡 **综合判断**\n\n"
            f"**短期（今天-7天）**: ⚠️ **补货压力偏高**\n"
            f"1. {p1_text}\n\n"
            f"**中期（1-4周）**: ➡️ **稳定供给**\n"
            f"1. {stockout_text}\n\n"
            f"**长期（1-3月）**: 📈 **保护畅销 SKU**\n"
            f"1. 近 7 天销量最高为 **{leader_text}**。\n\n"
            f"---\n\n"
            f"📌 **一句话总结**\n\n"
            f"{profit_text},今天优先关注 P1 与断货风险。"
        )

    def card_svg(self, report: NotificationReport, *, title: str, subtitle: str) -> str:
        """生成钉钉 Markdown 中可嵌入的日报卡片图."""
        metric_map = {m.label: m for m in report.finance}

        def metric(label: str) -> str:
            m = metric_map[label]
            if m.unit == "USD":
                return f"${m.value:,.2f}"
            if m.unit:
                return f"{int(m.value):,}{m.unit}"
            return f"{m.value:,.2f}"

        def cut(value: str | None, max_len: int) -> str:
            if not value:
                return "未命名商品"
            return value if len(value) <= max_len else value[:max_len - 1] + "…"

        def store_product(sku: NotificationSkuRow, max_len: int = 25) -> str:
            return f"{sku.store_name or '未知店铺'} · {cut(sku.product_name, max_len)}"

        def rect(x: int, y: int, w: int, h: int, fill: str, stroke: str = "#252833", rx: int = 8) -> str:
            return (
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
            )

        def text(
            x: int,
            y: int,
            value: str,
            *,
            size: int = 18,
            color: str = "#f7f8fb",
            weight: int = 500,
            anchor: str = "start",
        ) -> str:
            return (
                f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
                f'font-weight="{weight}" text-anchor="{anchor}" '
                f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,'
                f'Microsoft YaHei,sans-serif">{escape(value)}</text>'
            )

        width = 760
        height = 930
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">',
            '<rect width="760" height="930" fill="#0b0d12"/>',
            text(24, 45, title, size=26, weight=750),
            text(24, 73, subtitle, size=14, color="#9298a8"),
        ]

        metric_specs = [
            ("昨日销量", metric("昨日销量"), "#aab7ff"),
            ("收入", metric("收入"), "#f7f8fb"),
            ("成本", metric("成本"), "#f7f8fb"),
            ("费用", metric("费用"), "#f7f8fb"),
            ("利润", metric("利润"), "#3fd6a4"),
        ]
        card_w = 134
        for i, (label, value, color) in enumerate(metric_specs):
            x = 24 + i * (card_w + 10)
            parts.append(rect(x, 92, card_w, 82, "#12141a"))
            parts.append(text(x + 12, 121, label, size=13, color="#858b99", weight=600))
            parts.append(text(x + 12, 153, value, size=22, color=color, weight=750))

        parts.append(rect(24, 194, 712, 706, "#111318", "#2a2d37", rx=10))
        parts.append(text(44, 232, "今日关注", size=18, weight=700))
        parts.append(text(390, 232, "建议动作", size=18, weight=700))

        mini_stats = [
            ("断货风险", f"{report.risk.risk_sku_count} SKU", "#aab7ff"),
            ("P1 紧急", f"{report.risk.p1_count} SKU", "#ff6b63"),
            ("7 天内断货", f"{report.risk.stockout_7_count} SKU", "#ffbd6b"),
            ("建议采购", f"{report.risk.suggest_sku_count} SKU", "#aab7ff"),
        ]
        for idx, (label, value, color) in enumerate(mini_stats):
            x = 44 + (idx % 2) * 164
            y = 252 + (idx // 2) * 72
            parts.append(rect(x, y, 150, 58, "#181b21", "#30333d", rx=6))
            parts.append(text(x + 12, y + 23, label, size=12, color="#858b99", weight=600))
            parts.append(text(x + 12, y + 47, value, size=19, color=color, weight=750))

        parts.append(rect(390, 252, 326, 130, "#181b21", "#30333d", rx=6))
        action_lines = [
            f"优先审批 P1 高风险 SKU 的采购计划",
            f"关注 {report.risk.suggest_total_qty} 件建议采购量",
            f"预计采购金额 ${report.risk.suggest_total_amount:,.2f}",
        ]
        for i, line in enumerate(action_lines):
            parts.append(text(410, 284 + i * 30, line, size=15, color="#d6d9e3", weight=600))

        parts.append(text(44, 412, cut(report.summary, 42), size=15, color="#d8dbe5", weight=500))
        parts.append(text(44, 466, "近 7 天畅销 SKU", size=18, weight=700))
        parts.append(text(390, 466, "优先处理 SKU", size=18, weight=700))

        list_y = 488
        row_h = 70
        for i, sku in enumerate(report.top_skus[:5], 1):
            y = list_y + (i - 1) * row_h
            parts.append(rect(44, y, 312, row_h, "#15171d", "#282b35", rx=0))
            parts.append(text(62, y + 41, str(i), size=14, color="#858b99", weight=500))
            parts.append(text(92, y + 28, sku.msku, size=16, weight=750))
            parts.append(text(92, y + 51, store_product(sku, 20), size=12, color="#8d93a3"))
            parts.append(text(334, y + 38, f"{sku.sales_7d} 件", size=15, color="#f7f8fb", weight=750, anchor="end"))

        for i, sku in enumerate(report.focus_skus[:5], 1):
            y = list_y + (i - 1) * row_h
            qty = f"{sku.suggest_qty or 0} 件"
            parts.append(rect(390, y, 326, row_h, "#15171d", "#282b35", rx=0))
            parts.append(text(408, y + 41, str(i), size=14, color="#858b99", weight=500))
            parts.append(text(438, y + 28, sku.msku, size=16, weight=750))
            parts.append(text(438, y + 51, store_product(sku, 18), size=12, color="#8d93a3"))
            parts.append(text(694, y + 38, qty, size=15, color="#ff6b63", weight=750, anchor="end"))

        parts.append("</svg>")
        return "\n".join(parts)

    def _card_image_url(self, req: NotificationPreviewRequest, detail_url: str) -> str:
        parsed = urlparse(detail_url)
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
        api_base = parse_qs(parsed.query).get("api", ["/api/supplyai"])[0]
        if api_base.startswith("http://") or api_base.startswith("https://"):
            base = api_base.rstrip("/")
        else:
            base = f"{origin}{api_base}".rstrip("/")
        params: dict[str, object] = {
            "tenant_id": req.tenant_id,
            "role": req.role,
            "detail_url": detail_url,
        }
        if req.target_name:
            params["target_name"] = req.target_name
        if req.owners:
            params["owners"] = req.owners
        if req.mall_ids:
            params["mall_ids"] = req.mall_ids
        if req.country_codes:
            params["country_codes"] = req.country_codes
        return f"{base}/notifications/dingtalk/card.svg?{urlencode(params, doseq=True)}"

    def _ai_detail_url(self, detail_url: str) -> str:
        parsed = urlparse(detail_url)
        query = parse_qs(parsed.query)
        query["ai"] = ["1"]
        return parsed._replace(query=urlencode(query, doseq=True)).geturl()

    def _dingtalk_action_card(
        self, *, title: str, markdown: str, detail_url: str
    ) -> dict:
        return {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": markdown,
                "btnOrientation": "0",
                "singleTitle": "了解详情",
                "singleURL": detail_url,
            },
        }

    def _signed_webhook_url(self, webhook: str, secret: str | None) -> str:
        if not secret:
            return webhook
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        digest = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        sign = quote_plus(base64.b64encode(digest))
        sep = "&" if "?" in webhook else "?"
        return f"{webhook}{sep}timestamp={timestamp}&sign={sign}"

    def _safe_json(self, resp: httpx.Response) -> dict:
        try:
            data = resp.json()
            return data if isinstance(data, dict) else {"data": data}
        except Exception:  # noqa: BLE001
            return {"text": resp.text[:500]}

    def _dingtalk_ok(self, data: dict | None) -> bool:
        if not data:
            return True
        errcode = data.get("errcode")
        return errcode in (None, 0)
