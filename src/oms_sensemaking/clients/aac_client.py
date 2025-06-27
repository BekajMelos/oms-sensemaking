import logging
import ssl
from typing import List, Optional, Union

import httpx

from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)


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

        verify: Union[bool, ssl.SSLContext] = False
        if verification_mode:
            LOGGER.warning("AAC Client verification enabled")
            verify = self._ctx
        else:
            LOGGER.warning("AAC Client verification disabled")

        self.client = httpx.Client(verify=verify, timeout=30)

    def __del__(self):
        """
        Deconstruct the client communicating with an AAC Service v2.x
        """
        self.client.close()

    def get_acm_rollup(self, acms: List[dict]) -> dict:
        """Use AAC to rollup a list of ACMs"""
        LOGGER.debug("Getting ACM Rollup")

        response = self.client.post(f"{SETTINGS.aac_url}/acms/rollup", json={"AccessTuples": acms})
        return response.json()["RollupACM"]
