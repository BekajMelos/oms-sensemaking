from oms_sensemaking.config import SETTINGS


def test_highest_classification():
    assert SETTINGS.highest_classification is not None
