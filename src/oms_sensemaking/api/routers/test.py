"""Test endpoints for observability and development testing."""

import logging
import time

from fastapi import APIRouter

from oms_sensemaking.core.observability import record_event_failed, record_event_processed, record_queue_processing_time

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.post("/hello-world")
def generate_hello_world_events():
    """Generate hello_world events for observability testing."""
    start_time = time.time()

    # Generate some successful events
    for i in range(3):
        processing_time = 0.1 + (i * 0.05)
        record_queue_processing_time("hello_world", processing_time)
        record_event_processed("hello_world")
        time.sleep(0.1)

    # Generate some failed events
    for _i in range(2):
        record_event_failed("hello_world")
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
            record_queue_processing_time(queue_name, processing_time)
            record_event_processed(queue_name)
            time.sleep(0.05)

        # Failed events
        record_event_failed(queue_name)
        time.sleep(0.02)

    total_time = time.time() - start_time

    return {
        "message": "Test metrics generated!",
        "queues_processed": len(event_types),
        "total_events": len(event_types) * 3,  # 2 success + 1 failure per queue
        "total_time": f"{total_time:.3f}s",
    }
