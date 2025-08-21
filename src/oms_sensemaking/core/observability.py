"""Observability module for OMS Sensemaking using OpenTelemetry, Prometheus, and structured logging."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST, generate_latest
from prometheus_client.registry import REGISTRY
from starlette.responses import Response

from oms_sensemaking.config import SETTINGS

# Configure logging with trace context and structured format
LoggingInstrumentor().instrument(
    set_logging_format=True,
    log_level=logging.INFO,
)

# Configure structured logging format
logging.basicConfig(
    level=logging.INFO,
    format=(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"name": "%(name)s", "message": "%(message)s", '
        '"trace_id": "%(otelTraceID)s", "span_id": "%(otelSpanID)s"}'
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Prometheus metrics with exemplars
REQUESTS_PROCESSING_TIME = Histogram(
    "fastapi_requests_duration_seconds",
    "Histogram of requests processing time by path (in seconds)",
    ["method", "path", "app_name"],
)

REQUESTS_TOTAL = Counter(
    "fastapi_requests_total",
    "Total number of requests by path and status",
    ["method", "path", "status_code", "app_name"],
)

QUEUE_PROCESSING_TIME = Histogram(
    "queue_processing_time_seconds",
    "Time from reading object from queue to being processed",
    ["queue_name", "app_name"],
)

EVENTS_PROCESSED = Counter(
    "events_processed_total",
    "Total number of events processed by queue",
    ["queue_name", "app_name"],
)

EVENTS_FAILED = Counter(
    "events_failed_total",
    "Total number of events that failed processing",
    ["queue_name", "app_name"],
)

# OpenTelemetry tracer
tracer = None


def initialize_observability():
    """Initialize OpenTelemetry tracing and Prometheus metrics."""
    global tracer

    if not SETTINGS.enable_telemetry:
        logging.info("Observability is disabled in configuration")
        return

    try:
        # Set up OpenTelemetry tracing
        resource = Resource.create({"service.name": "oms-sensemaking"})

        # OTLP exporter for traces
        otlp_exporter = OTLPSpanExporter(endpoint=SETTINGS.otel_exporter_otlp_endpoint or "http://tempo:4317")

        # Batch span processor
        span_processor = BatchSpanProcessor(otlp_exporter)

        # Tracer provider
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(span_processor)

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer
        tracer = trace.get_tracer(__name__)

        logging.info("OpenTelemetry tracing initialized successfully")

    except Exception as e:
        logging.error(f"Failed to initialize OpenTelemetry: {e}")


def instrument_fastapi(app):
    """Instrument FastAPI application with OpenTelemetry."""
    if not SETTINGS.enable_telemetry:
        return

    try:
        FastAPIInstrumentor.instrument_app(app)
        logging.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logging.error(f"Failed to instrument FastAPI: {e}")


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID for exemplars."""
    try:
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            return trace.format_trace_id(span.get_span_context().trace_id)
    except Exception:
        pass
    return None


def record_request_metrics(method: str, path: str, status_code: int, duration: float):
    """Record request metrics with trace exemplars."""
    if not SETTINGS.enable_telemetry:
        return

    try:
        trace_id = get_current_trace_id()
        exemplar = {"TraceID": trace_id} if trace_id else None

        # Record duration with exemplar
        REQUESTS_PROCESSING_TIME.labels(method=method, path=path, app_name="oms-sensemaking").observe(
            duration, exemplar=exemplar
        )

        # Record total requests
        REQUESTS_TOTAL.labels(method=method, path=path, status_code=status_code, app_name="oms-sensemaking").inc()

    except Exception as e:
        logging.error(f"Failed to record request metrics: {e}")


def record_queue_processing_time(queue_name: str, processing_time_seconds: float):
    """Record queue processing time with trace exemplars."""
    if not SETTINGS.enable_telemetry:
        return

    try:
        trace_id = get_current_trace_id()
        exemplar = {"TraceID": trace_id} if trace_id else None

        QUEUE_PROCESSING_TIME.labels(queue_name=queue_name, app_name="oms-sensemaking").observe(
            processing_time_seconds, exemplar=exemplar
        )

        logging.info(f"Queue processing time recorded: {queue_name} = {processing_time_seconds:.4f}s")

    except Exception as e:
        logging.error(f"Failed to record queue processing time: {e}")


def record_event_processed(queue_name: str):
    """Record event processed counter."""
    if not SETTINGS.enable_telemetry:
        return

    try:
        EVENTS_PROCESSED.labels(queue_name=queue_name, app_name="oms-sensemaking").inc()

        logging.debug(f"Event processed counter incremented for queue: {queue_name}")

    except Exception as e:
        logging.error(f"Failed to record event processed: {e}")


def record_event_failed(queue_name: str):
    """Record event failed counter."""
    if not SETTINGS.enable_telemetry:
        return

    try:
        EVENTS_FAILED.labels(queue_name=queue_name, app_name="oms-sensemaking").inc()

        logging.debug(f"Event failed counter incremented for queue: {queue_name}")

    except Exception as e:
        logging.error(f"Failed to record event failed: {e}")


def record_processing_completion(queue_name: str, start_time: float, success: bool = True):
    """Record processing completion with timing and success/failure."""
    if not SETTINGS.enable_telemetry:
        return

    try:
        processing_time = time.time() - start_time

        record_queue_processing_time(queue_name, processing_time)

        if success:
            record_event_processed(queue_name)
        else:
            record_event_failed(queue_name)

    except Exception as e:
        logging.error(f"Failed to record processing completion: {e}")


def record_processing_success(queue_name: str, start_time: float):
    """Record successful processing completion."""
    record_processing_completion(queue_name, start_time, success=True)


def record_processing_failure(queue_name: str, start_time: float):
    """Record failed processing completion."""
    record_processing_completion(queue_name, start_time, success=False)


def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint with OpenMetrics format and exemplars."""
    return Response(generate_latest(REGISTRY), headers={"Content-Type": CONTENT_TYPE_LATEST})


@asynccontextmanager
async def trace_span(name: str, attributes: Optional[dict] = None):
    """Context manager for creating trace spans."""
    if not SETTINGS.enable_telemetry or not tracer:
        yield
        return

    try:
        with tracer.start_as_current_span(name, attributes=attributes or {}) as span:
            yield span
    except Exception as e:
        logging.error(f"Failed to create trace span: {e}")
        yield None
