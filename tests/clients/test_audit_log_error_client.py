from datetime import datetime
from unittest.mock import MagicMock, patch

from oms_sensemaking.clients.audit_log_error_client import AuditLogErrorClient
from oms_sensemaking.models.logs import AuditLogError


def make_mock_error(id=1):
    """Helper to construct a fake AuditLogError ORM object."""
    error = MagicMock(spec=AuditLogError)
    error.created_at = datetime(2024, 1, 1, 12, 0, 0)
    error.id = id
    error.object_id = id
    error.object_type = "SomeType"
    error.event_type = "SomeEvent"
    error.module_name = "mod"
    error.line_no = 10
    error.function_name = "func"
    error.code = "X1"
    error.exception_name = "ValueError"
    error.version = "1.0"
    error.message = "Something went wrong"
    error.exc_text = "Stacktrace..."
    error.acm = {"portion": "S"}
    return error


def test_get_audit_log_errors_no_results():
    """Should return empty list when DB query returns none."""
    client = AuditLogErrorClient()

    with (
        patch("oms_sensemaking.clients.audit_log_error_client.db_session") as mock_db_session,
    ):
        # Mock context manager for db_session()
        mock_db = MagicMock()
        mock_db.query().order_by().limit().offset().all.return_value = []
        mock_db_session.return_value.__enter__.return_value = mock_db

        result = client.get_audit_log_errors("test", None, 1, 500)
        assert result == []


def test_get_audit_log_errors_success():
    """Should return formatted errors when AAC access allows all entries."""
    client = AuditLogErrorClient()

    mock_error = make_mock_error()

    with (
        patch("oms_sensemaking.clients.audit_log_error_client.db_session") as mock_db_session,
        patch("oms_sensemaking.clients.audit_log_error_client.aac_client") as mock_aac,
    ):
        # DB returns one error record
        mock_db = MagicMock()
        mock_db.query().order_by().limit().offset().all.return_value = [mock_error]
        mock_db_session.return_value.__enter__.return_value = mock_db

        # AAC returns access allowed (no "Errors" entry)
        mock_aac.check_access_for_acms.return_value = [{"Errors": None}]

        result = client.get_audit_log_errors("test", None, 1, 500)

        assert len(result) == 1
        entry = result[0]

        assert entry["id"] == 1
        assert entry["exception_name"] == "ValueError"
        assert entry["message"] == "Something went wrong"

        mock_aac.check_access_for_acms.assert_called_once()
