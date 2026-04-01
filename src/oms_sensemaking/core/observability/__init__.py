"""Observability: OpenTelemetry tracing, Prometheus metrics, and public helpers."""

from .base_publisher import MetricsPublisher
from .facade import (
    initialize_observability,
    instrument_fastapi,
    metrics_endpoint,
    record_processing_failure,
    record_processing_success,
    record_request_metrics,
    trace_span,
)
from .prometheus_metrics import (
    EVENTS_FAILED,
    EVENTS_PROCESSED,
    QUEUE_PROCESSING_TIME,
    REQUESTS_PROCESSING_TIME,
    REQUESTS_TOTAL,
)
from .prometheus_publisher import PrometheusMetricsPublisher, metrics_publisher
from .telemetry import (
    BaseTelemetryManager,
    NoOpTelemetryManager,
    TelemetryManager,
    get_current_trace_id,
    telemetry_manager,
)

__all__ = [
    "BaseTelemetryManager",
    "EVENTS_FAILED",
    "EVENTS_PROCESSED",
    "MetricsPublisher",
    "NoOpTelemetryManager",
    "PrometheusMetricsPublisher",
    "QUEUE_PROCESSING_TIME",
    "REQUESTS_PROCESSING_TIME",
    "REQUESTS_TOTAL",
    "TelemetryManager",
    "get_current_trace_id",
    "initialize_observability",
    "instrument_fastapi",
    "metrics_endpoint",
    "metrics_publisher",
    "record_processing_failure",
    "record_processing_success",
    "record_request_metrics",
    "telemetry_manager",
    "trace_span",
]
