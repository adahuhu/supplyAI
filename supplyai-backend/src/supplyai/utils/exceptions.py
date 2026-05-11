"""业务异常类."""
from __future__ import annotations

from fastapi import HTTPException


class BusinessException(HTTPException):
    """业务异常基类 — 默认 HTTP 400."""

    code: str = "BUSINESS_ERROR"

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": self.code, "message": message},
        )


class CalcRunNotFoundException(BusinessException):
    code = "CALC_RUN_NOT_FOUND"

    def __init__(
        self,
        tenant_id: int | None = None,
        *,
        calc_run_id: str | None = None,
    ) -> None:
        if calc_run_id:
            message = f"未找到 calc_run_id={calc_run_id} 的批次记录。"
        else:
            message = f"未找到租户 {tenant_id} 的最新计算批次,请先执行 calc.run。"
        super().__init__(message, status_code=404)


class FbmNotSupportedException(BusinessException):
    """FBM 商品当前 Phase 不支持备货分析(数据表设计 §11)."""

    code = "FBM_NOT_SUPPORTED"

    def __init__(self, listing_id: int) -> None:
        super().__init__(
            f"Listing {listing_id} 是 FBM 商品,Phase 1 暂不支持备货分析。",
            status_code=400,
        )


class SkuNotFoundException(BusinessException):
    code = "SKU_NOT_FOUND"

    def __init__(self, listing_id: int) -> None:
        super().__init__(f"未找到 listing_id={listing_id} 的 SKU。", status_code=404)


class DraftNotFoundException(BusinessException):
    code = "DRAFT_NOT_FOUND"

    def __init__(self, draft_id: str) -> None:
        super().__init__(f"未找到 draft_id={draft_id} 的草稿。", status_code=404)


class InvalidDraftQtyException(BusinessException):
    code = "INVALID_DRAFT_QTY"

    def __init__(self) -> None:
        super().__init__("草稿数量必须 > 0。", status_code=400)


class DraftInvalidTransitionException(BusinessException):
    code = "DRAFT_INVALID_TRANSITION"

    def __init__(self, from_state: str, to_state: str) -> None:
        super().__init__(
            f"草稿无法从 {from_state} 切换到 {to_state}。",
            status_code=400,
        )


class ExportTaskNotFoundException(BusinessException):
    code = "EXPORT_TASK_NOT_FOUND"

    def __init__(self, task_id: str) -> None:
        super().__init__(f"未找到 task_id={task_id} 的导出任务。", status_code=404)


class ExportFileMissingException(BusinessException):
    code = "EXPORT_FILE_MISSING"

    def __init__(self, task_id: str) -> None:
        super().__init__(
            f"导出任务 {task_id} 文件已过期或丢失,请重新触发导出。",
            status_code=410,
        )


class RuleNotFoundException(BusinessException):
    code = "RULE_NOT_FOUND"

    def __init__(self, rule_id: str) -> None:
        super().__init__(f"未找到 rule_id={rule_id} 的规则。", status_code=404)


class RuleInvalidScopeException(BusinessException):
    code = "RULE_INVALID_SCOPE"

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


class AiEmptyMessagesException(BusinessException):
    code = "AI_EMPTY_MESSAGES"

    def __init__(self) -> None:
        super().__init__("AI 对话至少需要一条用户消息。", status_code=400)
