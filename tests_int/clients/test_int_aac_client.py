from oms_sdk import DEFAULT_ACM

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.config import SETTINGS


def test_single_rollup():
    acm = DEFAULT_ACM
    aac_client = AacClient(SETTINGS.cert_path, SETTINGS.key_path, SETTINGS.cacert_path, SETTINGS.aac_verification_mode)

    rollup_acm = aac_client.get_acm_rollup([{"ACM": acm}])
    assert rollup_acm.get("classif") == "U"
