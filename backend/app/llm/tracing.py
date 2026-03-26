from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from app.core.logging import get_logger

logger = get_logger()


class _NullTracing:
    @contextmanager
    def trace(self, _name: str) -> Iterator[None]:
        yield


def get_tracer(enabled: bool) -> Any:
    if not enabled:
        return _NullTracing()
    try:
        from datapizza.tracing import ContextTracing
    except ImportError:
        logger.warning("datapizza_tracing_missing")
        return _NullTracing()
    return ContextTracing()
