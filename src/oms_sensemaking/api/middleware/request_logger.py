import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

LOGGER: logging.Logger = logging.getLogger(__name__)


class RequestLogger(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        headers = request.headers.items()
        response = await call_next(request)
        client_host = request.client.host if request.client else ""
        client_port = request.client.port if request.client else ""
        LOGGER.info(f"{request.method} {request.url} client: {client_host}:{client_port} headers: {headers}")

        return response
