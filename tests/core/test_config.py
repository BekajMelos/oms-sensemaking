from oms_sensemaking.config import SETTINGS


def test_audit_log_error():
    assert SETTINGS.audit_log_error_acm is not None
