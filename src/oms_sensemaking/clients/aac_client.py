"""AAC Client"""

import dataclasses
import json
import logging
import ssl
from typing import Any, List, Optional, Union

import hishel
import httpcore
import httpx
from hishel._utils import generate_key

from oms_sensemaking.clients.base_client import BaseClient
from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)

HTTPX_TIMEOUT = 30


@dataclasses.dataclass(frozen=True)
class TextMarking:
    marking: str
    path: str

    def __init__(self, marking: str, path: str) -> None:
        """
        :param marking: text marking such as "U" or "UNCLASSIFIED"
        :param path: unique identifier for the marking
        """
        object.__setattr__(self, "marking", marking)
        object.__setattr__(self, "path", path)

    def to_json(self) -> str:
        """Return a JSON representation of the marking"""
        return json.dumps(
            {
                "Marking": self.marking,
                "Path": self.path,
            }
        )


@dataclasses.dataclass(frozen=True)
class ParsedMarking:
    """
    POJO output from converting a text marking to an acm marking
    """

    errors: list[str]
    warnings: list[str]
    acm: object
    path: str

    def __init__(self, output: dict[str, Any]) -> None:
        object.__setattr__(self, "errors", output["Errors"])
        object.__setattr__(self, "warnings", output["Warnings"])
        object.__setattr__(self, "acm", output["ACM"])
        object.__setattr__(self, "path", output["Path"])


class MarkingParser:
    """
    Converts a text marking list response to an acm marking list
    """

    @staticmethod
    def parse(json_body: Any) -> list[ParsedMarking]:
        """
        :param json_body: response from AAC Service when creating a
        """
        return [ParsedMarking(marking) for marking in json_body.json()]


class AacClient(BaseClient):
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

        For https connections with two-way ssl, the client can be configured in one of two ways
        * set the cert_path with a .pem file,
        * set the cert_path with a .crt file and the key_path with a .key file

        For http connections, do not set cert_path or key_path

        :param cert_path: For two-way ssl, the path to the .pem or .crt file

        :param key_path: For two-way ssl, the path to the .key file

        :param ca_cert_path: Optional path to a CA's .pem file

        :param verification_mode: Optional, set whether the host is verified through a CA Bundle or not
        """

        super().__init__(host=SETTINGS.aac_host, port=SETTINGS.aac_port, service_name="AAC")

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

    def get_acms_from_markings(self, markings: list[TextMarking]):
        """
        Use AAC to generate acms from classif markings

        :param markings: list of identifiers and classification marking (e.g. "foo" -> "UNCLASSIFIED" or "U")
        """
        LOGGER.debug("Getting acms from text markings")

        response = self.client.post(f"{SETTINGS.aac_url}/icmss/markings/acms", json=markings)

        return MarkingParser.parse(response)

    def clear_cache(self) -> None:
        """Admin endpoint to clear the local aac_cache."""
        if SETTINGS.aac_cache_enabled:
            transport = self._get_new_caching_transport()
            self.client = httpx.Client(verify=self.verify, timeout=HTTPX_TIMEOUT, transport=transport)
        else:
            LOGGER.info("Cache not enabled. Unable to clear cache.")

    def check_access_for_acms(self, user_dn, acms: list[dict]) -> list[dict]:
        """
        Determine if the given user_dn has has access to the acms.
        Returns a matching list of acms with errors if they exist
        """
        response = self.client.post(f"{SETTINGS.aac_url}/users/{user_dn}/accesses", json=acms)
        return response.json()

    @staticmethod
    def _dedup_acms(acms: List[dict]):
        json_acms = [json.dumps(acm, sort_keys=True) for acm in acms]
        deduped = set(json_acms)
        return [json.loads(dedup) for dedup in deduped]

    @staticmethod
    def _custom_key_generator(request: httpcore.Request, body: bytes):
        """
        Create a cache key based on the request body, for our case, it is a list of acms
        """
        key = generate_key(request, body)
        host = request.url.host.decode()
        return f"{host}|{key}"
