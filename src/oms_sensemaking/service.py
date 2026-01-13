"""oms-sensemaking microservice."""

import html
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from logging.config import dictConfig
from pathlib import Path
from threading import Thread

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
from oms_sensemaking.core.settings import Settings as AppSettings
from oms_sensemaking.geospatial.controllers import GeoQueueFilter, GeospatialSensemakerController
from oms_sensemaking.inference.controllers import InferenceQueueFilter, InferenceSensemakerController
from oms_sensemaking.iw.controllers import ObservableSensemakerController
from oms_sensemaking.mil_symbol.controllers import MilSymbolQueueFilter, MilSymbolSensemakerController
from oms_sensemaking.object_minimums.controllers import (
    ObjectMinimumsQueueFilter,
    ObjectMinimumsSensemakerController,
    ObjMinDataProvider,
)
from oms_sensemaking.resolution.controllers import (
    ResolutionIriProvider,
    ResolutionQueueFilter,
    ResolutionSensemakerController,
)

LOGGER: logging.Logger = logging.getLogger(__name__)

dictConfig(LogConfig().model_dump())  # initialize logging

# Initialize observability system
initialize_observability()


def get_controllers(app_settings: AppSettings) -> list[SensemakerController]:
    """Return a list of initialized sensemaker controllers."""

    err_logger: ErrorLogger | RethrowErrorLogger = ErrorLogger()
    if SETTINGS.rethrow_errors_enabled:
        err_logger = RethrowErrorLogger(err_logger)

    controllers: list[SensemakerController] = [
        GeospatialSensemakerController(
            RabbitMQListener(
                "GeoRMQListener",
                SETTINGS.rmq_geo_queue_name,
                workers=SETTINGS.queue_worker_threads,
                app_settings=app_settings,
                event_filter=GeoQueueFilter(),
            ),
            err_logger,
            ontology_service,
        ),
        InferenceSensemakerController(
            RabbitMQListener(
                "InferenceRMQListener",
                SETTINGS.rmq_inference_queue_name,
                workers=SETTINGS.queue_worker_threads,
                app_settings=app_settings,
                event_filter=InferenceQueueFilter(),
            ),
            err_logger,
        ),
        ResolutionSensemakerController(
            RabbitMQListener(
                "ResolutionRMQListener",
                SETTINGS.rmq_res_queue_name,
                workers=SETTINGS.queue_worker_threads,
                app_settings=app_settings,
                event_filter=ResolutionQueueFilter(ResolutionIriProvider()),
            ),
            err_logger,
        ),
        MilSymbolSensemakerController(
            RabbitMQListener(
                "MilSymbolRMQListener",
                SETTINGS.mil_symbol_settings.rmq_mil_symbol_queue_name,
                workers=SETTINGS.queue_worker_threads,
                app_settings=app_settings,
                event_filter=MilSymbolQueueFilter(),
            ),
            err_logger,
        ),
        ObjectMinimumsSensemakerController(
            RabbitMQListener(
                "ObjectMinimumsRMQListener",
                SETTINGS.object_minimum_settings.rmq_object_minimums_queue_name,
                workers=SETTINGS.queue_worker_threads,
                app_settings=app_settings,
                event_filter=ObjectMinimumsQueueFilter(ObjMinDataProvider()),
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

    app_settings = AppSettings()

    controllers: list[tuple[SensemakerController, Thread]] = []
    for ctrlr in get_controllers(app_settings):
        controller_thread: Thread = Thread(target=run_controller, args=(ctrlr,))
        controller_thread.start()
        controllers.append((ctrlr, controller_thread))

    yield

    for controller, controller_thread in controllers:
        LOGGER.warning("Handling the keyboard interrupt.")
        controller.stop()

        if controller_thread.is_alive():
            controller_thread.join()


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


def check_obj_min_rubric_file_path() -> None:
    """Check for valid object minimums rubric directory"""
    if not os.path.exists(SETTINGS.object_minimum_settings.rubrics_file_path):
        LOGGER.error("%s is not a valid directory", SETTINGS.object_minimum_settings.rubrics_file_path)
        sys.exit("The object minimums rubric file path is incorrect or does not exist.")


def initialize_settings() -> None:
    """Initialize Settings"""
    try:
        SETTINGS.load_audit_log_event_error_acm()
        _ = SETTINGS.user_dn_whitelist
        check_aoi_file_path()
        check_obj_min_rubric_file_path()
    except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
        LOGGER.error("Unable to initialize settings: %s", e)
        sys.exit("An error occurred during initialization.")


initialize_settings()


app: FastAPI = create_app(SETTINGS)
