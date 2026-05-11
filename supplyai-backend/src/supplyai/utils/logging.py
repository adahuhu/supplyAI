"""structlog 日志配置."""
from __future__ import annotations

import logging
import sys
from typing import Literal

import structlog
from structlog.types import Processor


def configure_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    fmt: Literal["console", "json"] = "console",
) -> None:
    """配置全局日志.

    本地开发用 console 友好格式;生产用 json 给日志收集。
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
    ]

    if fmt == "json":
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # 同步标准库 logging level
    logging.basicConfig(level=getattr(logging, level), stream=sys.stdout)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取一个 structlog logger."""
    return structlog.get_logger(name)
