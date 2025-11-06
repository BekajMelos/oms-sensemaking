"""oms-sensemaking microservice."""

import html
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from logging.config import dictConfig
from pathlib import Path
from threading import Lock, Thread

from fastapi import FastAPI, status
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi_offline import FastAPIOffline

from oms_sensemaking import __description__, __title__, __version__
from oms_sensemaking.api.middleware.request_logger import RequestLogger
from oms_sensemaking.api.routers import aac, about, audit_log_error, health, rdf, settings, test
from oms_sensemaking.clients.instances import aac_client, oms_crud_tool, ontology_service, ping_db, ping_db_host_wait
from oms_sensemaking.config import SETTINGS, LogConfig, Settings
from oms_sensemaking.core.controllers import SensemakerController, run_controller
from oms_sensemaking.core.error_loggers import ErrorLogger, RethrowErrorLogger
from oms_sensemaking.core.events import CronEventEmitter, RabbitMQListener
from oms_sensemaking.core.middleware import MetricsMiddleware
from oms_sensemaking.core.observability import initialize_observability, instrument_fastapi, metrics_endpoint
from oms_sensemaking.geospatial.controllers import GeoQueueFilter, GeospatialSensemakerController
from oms_sensemaking.inference.controllers import InferenceQueueFilter, InferenceSensemakerController
from oms_sensemaking.iw.controllers import ObservableSensemakerController
from oms_sensemaking.mil_symbol.controllers import MilSymbolQueueFilter, MilSymbolSensemakerController
from oms_sensemaking.resolution.controllers import ResolutionQueueFilter, ResolutionSensemakerController

LOGGER: logging.Logger = logging.getLogger(__name__)

dictConfig(LogConfig().model_dump())  # initialize logging

# Initialize observability system
initialize_observability()

# Global storage for controller references and threads for live reload
_controller_threads: list[tuple[SensemakerController, Thread]] = []
_controller_lock = Lock()


def get_controllers() -> list[SensemakerController]:
    """Return a list of initialized sensemaker controllers."""

    err_logger: ErrorLogger | RethrowErrorLogger = ErrorLogger()
    if SETTINGS.rethrow_errors_enabled:
        err_logger = RethrowErrorLogger(err_logger)

    controllers: list[SensemakerController] = [
        GeospatialSensemakerController(
            RabbitMQListener(
                "GeoRMQListener",
                SETTINGS.rmq_geo_queue_name,
                event_filter=GeoQueueFilter(),
            ),
            err_logger,
            ontology_service,
        ),
        InferenceSensemakerController(
            RabbitMQListener(
                "InferenceRMQListener", SETTINGS.rmq_inference_queue_name, event_filter=InferenceQueueFilter()
            ),
            err_logger,
        ),
        ResolutionSensemakerController(
            RabbitMQListener(
                "ResolutionRMQListener", SETTINGS.rmq_res_queue_name, event_filter=ResolutionQueueFilter()
            ),
            err_logger,
        ),
        MilSymbolSensemakerController(
            RabbitMQListener(
                "MilSymbolRMQListener",
                SETTINGS.mil_symbol_settings.rmq_mil_symbol_queue_name,
                event_filter=MilSymbolQueueFilter(),
            ),
            err_logger,
        ),
        ObservableSensemakerController(CronEventEmitter(SETTINGS.iw_settings.observable_query_interval), err_logger),
    ]

    return controllers


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    Handle application lifecycle events.

    This function provides a contextmanager that can be registered with a
    FastAPI application to startup and shutdown the OMS Sensemaking
    controllers.
    """
    # startup
    LOGGER.info("Initializing sensemaker controllers")
    try:
        aac_client.wait_until_ready()
        oms_crud_tool.wait_until_ready()
        ping_db_host_wait()
        ping_db()
    except Exception as ex:
        LOGGER.warning("Dependency readiness checks encountered an issue: %s", ex)

    # Initialize controllers and store references globally
    with _controller_lock:
        _controller_threads.clear()
        for ctrlr in get_controllers():
            controller_thread: Thread = Thread(target=run_controller, args=(ctrlr,))
            controller_thread.start()
            _controller_threads.append((ctrlr, controller_thread))

    yield

    # Shutdown all controllers
    with _controller_lock:
        for controller, controller_thread in _controller_threads:
            LOGGER.warning("Handling the keyboard interrupt.")
            controller.stop()

            if controller_thread.is_alive():
                controller_thread.join()
        _controller_threads.clear()


def handle_exception(_, ex: Exception):
    """
    Handle generic exceptions.

    This handler formats the exception into a JSON response.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(ex) or f"Unexpected error: {ex.__class__.__name__}"},
    )


def create_app(config: Settings) -> FastAPI:
    """
    Create the oms_sensemaking microservice app with the provided settings.

    :param config: configuration used to initialize FastAPI and submodules.
    """
    application: FastAPI = FastAPIOffline(
        title=__title__,
        description=__description__,
        version=__version__,
        lifespan=lifespan,
        root_path=config.root_path,
        docs_url=None,
    )

    @application.get("/", response_class=HTMLResponse)
    async def custom_swagger_ui():
        """Serve custom Swagger UI with DoD warning."""
        template_path = Path(__file__).parent / "templates" / "custom_swagger.html"
        if template_path.exists():
            template_content = template_path.read_text()

            template_content = template_content.replace(
                "CLASSIFICATION_BANNER_TEXT", html.escape(config.classification_banner_text)
            )
            template_content = template_content.replace(
                "CLASSIFICATION_BANNER_COLOR", html.escape(config.classification_banner_color)
            )

            return HTMLResponse(content=template_content, media_type="text/html")
        else:
            return HTMLResponse(content="<h1>Template not found</h1>", media_type="text/html")

    # initialize gzip middleware
    application.add_middleware(GZipMiddleware, minimum_size=config.gzip_minimum_size)
    application.add_middleware(RequestLogger)

    # Add metrics middleware
    application.add_middleware(MetricsMiddleware)

    # configure routes
    application.include_router(about.router)
    application.include_router(aac.router, prefix="/aac")
    application.include_router(health.router)
    application.include_router(rdf.router, prefix="/resolver", tags=["resolver"])
    application.include_router(audit_log_error.router)
    application.include_router(settings.router, tags=["settings"])

    # Include test endpoints only if enabled
    if config.toggle_test_endpoints:
        application.include_router(test.router, prefix="/test", tags=["test"])

    # Mount metrics endpoint
    application.add_route("/metrics", metrics_endpoint)

    # Instrument with OpenTelemetry
    instrument_fastapi(application)

    # ensure exceptions are formatted as JSON
    application.add_exception_handler(Exception, handle_exception)

    return application


def check_aoi_file_path() -> None:
    """Check for valid areas of interest directory"""
    if SETTINGS.toggle_incursion_rule and (not os.path.isdir(SETTINGS.inference_incursion_areas_of_interest_path)):
        LOGGER.error("%s is not a valid directory", SETTINGS.inference_incursion_areas_of_interest_path)
        sys.exit("The areas of interest directory is incorrect or does not exist.")


def initialize_settings() -> None:
    """Initialize Settings"""
    try:
        SETTINGS.load_audit_log_event_error_acm()
        _ = SETTINGS.user_dn_whitelist
        check_aoi_file_path()
    except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
        LOGGER.error("Unable to initialize settings: %s", e)
        sys.exit("An error occurred during initialization.")


initialize_settings()


def reload_settings_from_db() -> None:
    """Reload settings from database and update the global SETTINGS object."""
    try:
        from oms_sensemaking.core.settings import Settings as DBSettings

        db_settings_obj = DBSettings()
        db_settings_dict = db_settings_obj.get_settings()

        if not db_settings_dict:
            LOGGER.info("No settings found in database, keeping current config/env defaults")
            return

        updated_count = 0
        for field_name, field_value in db_settings_dict.items():
            if "__" in field_name:
                continue

            if field_name not in SETTINGS.model_fields:
                LOGGER.debug("Skipping unknown setting from DB: %s", field_name)
                continue

            # Get current value
            old_value = getattr(SETTINGS, field_name, None)

            # Only update if value changed
            if old_value != field_value:
                object.__setattr__(SETTINGS, field_name, field_value)
                updated_count += 1
                LOGGER.info("Reloaded setting from DB: %s (old: %s -> new: %s)", field_name, old_value, field_value)

        if updated_count > 0:
            LOGGER.info("Successfully reloaded %d setting(s) from database", updated_count)
        else:
            LOGGER.info("Reloaded %d setting(s) from database, no changes needed", len(db_settings_dict))

    except Exception as e:
        LOGGER.warning("Failed to reload settings from database: %s", e, exc_info=True)


def restart_controllers() -> None:
    """Stop all running controllers and restart them with updated settings."""
    LOGGER.info("Restarting sensemaker controllers...")

    with _controller_lock:
        # Stop all existing controllers
        for controller, controller_thread in _controller_threads:
            LOGGER.info("Stopping controller %s", controller.__class__.__name__)
            controller.stop()
            if controller_thread.is_alive():
                controller_thread.join(timeout=5.0)
                if controller_thread.is_alive():
                    LOGGER.warning("Controller thread %s did not stop in time", controller.__class__.__name__)

        # Clear the list
        _controller_threads.clear()

        # Create new controllers with updated settings
        for ctrlr in get_controllers():
            new_thread = Thread(target=run_controller, args=(ctrlr,))
            new_thread.start()
            _controller_threads.append((ctrlr, new_thread))
            LOGGER.info("Started controller %s", ctrlr.__class__.__name__)

    LOGGER.info("All controllers restarted successfully")


def reload_settings_and_restart_controllers() -> None:
    """Reload settings from database and restart all controllers."""
    LOGGER.info("Reloading settings and restarting controllers...")
    reload_settings_from_db()
    restart_controllers()
    LOGGER.info("Settings reload and controller restart complete")


app: FastAPI = create_app(SETTINGS)
