"""导出 API — POST 触发 + 状态 + 下载."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.db import get_db_session
from supplyai.repositories.dashboard_repo import DashboardRepository
from supplyai.repositories.sku_repo import SkuRepository
from supplyai.schemas.export import (
    ExportSkuListRequest,
    ExportTaskDTO,
    ExportTaskRequest,
)
from supplyai.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])

XLSX_MIME = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def _build_service(session: AsyncSession) -> ExportService:
    return ExportService(
        session=session,
        sku_repo=SkuRepository(session),
        dashboard_repo=DashboardRepository(session),
    )


@router.post("/sku-list", response_model=ExportTaskDTO)
async def export_sku_list(
    req: ExportSkuListRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExportTaskDTO:
    """SKU 列表导出 — Phase 1 同步生成 xlsx,返回 task 元信息."""
    result = await _build_service(session).export_sku_list(req)
    await session.commit()
    return result


@router.post("/status", response_model=ExportTaskDTO)
async def export_status(
    req: ExportTaskRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExportTaskDTO:
    """查询导出任务状态."""
    return await _build_service(session).get_status(
        tenant_id=req.tenant_id, task_id=req.task_id
    )


@router.post("/download")
async def export_download(
    req: ExportTaskRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    """下载导出文件 — 返回 xlsx 字节流."""
    content, filename = await _build_service(session).load_file_bytes(
        tenant_id=req.tenant_id, task_id=req.task_id
    )
    return Response(
        content=content,
        media_type=XLSX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
