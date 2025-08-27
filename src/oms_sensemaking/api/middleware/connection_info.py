from typing import Protocol

from fastapi import Request
from fastapi.datastructures import Address, Headers


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
        x_forwarded_for = self._get_header(request.headers, "X-Forwarded-For")
        x_real_ip = self._get_header(request.headers, "X-Real-IP")

        if x_forwarded_for:
            hostname = x_forwarded_for[1].split(",")[0].strip()
            return ParamsConnectionInfo(hostname, "Unknown (from X-Forwarded-For)")
        elif x_real_ip:
            hostname = x_real_ip[0]
            return ParamsConnectionInfo(hostname, "Unknown (from X-Real-IP)")
        else:
            return ParamsConnectionInfo("Unknown", "Unkown")

    def _get_header(self, headers: Headers, header_name: str) -> tuple[str, str] | None:
        name = header_name.upper()
        return next(((key, value) for key, value in headers.items() if key.upper() == name), None)
