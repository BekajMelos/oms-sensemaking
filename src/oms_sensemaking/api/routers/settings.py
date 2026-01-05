"""Rest Endpoints for Settings Management"""

import logging
from threading import Thread

from fastapi import APIRouter, Request, Response

from oms_sensemaking.api.schemas.settings import SettingsBatchUpdate
from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.core.controllers import SensemakerController, run_controller
from oms_sensemaking.core.settings import Settings as AppSettings
from oms_sensemaking.models.settings import Setting

LOGGER: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


def _restart_controllers_with_new_settings(
    controllers: list[SensemakerController], controller_threads: list[Thread], app_state
) -> None:
    """
    Background task to restart controllers with new settings.

    This function stops controllers, waits for threads to finish, updates settings,
    and restarts controllers.
    """

    for ctrl in controllers:
        ctrl.stop()

    for thread in controller_threads:
        if thread.is_alive():
            LOGGER.debug("Joining controller thread: %s", thread.name)
            thread.join(timeout=10.0)  # Timeout to prevent hanging
            if thread.is_alive():
                LOGGER.warning("Controller thread %s did not finish within timeout", thread.name)

    app_settings = AppSettings()

    LOGGER.info("Updating controllers with new settings")
    new_threads: list[Thread] = []
    for ctrl in controllers:
        ctrl.update_settings(app_settings)
        # Create new thread for the controller
        controller_thread = Thread(target=run_controller, args=(ctrl,))
        controller_thread.start()
        new_threads.append(controller_thread)

    # Update application state with new threads
    app_state.controller_threads = new_threads
    LOGGER.info("Controllers restarted with new settings")


@router.post("/settings", status_code=201)
def update_settings(request: Request, body: SettingsBatchUpdate):
    """
    Update application settings and restart controllers with new settings.

    This endpoint persists settings immediately and returns. Controllers are restarted
    asynchronously in the background to avoid blocking the API response during high load.
    """
    controllers: list[SensemakerController] = request.app.state.controllers
    controller_threads = getattr(request.app.state, "controller_threads", [])

    # Persist settings to the database
    LOGGER.info("Persisting %d settings to database", len(body.settings))
    if body.settings:
        with db_session() as db:
            for field_name, field_value in body.settings.items():
                existing_setting = db.query(Setting).filter(Setting.field_name == field_name).first()
                if existing_setting:
                    existing_setting.field_value = field_value
                    LOGGER.debug("Updated setting %s = %s", field_name, field_value)
                else:
                    new_setting = Setting(field_name=field_name, field_value=field_value)
                    db.add(new_setting)
                    LOGGER.debug("Created new setting %s = %s", field_name, field_value)
            db.commit()

    restart_thread = Thread(
        target=_restart_controllers_with_new_settings,
        args=(controllers, controller_threads, request.app.state),
        daemon=True,
    )
    restart_thread.start()
    LOGGER.info("Settings persisted. Controller restart initiated in background thread.")

    return Response(content="Settings updated", status_code=201)
