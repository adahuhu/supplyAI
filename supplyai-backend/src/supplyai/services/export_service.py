"""导出服务 — Phase 1 同步生成 xlsx 落本地磁盘."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import Workbook

from supplyai.config import settings
from supplyai.models.mk import MkExportTask
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.repositories.sku_repo import SkuRepository
from supplyai.schemas.export import ExportSkuListRequest, ExportTaskDTO
from supplyai.services.sku_service import _row_to_dto
from supplyai.utils.exceptions import (
    CalcRunNotFoundException,
    ExportFileMissingException,
    ExportTaskNotFoundException,
)

XLSX_HEADERS = [
    "MSKU",
    "SKU",
    "ASIN",
    "商品名称",
    "店铺",
    "国家",
    "风险等级",
    "未来日均",
    "总库存",
    "可售天数",
    "断货日期",
    "采购日期",
    "建议数量",
    "建议金额(基准币)",
    "基准币种",
    "calc_run_id",
]


class ExportService:
    def __init__(
        self,
        session,
        sku_repo: SkuRepository,
        dashboard_repo: DashboardRepository,
    ) -> None:
        self._session = session
        self._sku_repo = sku_repo
        self._dashboard_repo = dashboard_repo

    async def export_sku_list(self, req: ExportSkuListRequest) -> ExportTaskDTO:
        """生成 sku-list.xlsx 并落盘."""
        calc_run_id = req.calc_run_id or await self._dashboard_repo.latest_calc_run_id(
            req.tenant_id
        )
        if not calc_run_id:
            raise CalcRunNotFoundException(req.tenant_id)

        # 拉一次全量(忽略 page,导出场景下可接受)
        rows, total = await self._sku_repo.list_skus(
            calc_run_id=calc_run_id,
            tenant_id=req.tenant_id,
            priorities=req.priorities,
            mall_ids=req.mall_ids,
            country_codes=req.country_codes,
            tags=req.tags,
            keyword=req.keyword,
            suggest_only=req.suggest_only,
            page=1,
            page_size=100000,
        )

        task_id = self._new_task_id()
        export_dir = Path(settings.export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        file_path = export_dir / f"{task_id}.xlsx"

        wb = Workbook()
        ws = wb.active
        ws.title = "SKU"
        ws.append(XLSX_HEADERS)
        for stat, lps, mall_name in rows:
            dto = _row_to_dto(stat, lps, mall_name)
            ws.append(
                [
                    dto.msku,
                    dto.sku,
                    dto.asin,
                    dto.product_name,
                    dto.store_name,
                    dto.country_code,
                    dto.priority,
                    dto.future_daily,
                    dto.total_stock,
                    dto.sellable_days,
                    dto.stockout_date.isoformat() if dto.stockout_date else None,
                    dto.purchase_date.isoformat() if dto.purchase_date else None,
                    dto.suggest_qty,
                    dto.suggest_amount_base,
                    dto.base_currency,
                    dto.calc_run_id,
                ]
            )
        wb.save(file_path)

        now = datetime.utcnow()
        task = MkExportTask(
            task_id=task_id,
            tenant_id=req.tenant_id,
            created_by=req.created_by,
            scope_json=req.model_dump(exclude_none=True),
            row_count=total,
            status="success",
            file_url=str(file_path),
            expires_at=now + timedelta(days=7),
            created_at=now,
            updated_at=now,
        )
        self._session.add(task)
        await self._session.flush()
        return ExportTaskDTO.model_validate(task)

    async def get_status(self, *, tenant_id: int, task_id: str) -> ExportTaskDTO:
        task = await self._fetch(tenant_id=tenant_id, task_id=task_id)
        return ExportTaskDTO.model_validate(task)

    async def load_file_bytes(self, *, tenant_id: int, task_id: str) -> tuple[bytes, str]:
        task = await self._fetch(tenant_id=tenant_id, task_id=task_id)
        if not task.file_url:
            raise ExportFileMissingException(task_id)
        path = Path(task.file_url)
        if not path.exists():
            raise ExportFileMissingException(task_id)
        return path.read_bytes(), path.name

    async def _fetch(self, *, tenant_id: int, task_id: str) -> MkExportTask:
        from sqlalchemy import select

        task = await self._session.scalar(
            select(MkExportTask).where(
                MkExportTask.tenant_id == tenant_id,
                MkExportTask.task_id == task_id,
            )
        )
        if task is None:
            raise ExportTaskNotFoundException(task_id)
        return task

    @staticmethod
    def _new_task_id() -> str:
        return f"EXP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3)}"
