"""AAC Client"""

import json
import logging
import ssl
from typing import List, Optional, Union

import hishel
import httpcore
import httpx
from hishel._utils import generate_key

from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)

HTTPX_TIMEOUT = 30


class AacClient:
    """AAC Client for communicating with the AAC Service"""

    def __init__(
        self,
        cert_path: Optional[str],
        key_path: Optional[str],
        ca_cert_path: Optional[str],
        verification_mode: Optional[bool],
    ) -> None:
        """
        Construct the client for communicating to an AAC Service v2.x

        For https connections with two way ssl, the client can be configured in one of two ways
        * set the cert_path with a .pem file,
        * set the cert_path with a .crt file and the key_path with a .key file

        For http connections, do not set cert_path or key_path

        :param cert_path: For two-way ssl, the path to the .pem or .crt file

        :param key_path: For two-way ssl, the path to the .key file

        :param ca_cert_path: Optional path to a CA's .pem file

        :param aac_verification_mode: Optional, set whether the host is verified through a CA Bundle or not
        """

        if ca_cert_path is None or ca_cert_path == "":
            LOGGER.warning("AAC Client CA_CERT_PATH not detected")
        self._ctx = ssl.create_default_context(cafile=ca_cert_path)

        if cert_path and key_path:
            LOGGER.warning("AAC Client cert_path and key_path detected")
            self._ctx.load_cert_chain(f"{cert_path}", f"{key_path}")
        elif cert_path:
            LOGGER.warning("AAC Client cert_path detected")
            self._ctx.load_cert_chain(f"{cert_path}")
        else:
            LOGGER.warning("AAC Client certs not detected")

        self.verify: Union[bool, ssl.SSLContext] = False
        if verification_mode:
            LOGGER.warning("AAC Client verification enabled")
            self.verify = self._ctx
        else:
            LOGGER.warning("AAC Client verification disabled")

        transport: httpx.BaseTransport = httpx.HTTPTransport(verify=self.verify)

        if SETTINGS.aac_cache_enabled:
            LOGGER.warning("AAC Cache is enabled")
            transport = self._get_new_caching_transport()
        else:
            LOGGER.warning("AAC Cache is disabled")

        self.client = httpx.Client(verify=self.verify, timeout=HTTPX_TIMEOUT, transport=transport)

    def _get_new_caching_transport(self) -> httpx.BaseTransport:
        cache_storage = hishel.InMemoryStorage(ttl=SETTINGS.aac_cache_storage_ttl_seconds)
        controller = hishel.Controller(
            cacheable_methods=["GET", "POST"],
            force_cache=True,
            key_generator=self._custom_key_generator,  # type: ignore[arg-type]
        )
        return hishel.CacheTransport(
            transport=httpx.HTTPTransport(verify=self.verify), storage=cache_storage, controller=controller
        )

    def __del__(self):
        """
        Deconstruct the client communicating with an AAC Service v2.x
        """
        self.client.close()

    def get_acm_rollup(self, acms: List[dict]) -> dict:
        """Use AAC to rollup a list of ACMs"""
        LOGGER.debug("Getting ACM Rollup")

        response = self.client.post(f"{SETTINGS.aac_url}/acms/rollup", json={"AccessTuples": self._dedup_acms(acms)})
        return response.json()["RollupACM"]

    def clear_cache(self) -> None:
        """Admin endpoint to clear the local aac_cache."""
        if SETTINGS.aac_cache_enabled:
            transport = self._get_new_caching_transport()
            self.client = httpx.Client(verify=self.verify, timeout=HTTPX_TIMEOUT, transport=transport)
        else:
            LOGGER.info("Cache not enabled. Unable to clear cache.")

    def _dedup_acms(self, acms: List[dict]):
        json_acms = [json.dumps(acm, sort_keys=True) for acm in acms]
        deduped = set(json_acms)
        return [json.loads(dedup) for dedup in deduped]

    def _custom_key_generator(self, request: httpcore.Request, body: bytes):
        """
        Create a cache key based on the request body, for our case, it is a list of acms
        """
        key = generate_key(request, body)
        host = request.url.host.decode()
        return f"{host}|{key}"
