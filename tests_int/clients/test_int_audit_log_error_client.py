import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from oms_sdk import DEFAULT_ACM
from sqlalchemy import delete
from sqlalchemy.orm import Session

from oms_sensemaking.clients.audit_log_error_client import AuditLogErrorClient
from oms_sensemaking.models.logs import AuditLogError

TEST_PARAMETERS = [
    (
        "KeyError",
        datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 3, 0, 0, 0, tzinfo=timezone.utc),
        2,
    ),
    ("TypeError", None, datetime(2026, 1, 4, 0, 0, 0, tzinfo=timezone.utc), 1),
    (
        None,
        datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 5, 0, 0, 0, tzinfo=timezone.utc),
        4,
    ),
    (None, datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc), None, 0),
    (None, None, None, 0),
]


@pytest.fixture
def tester_db(db: Session):
    """Helper to create AuditLogError entries in the DB"""

    times_and_exceptions = [
        (datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), "KeyError"),
        (datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc), "KeyError"),
        (datetime(2026, 1, 3, 0, 0, 0, tzinfo=timezone.utc), "TypeError"),
        (datetime(2026, 1, 4, 0, 0, 0, tzinfo=timezone.utc), "TypeError"),
        (datetime(2026, 1, 5, 0, 0, 0, tzinfo=timezone.utc), "AttributeError"),
        (datetime(2026, 1, 6, 0, 0, 0, tzinfo=timezone.utc), "AttributeError"),
    ]

    errors = []

    for time_and_exception in times_and_exceptions:
        error = AuditLogError(
            object_id=uuid.uuid4(),
            object_type="ATTRIBUTE",
            event_type="CREATE",
            module_name="oms_sensemaking.models.logs",
            line_no=12345678,
            function_name="my_func",
            code="code_text",
            exc_text="Exception('this is exception text')",
            message="Error handling audit log message. Here is the error",
            acm=DEFAULT_ACM,
            exception_name=time_and_exception[1],
            version="0.1.0",
        )
        error.created_at = time_and_exception[0]
        errors.append(error)

    db.add_all(errors)
    db.commit()

    yield errors

    # cleanup created AuditLogErrors
    query = delete(AuditLogError).where(AuditLogError.line_no == 12345678)
    db.execute(query)
    db.commit()


class TestAuditLogErrorClass:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup the buffer"""
        self.client = AuditLogErrorClient()
        yield

    @pytest.mark.parametrize(
        "exception_name, created_at_start, created_at_end, expected_count",
        TEST_PARAMETERS,
    )
    def test_get_audit_log_errors_success(
        self, exception_name, created_at_start, created_at_end, expected_count, tester_db, db
    ):
        """Should return formatted errors when AAC access allows all entries."""

        with (
            patch("oms_sensemaking.clients.audit_log_error_client.aac_client") as mock_aac,
        ):
            # AAC returns access allowed (no "Errors" entry)
            # the len of response should match the expected number of AuditLogErrors
            mock_aac.check_access_for_acms.return_value = [{"Errors": None} for _ in range(expected_count)]

            result = self.client.get_audit_log_errors(
                "user_dn", exception_name, created_at_start, created_at_end, 1, 500
            )
            assert len(result) == expected_count

    @pytest.mark.parametrize(
        "exception_name, created_at_start, created_at_end, expected_count",
        TEST_PARAMETERS,
    )
    def test_delete_audit_log_errors_success(
        self, exception_name, created_at_start, created_at_end, expected_count, tester_db, db
    ):
        """Should delete errors"""

        count = self.client.delete_audit_log_errors(exception_name, created_at_start, created_at_end)
        assert count == expected_count
