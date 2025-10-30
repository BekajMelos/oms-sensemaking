"""Base client with common connectivity checks for external services."""

import logging
import socket
import time

from oms_sensemaking.config import SETTINGS

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
            LOGGER.info("Resolved %s host '%s' to IP %s:%s", self._service_name, self._host, resolved, self._port)
            return resolved
        except socket.gaierror as e:
            LOGGER.warning("Failed to resolve host '%s' for %s: %s", self._host, self._service_name, e)
            return None

    def ping(self) -> bool:
        """Attempt a TCP connection to the configured host/port."""

        resolved = self._resolve_host() or self._host
        try:
            with socket.create_connection((resolved, self._port), timeout=SETTINGS.ping_timeout_seconds):
                LOGGER.info("%s connectivity check successful to %s:%s", self._service_name, resolved, self._port)
                return True
        except (TimeoutError, socket.gaierror, OSError) as ex:
            LOGGER.warning("%s connectivity check failed to %s:%d: %s", self._service_name, resolved, self._port, ex)
            return False

    def wait_until_ready(self) -> bool:
        """Ping until healthy or retries exhausted."""

        retries = SETTINGS.ping_wait_retries
        delay_seconds = SETTINGS.ping_wait_delay_seconds

        attempt = 0
        while attempt < retries:
            if self.ping():
                return True
            attempt += 1
            if attempt < retries:
                LOGGER.warning(
                    "Failed to connect to %s at %s:%s. Retrying in %ds. Attempt %d/%d",
                    self._service_name,
                    self._host,
                    self._port,
                    delay_seconds,
                    attempt + 1,
                    retries,
                )
                time.sleep(delay_seconds)
        LOGGER.error(
            "Failed to connect to %s at %s:%s after %d attempts", self._service_name, self._host, self._port, retries
        )
        return False
