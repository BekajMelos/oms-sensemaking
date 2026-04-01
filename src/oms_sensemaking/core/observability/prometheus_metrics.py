"""Prometheus metric instruments (histograms and counters)."""

from prometheus_client import Counter, Histogram

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

# EVENTS_PROCESSED counts successful events, EVENTS_FAILED counts failed events
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
