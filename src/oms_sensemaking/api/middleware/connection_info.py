import logging
from typing import Protocol

from fastapi import Request
from fastapi.datastructures import Address, Headers

LOGGER: logging.Logger = logging.getLogger(__name__)


class ConnectionInfo(Protocol):
    """Common interface for request client info"""

    host: str
    port: str


class AddressConnectionInfo(ConnectionInfo):
    """Build connection info from direct requests"""

    def __init__(self, address: Address) -> None:
        self.host = address.host
        self.port = str(address.port)


class ParamsConnectionInfo(ConnectionInfo):
    def __init__(self, host: str, port: str) -> None:
        self.host = host
        self.port = port


class HeaderAddressConnectionInfo:
    """Handle proxied requests that may not have request client populated"""

    def get_connection_info(self, request: Request) -> ConnectionInfo:
        """
        Try to process request headers that may indicate a client's address.
        The headers are a "defacto" but unofficial standard when proxied,
        X-Real-IP does not have an official singular format though.  The env
        is likely to be proxied somewhere though, so we need to at least try
        to capture the original host.
        """
        x_forwarded_for = self._get_header(request.headers, "X-Forwarded-For")
        x_real_ip = self._get_header(request.headers, "X-Real-IP")

        try:
            if x_forwarded_for:
                hostname = x_forwarded_for[1].split(",")[0].strip()
                return ParamsConnectionInfo(hostname, "Unknown (from X-Forwarded-For)")
            elif x_real_ip:
                hostname = x_real_ip[1]
                return ParamsConnectionInfo(hostname, "Unknown (from X-Real-IP)")
            else:
                return ParamsConnectionInfo("Unknown", "Unknown")
        except Exception:
            LOGGER.exception("Unable to parse header for connection information")
            return ParamsConnectionInfo("Unknown", "Unknown")

    def _get_header(self, headers: Headers, header_name: str) -> tuple[str, str] | None:
        name = header_name.upper()
        return next(((key, value) for key, value in headers.items() if key.upper() == name), None)
