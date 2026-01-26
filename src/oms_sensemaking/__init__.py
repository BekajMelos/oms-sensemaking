"""ATOMS Sensemaking - Analytics for ATOMS."""

from contextlib import suppress
from importlib.metadata import PackageNotFoundError, version

__description__: str = "A service for performing analytics on ATOMS data."
__title__: str = "ATOMS Sensemaking Service"
__version__: str = "UNKNOWN"


with suppress(PackageNotFoundError):
    __version__ = version("oms_sensemaking")
