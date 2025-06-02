"""OMS Sensemaking - Analytics for OMS."""

from contextlib import suppress
from importlib.metadata import PackageNotFoundError, version

__description__: str = "A service for performing analytics on OMS data."
__title__: str = "OMS Sensemaking Service"
__version__: str = "UNKNOWN"


with suppress(PackageNotFoundError):
    __version__ = version("oms_sensemaking")
