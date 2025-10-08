"""The *about* module contains endpoints that return information about the service."""

import logging

from fastapi import APIRouter

from oms_sensemaking import __description__, __title__, __version__
from oms_sensemaking.api.schemas.app_info import AppInfo

router: APIRouter = APIRouter()

LOGGER: logging.Logger = logging.getLogger(__name__)


@router.get("/version.json", response_model=AppInfo, response_model_exclude_none=True)
def about() -> AppInfo:
    """Return service information."""
    LOGGER.info("Version endpoint requested", extra={"endpoint": "/version.json", "version": __version__})

    # Create AppInfo object
    app_info = AppInfo(title=__title__, version=__version__, description=__description__)

    return app_info
