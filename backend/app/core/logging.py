from __future__ import annotations

import logging
import sys
from typing import cast

import structlog


def configure_logging(log_level: str) -> None:
    resolved_level = logging.getLevelName(log_level.upper())
    if isinstance(resolved_level, str):
        resolved_level = logging.INFO

    logging.basicConfig(stream=sys.stdout, level=resolved_level, format="%(message)s")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(resolved_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger() -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger())
