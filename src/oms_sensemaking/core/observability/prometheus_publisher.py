"""Prometheus-backed metrics publisher and default app instance."""

import logging

from oms_sensemaking.config import SETTINGS

from .base_publisher import MetricsPublisher
from .prometheus_metrics import (
    EVENTS_FAILED,
    EVENTS_PROCESSED,
    QUEUE_PROCESSING_TIME,
    REQUESTS_PROCESSING_TIME,
    REQUESTS_TOTAL,
)

LOGGER: logging.Logger = logging.getLogger(__name__)


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
