"""Test DB Logging"""

import uuid
from unittest import mock

import pytest
from sqlalchemy.orm import Session

from oms_sensemaking import __version__
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.error_loggers import ErrorLogger, RethrowErrorLogger
from oms_sensemaking.core.events import AuditLogEvent
from oms_sensemaking.models.logs import AuditLogError


@mock.patch("oms_sensemaking.core.error_loggers.db_session")
def test_db_error_logging(mock_db_session: Session):
    """Test that errors are logged to DB"""

    node_id = str(uuid.uuid4())
    event = AuditLogEvent(objectId=node_id, userId="user", objectType="NODE", action="CREATE")

    error_logger = ErrorLogger()

    db_mock = mock.MagicMock()
    mock_db_session_instance = mock.MagicMock()
    mock_db_session.return_value = mock_db_session_instance
    mock_db_session_instance.__enter__ = db_mock
    last_mock = mock.MagicMock()
    db_mock.return_value = last_mock

    expected_audit_event = AuditLogError(
        acm=SETTINGS.audit_log_error_acm,
        object_id=node_id,
        object_type="NODE",
        event_type="CREATE",
        module_name=__file__,
        line_no=49,  # from the line above in test_error
        function_name="test_db_error_logging",
        code="_ = empty_list[1]",
        exception_name="IndexError",
        version=__version__,
        message=None,
        exc_text=None,
    )

    try:
        empty_list = []
        _ = empty_list[1]
    except IndexError as e:
        error_logger.log_error(event, "dummy message", "module", e, None)

    last_mock.add.assert_called_with(expected_audit_event)


@mock.patch("oms_sensemaking.core.error_loggers.db_session")
def test_rethrow_db_error_logging(mock_db_session: Session, ts_acm):
    """Test that errors are logged to DB"""

    node_id = str(uuid.uuid4())
    event = AuditLogEvent(objectId=node_id, userId="user", objectType="NODE", action="CREATE")

    error_logger = ErrorLogger()
    rethrow_error_logger = RethrowErrorLogger(error_logger)

    db_mock = mock.MagicMock()
    mock_db_session_instance = mock.MagicMock()
    mock_db_session.return_value = mock_db_session_instance
    mock_db_session_instance.__enter__ = db_mock
    last_mock = mock.MagicMock()
    db_mock.return_value = last_mock

    # limit to 100 chars since the paths won't be accurate in build job
    SETTINGS.audit_log_error_max_tb_chars = 100
    truncated_expected_exc_text = (
        "  _ = foo.fake_attr\n        ^^^^^^^^^^^^^\nAttributeError: 'Foo' object has no attribute 'fake_attr'\n"
    )

    expected_audit_event = AuditLogError(
        acm=ts_acm,
        object_id=node_id,
        object_type="NODE",
        event_type="CREATE",
        module_name=__file__,
        line_no=101,  # from the line above in test_error
        function_name="test_rethrow_db_error_logging",
        code="_ = foo.fake_attr",
        exception_name="AttributeError",
        version=__version__,
        message="dummy message",
        exc_text=truncated_expected_exc_text,
    )

    with pytest.raises(AttributeError):
        try:

            class Foo:
                attr = 1

            foo = Foo()
            _ = foo.fake_attr
        except AttributeError as e:
            rethrow_error_logger.log_error(event, "dummy message", "module", e, ts_acm)

    last_mock.add.assert_called_with(expected_audit_event)
