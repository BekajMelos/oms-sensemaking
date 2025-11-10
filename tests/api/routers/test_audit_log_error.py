from unittest.mock import patch

from oms_sensemaking.api.routers.audit_log_error import get_audit_log_errors


def test_get_audit_log_errors_direct_success():
    mock_data = [{"id": 1, "message": "Sample error"}]

    with (
        patch(
            "oms_sensemaking.api.routers.audit_log_error.AuditLogErrorClient.get_audit_log_errors",
            return_value=mock_data,
        ),
        patch("oms_sensemaking.api.routers.audit_log_error.check_user_dn_in_whitelist", return_value="test"),
    ):
        result = get_audit_log_errors(user_dn="test", exception_name=None, page=1, pagesize=500)

    assert result == mock_data
