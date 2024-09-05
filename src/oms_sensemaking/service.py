"""oms-sensemaking microservice."""

from fastapi import FastAPI, status
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi_offline import FastAPIOffline

from oms_sensemaking import __description__, __title__, __version__
from oms_sensemaking.api.routers import about, semantic
from oms_sensemaking.config import SETTINGS, Settings


def handle_exception(_, ex: Exception):
    """
    Handler for generic exceptions.

    This handler formats the exception into a JSON response.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={'detail': str(ex) or f'Unexpected error: {ex.__class__.__name__}'}
    )


def create_app(config: Settings) -> FastAPI:
    """
    Creates the oms_sensemaking microservice app with the provided settings.

    :param config: configuration used to initialize FastAPI and submodules.
    """
    application: FastAPI = FastAPIOffline(
        title=__title__,
        description=__description__,
        version=__version__,
    )

    # initialize gzip middleware
    application.add_middleware(GZipMiddleware, minimum_size=config.gzip_minimum_size)

    # configure routes
    application.include_router(about.router)
    application.include_router(
        semantic.router,
        prefix="/semantic",
        tags=["semantic"]
    )

    # configure semantic route
    application.include_router(semantic.router)

    # ensure exceptions are formatted as JSON
    application.add_exception_handler(Exception, handle_exception)

    return application


app: FastAPI = create_app(SETTINGS)
