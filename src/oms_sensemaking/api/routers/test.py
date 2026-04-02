"""Test endpoints for observability and development testing."""

import logging
import time

from fastapi import APIRouter

from oms_sensemaking.core.observability import record_processing_failure, record_processing_success

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.post("/hello-world")
def generate_hello_world_events():
    """Generate hello_world events for observability testing."""
    start_time = time.time()

    # Generate some successful events
    for i in range(3):
        processing_time = 0.1 + (i * 0.05)
        record_processing_success("hello_world", time.time() - processing_time)
        time.sleep(0.1)

    # Generate some failed events
    for _i in range(2):
        fail_start = time.time()
        record_processing_failure("hello_world", fail_start)
        time.sleep(0.05)

    total_time = time.time() - start_time

    return {
        "message": "Hello world events generated!",
        "events_processed": 3,
        "events_failed": 2,
        "total_time": f"{total_time:.3f}s",
    }


@router.post("/metrics-test")
def generate_test_metrics():
    """Generate a variety of test metrics for observability testing."""
    start_time = time.time()

    # Generate different types of events
    event_types = ["test_queue_1", "test_queue_2", "test_queue_3"]

    for queue_name in event_types:
        # Successful events
        for i in range(2):
            processing_time = 0.05 + (i * 0.02)
            record_processing_success(queue_name, time.time() - processing_time)
            time.sleep(0.05)

        # Failed events
        fail_start = time.time()
        record_processing_failure(queue_name, fail_start)
        time.sleep(0.02)

    total_time = time.time() - start_time

    return {
        "message": "Test metrics generated!",
        "queues_processed": len(event_types),
        "total_events": len(event_types) * 3,  # 2 success + 1 failure per queue
        "total_time": f"{total_time:.3f}s",
    }


@router.post("/custom-event")
def generate_custom_event_metrics(queue_name: str = "custom_test_queue"):
    """Generate custom event metrics with a custom name."""
    start_time = time.time()

    # Generate custom event metrics
    custom_queue_name = queue_name

    # Successful events
    for i in range(2):
        processing_time = 0.08 + (i * 0.03)
        record_processing_success(custom_queue_name, time.time() - processing_time)
        time.sleep(0.03)

    # Failed events
    fail_start = time.time()
    record_processing_failure(custom_queue_name, fail_start)
    time.sleep(0.02)

    total_time = time.time() - start_time

    return {
        "message": "Custom event metrics generated!",
        "queue_name": custom_queue_name,
        "events_processed": 2,
        "events_failed": 1,
        "total_time": f"{total_time:.3f}s",
    }


@router.post("/custom-event-json")
def generate_custom_event_metrics_json(data: dict):
    """Generate custom event metrics with data from request body."""
    start_time = time.time()

    # Extract parameters from request body
    custom_queue_name = data.get("queue_name", "default_queue")
    events_processed = data.get("events_processed", 2)
    events_failed = data.get("events_failed", 1)

    # Generate custom event metrics
    for i in range(events_processed):
        processing_time = 0.08 + (i * 0.03)
        record_processing_success(custom_queue_name, time.time() - processing_time)
        time.sleep(0.03)

    # Generate failed events
    for _ in range(events_failed):
        fail_start = time.time()
        record_processing_failure(custom_queue_name, fail_start)
        time.sleep(0.02)

    total_time = time.time() - start_time

    return {
        "message": "Custom event metrics generated from JSON!",
        "queue_name": custom_queue_name,
        "events_processed": events_processed,
        "events_failed": events_failed,
        "total_time": f"{total_time:.3f}s",
        "request_data": data,
    }
