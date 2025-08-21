"""The *about* module contains endpoints that return information about the service."""

import time

from fastapi import APIRouter

from oms_sensemaking import __description__, __title__, __version__
from oms_sensemaking.api.schemas.app_info import AppInfo
from oms_sensemaking.core.observability import record_event_processed, record_queue_processing_time

router: APIRouter = APIRouter()


@router.get("/version.json", response_model=AppInfo, response_model_exclude_none=True)
def about() -> AppInfo:
    """Return service information."""
    start_time = time.time()

    # Simulate some processing time
    time.sleep(0.1)

    # Record custom metrics for version info requests
    processing_time = time.time() - start_time
    record_queue_processing_time("version_info", processing_time)
    record_event_processed("version_info")

    return AppInfo(title=__title__, version=__version__, description=__description__)
