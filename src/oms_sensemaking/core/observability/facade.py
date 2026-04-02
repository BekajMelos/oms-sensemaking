"""Application-facing observability helpers (metrics wrappers, HTTP endpoint, spans)."""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from .prometheus_publisher import metrics_publisher
from .telemetry import telemetry_manager

LOGGER: logging.Logger = logging.getLogger(__name__)


def initialize_observability():
    """Initialize OpenTelemetry tracing and Prometheus metrics."""
    telemetry_manager.initialize()


def instrument_fastapi(app):
    """Instrument FastAPI application with OpenTelemetry."""
    telemetry_manager.instrument_fastapi(app)


def record_request_metrics(method: str, path: str, status_code: int, duration: float):
    """Record request metrics with trace exemplars."""
    try:
        metrics_publisher.record_request(method, path, status_code, duration)
    except Exception as e:
        LOGGER.error(f"Failed to record request metrics: {e}")


def record_processing_success(queue_name: str, start_time: float):
    """Record successful processing completion."""
    try:
        metrics_publisher.record_processing_success(queue_name, start_time)
    except Exception as e:
        LOGGER.error(f"Failed to record processing success: {e}")


def record_processing_failure(queue_name: str, start_time: float):
    """Record failed processing completion."""
    try:
        metrics_publisher.record_processing_failure(queue_name, start_time)
    except Exception as e:
        LOGGER.error(f"Failed to record processing failure: {e}")


def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint with OpenMetrics format and exemplars."""
    return Response(generate_latest(REGISTRY), headers={"Content-Type": CONTENT_TYPE_LATEST})


@asynccontextmanager
async def trace_span(name: str, attributes: Optional[dict] = None):
    """Context manager for creating trace spans."""
    tracer = telemetry_manager.get_tracer()
    if not tracer:
        yield
        return

    try:
        with tracer.start_as_current_span(name, attributes=attributes or {}) as span:
            yield span
    except Exception as e:
        LOGGER.error(f"Failed to create trace span: {e}")
        yield None
