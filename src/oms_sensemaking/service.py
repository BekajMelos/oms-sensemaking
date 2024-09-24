"""oms-sensemaking microservice."""

import logging
from contextlib import asynccontextmanager
from logging.config import dictConfig
from threading import Thread
from typing import Tuple

from fastapi import FastAPI, status
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi_offline import FastAPIOffline

from oms_sensemaking import __description__, __title__, __version__
from oms_sensemaking.api.routers import about, nlp
from oms_sensemaking.config import SETTINGS, LogConfig, Settings
from oms_sensemaking.core.controllers import SensemakerController, run_controller
from oms_sensemaking.core.events import NoOpEventConsumer
from oms_sensemaking.geospatial.controllers import GeospatialSensemakerController, GeoSQSListener
from oms_sensemaking.nlp.controllers import NlpSensemakerController
from oms_sensemaking.semantic.controllers import SemanticSensemakerController

LOGGER: logging.Logger = logging.getLogger(__name__)

dictConfig(LogConfig().model_dump())  # initialize logging


def get_controllers() -> list[SensemakerController]:
    """Return a list of initialized sensemaker controllers."""
    controllers: list[SensemakerController] = [
        # TODO: set queue names independently
        GeospatialSensemakerController(GeoSQSListener()),
        NlpSensemakerController(NoOpEventConsumer()),
        SemanticSensemakerController(NoOpEventConsumer())
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
    controllers: list[Tuple[SensemakerController, Thread]] = []

    for ctrlr in get_controllers():
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
        content={'detail': str(ex) or f'Unexpected error: {ex.__class__.__name__}'}
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
        lifespan=lifespan
    )

    # initialize gzip middleware
    application.add_middleware(GZipMiddleware, minimum_size=config.gzip_minimum_size)

    # configure routes
    application.include_router(about.router)

    application.include_router(
        nlp.router,
        prefix="/nlp",
        tags=["NLP"]
    )

    # ensure exceptions are formatted as JSON
    application.add_exception_handler(Exception, handle_exception)

    return application


app: FastAPI = create_app(SETTINGS)
