from oms_sdk import DEFAULT_ACM

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.config import SETTINGS


def test_single_rollup():
    acm = DEFAULT_ACM
    aac_client = AacClient(
        SETTINGS.cert_path, SETTINGS.key_path, SETTINGS.aac_cacert_path, SETTINGS.aac_verification_mode
    )

    rollup_acm = aac_client.get_acm_rollup([{"ACM": acm}])
    assert rollup_acm.get("classif") == "U"


def test_multiple_rollup(ts_acm):
    unclass = DEFAULT_ACM
    ts = ts_acm

    aac_client = AacClient(
        SETTINGS.cert_path, SETTINGS.key_path, SETTINGS.aac_cacert_path, SETTINGS.aac_verification_mode
    )
    rollup_acm = aac_client.get_acm_rollup([{"ACM": unclass}, {"ACM": ts}])
    assert rollup_acm.get("classif") == "TS"
