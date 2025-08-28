"""Base client with common connectivity checks for external services."""

import logging
import socket
import time


LOGGER: logging.Logger = logging.getLogger(__name__)


class BaseClient:
    """
    Base class providing simple TCP connectivity checks and DNS resolution logging.

    Subclasses should supply the host, port, and a human-readable service name.
    """

    def __init__(self, host: str, port: int, service_name: str) -> None:
        self._host = host
        self._port = port
        self._service_name = service_name

    def _resolve_host(self) -> str | None:
        try:
            resolved = socket.gethostbyname(self._host)
            LOGGER.info(f"Resolved {self._service_name} host '{self._host}' to IP {resolved}:{self._port}")
            return resolved
        except Exception as ex:
            LOGGER.warning(f"Unable to resolve {self._service_name} host '{self._host}': {ex}")
            return None

    def ping(self, timeout_seconds: float = 3.0) -> bool:
        """Attempt a TCP connection to the configured host/port."""
        resolved = self._resolve_host() or self._host
        try:
            with socket.create_connection((resolved, self._port), timeout=timeout_seconds):
                LOGGER.info(f"{self._service_name} connectivity check successful to {resolved}:{self._port}")
                return True
        except Exception as ex:
            LOGGER.warning(f"{self._service_name} connectivity check failed to {resolved}:{self._port}: {ex}")
            return False

    def wait_until_ready(self, retries: int = 5, delay_seconds: float = 2.0) -> bool:
        """Ping until healthy or retries exhausted."""
        attempt = 0
        while attempt < retries:
            if self.ping():
                return True
            attempt += 1
            if attempt < retries:
                time.sleep(delay_seconds)
        return False
