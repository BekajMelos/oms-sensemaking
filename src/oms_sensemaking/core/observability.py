"""Observability module for OpenTelemetry tracing and Prometheus metrics."""

import logging
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from functools import wraps
from typing import Optional

from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Histogram, generate_latest

from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)


class BaseTelemetryManager(ABC):
    """Base class for telemetry management."""

    @abstractmethod
    def initialize(self):
        """Initialize telemetry systems."""
        pass

    @abstractmethod
    def instrument_fastapi(self, app):
        """Instrument FastAPI application."""
        pass

    @abstractmethod
    def get_tracer(self):
        """Get the current tracer instance."""
        pass

    @abstractmethod
    def get_current_trace_id(self) -> Optional[str]:
        """Get the current trace ID for exemplars."""
        pass


class NoOpTelemetryManager(BaseTelemetryManager):
    """No-op implementation of TelemetryManager for when telemetry is disabled."""

    def initialize(self):
        """No-op initialization."""
        pass

    def instrument_fastapi(self, app):
        """No-op FastAPI instrumentation."""
        pass

    def get_tracer(self):
        """No-op tracer getter."""
        return None

    def get_current_trace_id(self) -> Optional[str]:
        """No-op trace ID getter."""
        return None


class TelemetryManager(BaseTelemetryManager):
    """Manages OpenTelemetry tracing and Prometheus metrics."""

    _instance = None
    _tracer = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelemetryManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Pass through init"""
        pass

    def initialize(self):
        """Initialize OpenTelemetry tracing and Prometheus metrics."""
        if self._initialized:
            logging.info("Observability already initialized")
            return

        self._initialized = True

        try:
            # Set up OpenTelemetry tracing
            resource = Resource.create({"service.name": "oms-sensemaking"})

            # OTLP exporter for traces
            otlp_exporter = OTLPSpanExporter(endpoint=SETTINGS.otel_exporter_otlp_endpoint)

            # Batch span processor
            span_processor = BatchSpanProcessor(otlp_exporter)

            # Tracer provider
            provider = TracerProvider(resource=resource)
            provider.add_span_processor(span_processor)

            # Set global tracer provider
            trace.set_tracer_provider(provider)

            # Get tracer
            self._tracer = trace.get_tracer(__name__)

            logging.info("OpenTelemetry tracing initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize OpenTelemetry: {e}")

    def instrument_fastapi(self, app):
        """Instrument FastAPI application with OpenTelemetry."""
        try:
            FastAPIInstrumentor.instrument_app(app)
            logging.info("FastAPI instrumented with OpenTelemetry")
        except Exception as e:
            logging.error(f"Failed to instrument FastAPI: {e}")

    def get_tracer(self):
        """Get the current tracer instance."""
        return self._tracer

    def get_current_trace_id(self) -> Optional[str]:
        """Get the current trace ID for exemplars."""
        try:
            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                return trace.format_trace_id(span.get_span_context().trace_id)
        except Exception as e:
            logging.warning(f"Failed to get current trace ID: {e}")
        return None


# Global instance of TelemetryManager - conditionally use NoOp or real implementation
telemetry_manager: BaseTelemetryManager = TelemetryManager() if SETTINGS.enable_telemetry else NoOpTelemetryManager()


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

# Event counters: EVENTS_PROCESSED counts successful events, EVENTS_FAILED counts failed events
# Total events handled = EVENTS_PROCESSED + EVENTS_FAILED
EVENTS_PROCESSED = Counter(
    "events_processed_total",
    "Total number of events successfully processed by queue",
    ["queue_name", "app_name"],
)

EVENTS_FAILED = Counter(
    "events_failed_total",
    "Total number of events that failed processing",
    ["queue_name", "app_name"],
)


def initialize_observability():
    """Initialize OpenTelemetry tracing and Prometheus metrics."""
    telemetry_manager.initialize()


def instrument_fastapi(app):
    """Instrument FastAPI application with OpenTelemetry."""
    telemetry_manager.instrument_fastapi(app)


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID for exemplars."""
    return telemetry_manager.get_current_trace_id()


def record_request_metrics(method: str, path: str, status_code: int, duration: float):
    """Record request metrics with trace exemplars."""
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
    try:
        EVENTS_PROCESSED.labels(queue_name=queue_name, app_name="oms-sensemaking").inc()

        logging.debug(f"Event processed counter incremented for queue: {queue_name}")

    except Exception as e:
        logging.error(f"Failed to record event processed: {e}")


def record_event_failed(queue_name: str):
    """Record event failed counter."""
    try:
        EVENTS_FAILED.labels(queue_name=queue_name, app_name="oms-sensemaking").inc()

        logging.debug(f"Event failed counter incremented for queue: {queue_name}")

    except Exception as e:
        logging.error(f"Failed to record event failed: {e}")


def record_processing_completion(queue_name: str, start_time: float, success: bool = True):
    """Record processing completion with timing and success/failure."""
    try:
        processing_time = time.time() - start_time

        # Always record processing time for any completed event
        record_queue_processing_time(queue_name, processing_time)

        # Record success/failure separately
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


def with_metrics_collection(func):
    """Decorator to add metrics collection to handle_event methods."""

    @wraps(func)
    def wrapper(self, event, *args, **kwargs):
        start_time = time.time()
        queue_name = getattr(self.event_consumer, "_queue_name", "unknown")

        try:
            result = func(self, event, *args, **kwargs)
            # Record successful processing
            record_processing_success(queue_name, start_time)
            return result
        except Exception as e:
            # Record failed processing
            record_processing_failure(queue_name, start_time)
            raise e

    return wrapper


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
        logging.error(f"Failed to create trace span: {e}")
        yield None
