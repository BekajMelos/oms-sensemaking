import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from oms_sensemaking.api.middleware.connection_info import (
    AddressConnectionInfo,
    ConnectionInfo,
    HeaderAddressConnectionInfo,
)

LOGGER: logging.Logger = logging.getLogger(__name__)


class RequestLogger(BaseHTTPMiddleware):
    """Middleware for logging request information"""

    async def dispatch(self, request: Request, call_next):
        headers = request.headers.items()
        response = await call_next(request)

        conn_info = self._get_conn_info(request)

        LOGGER.info(f"{request.method} {request.url} client: {conn_info.host}:{conn_info.port} headers: {headers}")

        return response

    def _get_conn_info(self, request: Request) -> ConnectionInfo:
        if request.client:
            return AddressConnectionInfo(request.client)
        return HeaderAddressConnectionInfo().get_connection_info(request)
