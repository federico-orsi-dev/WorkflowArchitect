from __future__ import annotations

from contextlib import contextmanager

from app.core.logging import get_logger

logger = get_logger()


class _NullTracing:
    @contextmanager
    def trace(self, _name: str):
        yield


def get_tracer(enabled: bool):
    if not enabled:
        return _NullTracing()
    try:
        from datapizza.tracing import ContextTracing  # type: ignore
    except ImportError:
        logger.warning("datapizza_tracing_missing")
        return _NullTracing()
    return ContextTracing()
