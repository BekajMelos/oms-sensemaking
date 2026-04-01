"""Metrics publisher abstract base and Prometheus implementation."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from oms_sensemaking.config import SETTINGS

from .prometheus_metrics import (
    EVENTS_FAILED,
    EVENTS_PROCESSED,
    QUEUE_PROCESSING_TIME,
    REQUESTS_PROCESSING_TIME,
    REQUESTS_TOTAL,
)
from .telemetry import get_current_trace_id

LOGGER: logging.Logger = logging.getLogger(__name__)


class MetricsPublisher(ABC):
    """Contract for metrics backends: subclass this, implement abstract hooks, inherit completion helpers."""

    def __init__(self, app_name: str):
        self.app_name = app_name

    @abstractmethod
    def record_request(self, method: str, path: str, status_code: int, duration: float) -> None:
        """Record request metrics in backend-specific storage."""
        pass

    @abstractmethod
    def record_queue_processing_time(self, queue_name: str, processing_time_seconds: float) -> None:
        """Record queue processing time in backend-specific storage."""
        pass

    @abstractmethod
    def record_event_processed(self, queue_name: str) -> None:
        """Record successful event count in backend-specific storage."""
        pass

    @abstractmethod
    def record_event_failed(self, queue_name: str) -> None:
        """Record failed event count in backend-specific storage."""
        pass

    def record_processing_completion(self, queue_name: str, start_time: float, success: bool = True) -> None:
        """Generic completion recording used by all publisher implementations."""
        processing_time = time.time() - start_time
        self.record_queue_processing_time(queue_name, processing_time)

        if success:
            self.record_event_processed(queue_name)
        else:
            self.record_event_failed(queue_name)

    def record_processing_success(self, queue_name: str, start_time: float) -> None:
        """Generic helper for successful completion."""
        self.record_processing_completion(queue_name, start_time, success=True)

    def record_processing_failure(self, queue_name: str, start_time: float) -> None:
        """Generic helper for failed completion."""
        self.record_processing_completion(queue_name, start_time, success=False)

    def _get_trace_exemplar(self) -> Optional[dict]:
        """Generic helper for trace exemplar construction."""
        trace_id = get_current_trace_id()
        return {"TraceID": trace_id} if trace_id else None


class PrometheusMetricsPublisher(MetricsPublisher):
    """Prometheus-backed implementation of metrics publishing."""

    def record_request(self, method: str, path: str, status_code: int, duration: float) -> None:
        exemplar = self._get_trace_exemplar()

        REQUESTS_PROCESSING_TIME.labels(method=method, path=path, app_name=self.app_name).observe(
            duration, exemplar=exemplar
        )
        REQUESTS_TOTAL.labels(method=method, path=path, status_code=status_code, app_name=self.app_name).inc()

    def record_queue_processing_time(self, queue_name: str, processing_time_seconds: float) -> None:
        exemplar = self._get_trace_exemplar()
        QUEUE_PROCESSING_TIME.labels(queue_name=queue_name, app_name=self.app_name).observe(
            processing_time_seconds, exemplar=exemplar
        )
        LOGGER.debug(f"Queue processing time recorded: {queue_name} = {processing_time_seconds:.4f}s")

    def record_event_processed(self, queue_name: str) -> None:
        EVENTS_PROCESSED.labels(queue_name=queue_name, app_name=self.app_name).inc()
        LOGGER.debug(f"Event processed counter incremented for queue: {queue_name}")

    def record_event_failed(self, queue_name: str) -> None:
        EVENTS_FAILED.labels(queue_name=queue_name, app_name=self.app_name).inc()
        LOGGER.debug(f"Event failed counter incremented for queue: {queue_name}")


metrics_publisher: MetricsPublisher = PrometheusMetricsPublisher(SETTINGS.otel_service_name)
