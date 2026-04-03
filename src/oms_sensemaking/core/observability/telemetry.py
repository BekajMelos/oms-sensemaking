"""OpenTelemetry tracing: managers, global instance, and trace helpers."""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

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
    """Manages OpenTelemetry tracing."""

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
        """Initialize OpenTelemetry tracing."""
        if self._initialized:
            LOGGER.info("Observability already initialized")
            return

        self._initialized = True

        try:
            resource = Resource.create({"service.name": SETTINGS.otel_service_name})
            otlp_exporter = OTLPSpanExporter(endpoint=SETTINGS.otel_exporter_otlp_endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            provider = TracerProvider(resource=resource)
            provider.add_span_processor(span_processor)
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(__name__)
            LOGGER.info("OpenTelemetry tracing initialized successfully")
        except Exception as e:
            LOGGER.error(f"Failed to initialize OpenTelemetry: {e}")

    def instrument_fastapi(self, app):
        """Instrument FastAPI application with OpenTelemetry."""
        try:
            FastAPIInstrumentor.instrument_app(app)
            LOGGER.info("FastAPI instrumented with OpenTelemetry")
        except Exception as e:
            LOGGER.error(f"Failed to instrument FastAPI: {e}")

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
            LOGGER.warning(f"Failed to get current trace ID: {e}")
        return None


telemetry_manager: BaseTelemetryManager = TelemetryManager() if SETTINGS.enable_telemetry else NoOpTelemetryManager()


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID for exemplars."""
    return telemetry_manager.get_current_trace_id()
