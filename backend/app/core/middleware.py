from __future__ import annotations

import threading
import time
import uuid
from typing import Any, cast

import structlog
from fastapi.responses import JSONResponse
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, header_name: str = "X-Request-Id") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
        self,
        request: Request,
        call_next: Any,
    ) -> Response:
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers[self.header_name] = request_id
        return cast(Response, response)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, limit_per_minute: int = 60) -> None:
        super().__init__(app)
        self.limit_per_minute = limit_per_minute
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[int, float]] = {}

    async def dispatch(
        self,
        request: Request,
        call_next: Any,
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        with self._lock:
            count, timestamp = self._buckets.get(client_ip, (0, now))
            if timestamp < window_start:
                count, timestamp = 0, now
            count += 1
            self._buckets[client_ip] = (count, timestamp)
            allowed = count <= self.limit_per_minute

        if not allowed:
            structlog.get_logger().warning("rate_limit_exceeded", client_ip=client_ip)
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

        return cast(Response, await call_next(request))
