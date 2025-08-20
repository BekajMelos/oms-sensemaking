"""oms-sensemaking microservice."""

import logging
from contextlib import asynccontextmanager
from logging.config import dictConfig
from pathlib import Path
from threading import Thread

from fastapi import FastAPI, status
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi_offline import FastAPIOffline

from oms_sensemaking import __description__, __title__, __version__
from oms_sensemaking.api.routers import aac, about, health, nlp, rdf
from oms_sensemaking.config import SETTINGS, LogConfig, Settings
from oms_sensemaking.core.controllers import SensemakerController, run_controller
from oms_sensemaking.core.events import RabbitMQListener
from oms_sensemaking.geospatial.controllers import GeoQueueFilter, GeospatialSensemakerController
from oms_sensemaking.inference.controllers import InferenceQueueFilter, InferenceSensemakerController
from oms_sensemaking.mil_symbol.controllers import MilSymbolQueueFilter, MilSymbolSensemakerController
from oms_sensemaking.resolution.controllers import ResolutionQueueFilter, ResolutionSensemakerController

LOGGER: logging.Logger = logging.getLogger(__name__)

dictConfig(LogConfig().model_dump())  # initialize logging


def get_controllers() -> list[SensemakerController]:
    """Return a list of initialized sensemaker controllers."""
    controllers: list[SensemakerController] = [
        GeospatialSensemakerController(
            RabbitMQListener("GeoRMQListener", SETTINGS.rmq_geo_queue_name, event_filter=GeoQueueFilter())
        ),
        InferenceSensemakerController(
            RabbitMQListener(
                "InferenceRMQListener", SETTINGS.rmq_inference_queue_name, event_filter=InferenceQueueFilter()
            )
        ),
        ResolutionSensemakerController(
            RabbitMQListener("ResolutionRMQListener", SETTINGS.rmq_res_queue_name, event_filter=ResolutionQueueFilter())
        ),
        MilSymbolSensemakerController(
            RabbitMQListener(
                "MilSymbolRMQListener",
                SETTINGS.mil_symbol_settings.rmq_mil_symbol_queue_name,
                event_filter=MilSymbolQueueFilter(),
            )
        ),
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
    controllers: list[tuple[SensemakerController, Thread]] = []

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

            template_content = template_content.replace("CLASSIFICATION_BANNER_TEXT", config.classification_banner_text)
            template_content = template_content.replace(
                "CLASSIFICATION_BANNER_COLOR", config.classification_banner_color
            )

            return HTMLResponse(content=template_content, media_type="text/html")
        else:
            return HTMLResponse(content="<h1>Template not found</h1>", media_type="text/html")

    # initialize gzip middleware
    application.add_middleware(GZipMiddleware, minimum_size=config.gzip_minimum_size)

    # configure routes
    application.include_router(about.router)
    application.include_router(aac.router, prefix="/aac")
    application.include_router(nlp.router, prefix="/nlp", tags=["NLP"])
    application.include_router(health.router)
    application.include_router(rdf.router, prefix="/resolver", tags=["resolver"])

    # ensure exceptions are formatted as JSON
    application.add_exception_handler(Exception, handle_exception)

    return application


app: FastAPI = create_app(SETTINGS)
