"""Middleware for request timing and metrics collection."""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from oms_sensemaking.core.observability import record_request_metrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics and timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        record_request_metrics(
            method=request.method, path=request.url.path, status_code=response.status_code, duration=duration
        )

        return response
