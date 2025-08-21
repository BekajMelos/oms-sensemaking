import logging
from typing import Optional

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from oms_sensemaking.config import SETTINGS

LOGGER = logging.getLogger(__name__)


class TelemetryManager:
    def __init__(self):
        if not SETTINGS.enable_telemetry:
            LOGGER.info("Telemetry is disabled in configuration")
            self.meter = None
            self.queue_processing_time = None
            self.events_processed = None
            self.events_failed = None
            self.hello_world_counter = None
            return

        self._setup_opentelemetry()
        self._create_metrics()
        try:
            if self.hello_world_counter:
                self.hello_world_counter.add(1)
                LOGGER.info("Hello world metric incremented")
        except Exception as exc:
            LOGGER.error(f"Failed to increment hello world metric: {exc}")

    def _setup_opentelemetry(self):
        try:
            exporter = OTLPMetricExporter(endpoint="http://prometheus:9090/api/v1/otlp/v1/metrics")
            reader = PeriodicExportingMetricReader(exporter)
            provider = MeterProvider(metric_readers=[reader])

            metrics.set_meter_provider(provider)

            LOGGER.info("OpenTelemetry metrics initialized successfully")

        except Exception as e:
            LOGGER.error(f"Failed to initialize OpenTelemetry: {e}")

    def _create_metrics(self):
        try:
            self.meter = metrics.get_meter(__name__)

            self.hello_world_counter = self.meter.create_counter(
                name="hello_world",
                description="Simple hello world metric",
                unit="1",
            )

            self.queue_processing_time = self.meter.create_histogram(
                name="queue_processing_time_seconds",
                description="Time from reading object from queue to being processed",
                unit="s",
            )

            self.events_processed = self.meter.create_counter(
                name="events_processed_total", description="Total number of events processed by queue", unit="1"
            )

            self.events_failed = self.meter.create_counter(
                name="events_failed_total", description="Total number of events that failed processing", unit="1"
            )

            LOGGER.info("Telemetry metrics created successfully")

        except Exception as e:
            LOGGER.error(f"Failed to create telemetry metrics: {e}")
            self.meter = None
            self.hello_world_counter = None
            self.queue_processing_time = None
            self.events_processed = None
            self.events_failed = None

    def record_queue_processing_time(self, queue_name: str, processing_time_seconds: float):
        if not SETTINGS.enable_telemetry or not self.queue_processing_time:
            return

        try:
            self.queue_processing_time.record(processing_time_seconds, attributes={"queue_name": queue_name})

            LOGGER.info(f"Queue processing time recorded: {queue_name} = {processing_time_seconds:.4f}s")

        except Exception as e:
            LOGGER.error(f"Failed to record queue processing time: {e}")

    def record_event_processed(self, queue_name: str):
        if not SETTINGS.enable_telemetry or not self.events_processed:
            return

        try:
            self.events_processed.add(1, attributes={"queue_name": queue_name})
            LOGGER.debug(f"Event processed counter incremented for queue: {queue_name}")
        except Exception as e:
            LOGGER.error(f"Failed to record event processed: {e}")

    def record_event_failed(self, queue_name: str):
        if not SETTINGS.enable_telemetry or not self.events_failed:
            return

        try:
            self.events_failed.add(1, attributes={"queue_name": queue_name})
            LOGGER.debug(f"Event failed counter incremented for queue: {queue_name}")
        except Exception as e:
            LOGGER.error(f"Failed to record event failed: {e}")


telemetry_manager: Optional[TelemetryManager] = None


def get_telemetry_manager() -> TelemetryManager:
    global telemetry_manager
    if telemetry_manager is None:
        telemetry_manager = TelemetryManager()
    return telemetry_manager


def initialize_telemetry():
    get_telemetry_manager()


def record_processing_completion(queue_name: str, start_time: float, success: bool = True):
    if not SETTINGS.enable_telemetry:
        return

    try:
        from time import time

        processing_time = time() - start_time

        telemetry_manager = get_telemetry_manager()
        telemetry_manager.record_queue_processing_time(queue_name, processing_time)

        if success:
            telemetry_manager.record_event_processed(queue_name)
        else:
            telemetry_manager.record_event_failed(queue_name)

    except Exception as e:
        LOGGER.error(f"Failed to record processing completion: {e}")


def record_processing_success(queue_name: str, start_time: float):
    record_processing_completion(queue_name, start_time, success=True)


def record_processing_failure(queue_name: str, start_time: float):
    record_processing_completion(queue_name, start_time, success=False)
