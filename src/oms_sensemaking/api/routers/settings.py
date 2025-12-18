"""Rest Endpoints for Settings Management"""

import logging
from threading import Thread

from fastapi import APIRouter, Request, Response

from oms_sensemaking.api.schemas.settings import SettingsBatchUpdate
from oms_sensemaking.core.controllers import run_controller
from oms_sensemaking.core.settings import Settings as AppSettings

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


@router.post("/settings", status_code=201)
def update_settings(request: Request, body: SettingsBatchUpdate):
    """
    Update application settings and restart controllers with new settings.

    This endpoint stops all controllers, updates their settings, and restarts them
    with new threads. The old controller threads are properly joined before creating new ones.
    """
    controllers = request.app.state.controllers
    controller_threads = getattr(request.app.state, "controller_threads", [])

    # Stop all controllers and wait for their threads to finish
    LOGGER.info("Stopping controllers for settings update")
    for ctrl in controllers:
        ctrl.stop()

    # Join all old threads to ensure they've finished
    for thread in controller_threads:
        if thread.is_alive():
            LOGGER.debug("Joining controller thread: %s", thread.name)
            thread.join(timeout=10.0)  # Timeout to prevent hanging
            if thread.is_alive():
                LOGGER.warning("Controller thread %s did not finish within timeout", thread.name)

    # Create new app_settings instance with updated settings
    # Note: The settings should already be persisted to the database by this point
    app_settings = AppSettings()

    # Update each controller with new settings and restart
    LOGGER.info("Updating controllers with new settings")
    new_threads: list[Thread] = []
    for ctrl in controllers:
        ctrl.update_settings(app_settings)
        ctrl.restart()
        # Create new thread for the restarted controller
        controller_thread = Thread(target=run_controller, args=(ctrl,))
        controller_thread.start()
        new_threads.append(controller_thread)

    # Update application state with new threads
    request.app.state.controller_threads = new_threads

    return Response(content="Settings updated", status_code=201)
