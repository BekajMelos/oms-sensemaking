from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

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


class TestAuditLogErrorClass:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup the buffer"""
        self.client = AuditLogErrorClient()
        yield

    def test_get_audit_log_errors_no_results(self):
        """Should return empty list when DB query returns none."""

        with (
            patch("oms_sensemaking.clients.audit_log_error_client.db_session") as mock_db_session,
        ):
            # Mock context manager for db_session()
            mock_db = MagicMock()
            mock_db.query().order_by().limit().offset().all.return_value = []
            mock_db_session.return_value.__enter__.return_value = mock_db

            result = self.client.get_audit_log_errors("user_dn", None, None, None, 1, 500)
            assert result == []

    def test_get_audit_log_errors_success(self):
        """Should return formatted errors when AAC access allows all entries."""
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

            result = self.client.get_audit_log_errors("user_dn", None, None, None, 1, 500)

            assert len(result) == 1
            entry = result[0]

            assert entry["id"] == 1
            assert entry["exception_name"] == "ValueError"
            assert entry["message"] == "Something went wrong"

            mock_aac.check_access_for_acms.assert_called_once()

    def test_get_audit_log_errors_with_filters(self):
        """Should return formatted errors when AAC access allows all entries."""

        mock_error1 = make_mock_error(1)
        mock_error2 = make_mock_error(2)
        mock_errors = [mock_error1, mock_error2]

        exception_name = "TypeError"
        created_at_start = "2026-01-01T00:00:00+00:00"
        created_at_end = "2026-01-04T00:00:00+00:00"

        with (
            patch("oms_sensemaking.clients.audit_log_error_client.db_session") as mock_db_session,
            patch("oms_sensemaking.clients.audit_log_error_client.aac_client") as mock_aac,
        ):
            # DB returns one error record
            mock_db = MagicMock()

            # mock query building
            mock_query = mock_db.query.return_value
            mock_query.order_by.return_value = mock_query
            mock_query.where.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.all.return_value = mock_errors

            mock_db_session.return_value.__enter__.return_value = mock_db

            # AAC returns access allowed (no "Errors" entry)
            mock_aac.check_access_for_acms.return_value = [{"Errors": None}, {"Errors": None}]

            result = self.client.get_audit_log_errors(
                "user_dn", exception_name, created_at_start, created_at_end, 1, 500
            )

            assert len(result) == 2
            mock_db.query.assert_called_with(AuditLogError)

            assert mock_query.where.call_count == 3
            where_calls = mock_query.where.call_args_list

            assert (AuditLogError.exception_name == exception_name).compare(where_calls[0][0][0])
            assert (AuditLogError.created_at >= created_at_start).compare(where_calls[1][0][0])
            assert (AuditLogError.created_at <= created_at_end).compare(where_calls[2][0][0])

    # TODO parameterize?
    def test_delete_audit_log_errors_success(self):
        """Should delete errors"""

        with patch("oms_sensemaking.clients.audit_log_error_client.db_session") as mock_db_session:
            # DB returns one error record
            mock_db = MagicMock()
            mock_db_session.return_value.__enter__.return_value = mock_db

            exception_name = "TypeError"
            created_at_start = "2026-01-01T00:00:00+00:00"
            created_at_end = "2026-01-04T00:00:00+00:00"

            self.client.delete_audit_log_errors(exception_name, created_at_start, created_at_end)

            args, _ = mock_db.execute.call_args
            stmt = args[0]

            assert stmt.is_delete
            assert stmt.table.name == AuditLogError.__tablename__

            params = stmt.compile().params
            assert params["exception_name_1"] == exception_name
            assert params["created_at_1"] == created_at_start
            assert params["created_at_2"] == created_at_end
