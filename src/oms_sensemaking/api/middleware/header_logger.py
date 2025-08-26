import logging

from fastapi import FastAPI, Request

LOGGER: logging.Logger = logging.getLogger(__name__)

app = FastAPI()


@app.middleware("http")
async def log_request_header(request: Request, call_next):
    try:
        LOGGER.info(request.headers.values())
    except Exception:
        LOGGER.error("could not parse request")

    response = await call_next(request)

    return response
