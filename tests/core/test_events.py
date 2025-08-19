"""Module for testing event listeners"""

import socket
import time
from datetime import timedelta
from unittest import mock
from unittest.mock import MagicMock

from oms_sensemaking.core.events import AuditLogEvent, BaseRabbitMQListener, CronEventEmitter


class DummyRabbitMQListener(BaseRabbitMQListener):
    """Dummy RabbitMQ Listener class"""

    def process_audit_log_events(self) -> None:
        """
        Process audit log events from a RabbitMQ queue.

        Subclasses should override this and call ``self.event_handler.handle_event`` for
        each ``AuditLogEvent`` processed.
        """
        print("Fake processing data. Calling self._connect()")
        return self._connect()


@mock.patch("oms_sensemaking.core.events.BlockingConnection")
def test_rmq_listeners(mock_connection: mock.MagicMock):
    """Test exception handling with rabbit mq connections"""
    mock_connection.side_effect = [socket.gaierror]
    listener = DummyRabbitMQListener("test", "test-queue", None, None)
    assert not listener.process_audit_log_events()


def test_cron_event_emitter_initialization():
    """Test CronEventEmitter initialization"""
    interval = timedelta(seconds=5)
    emitter = CronEventEmitter(interval)

    assert emitter.interval == interval
    assert emitter.handle_event is None
    assert not emitter.stopped.is_set()


def test_cron_event_emitter_with_handler():
    """Test CronEventEmitter with event handler"""
    interval = timedelta(seconds=1)
    mock_handler = MagicMock(return_value=True)
    emitter = CronEventEmitter(interval, mock_handler)

    assert emitter.handle_event == mock_handler


@mock.patch("oms_sensemaking.core.events.datetime")
@mock.patch("oms_sensemaking.core.events.LOGGER")
def test_cron_event_emitter_emits_events(mock_logger, mock_datetime):
    """Test that CronEventEmitter emits events when running"""
    mock_datetime.now.return_value = "2023-01-01 12:00:00"

    interval = timedelta(milliseconds=100)  # Short interval for testing
    mock_handler = MagicMock(return_value=True)
    emitter = CronEventEmitter(interval, mock_handler)

    # Start the emitter
    emitter.start()

    # Let it run for a short time
    time.sleep(0.25)  # Should allow 2-3 events

    # Stop the emitter
    emitter.stop()

    # Verify events were emitted
    assert mock_handler.call_count >= 1

    # Check that the handler was called with AuditLogEvent
    call_args = mock_handler.call_args_list[0][0]
    assert len(call_args) == 1
    event = call_args[0]
    assert isinstance(event, AuditLogEvent)
    assert event.userId == "CronJob"

    # Check logging
    mock_logger.info.assert_called()


def test_cron_event_emitter_without_handler():
    """Test CronEventEmitter behavior when no handler is provided"""
    interval = timedelta(milliseconds=50)
    emitter = CronEventEmitter(interval)

    # Start the emitter
    emitter.start()

    # Let it run briefly
    time.sleep(0.1)

    # Stop the emitter
    emitter.stop()

    # Should not raise any exceptions even without a handler
    assert emitter.handle_event is None


def test_cron_event_emitter_stop_before_start():
    """Test stopping emitter before starting"""
    interval = timedelta(seconds=1)
    emitter = CronEventEmitter(interval)

    # Should not raise exception
    emitter.stop()
    assert emitter.stopped.is_set()


@mock.patch("oms_sensemaking.core.events.uuid4")
def test_cron_event_emitter_event_properties(mock_uuid):
    """Test the properties of emitted events"""
    from uuid import UUID

    from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

    mock_uuid_value = UUID("12345678-1234-5678-1234-567812345678")
    mock_uuid.return_value = mock_uuid_value

    interval = timedelta(milliseconds=50)
    captured_events = []

    def capture_event(event):
        captured_events.append(event)
        return True

    emitter = CronEventEmitter(interval, capture_event)

    # Start and let it emit one event
    emitter.start()
    time.sleep(0.1)
    emitter.stop()

    # Verify event properties
    assert len(captured_events) >= 1
    event = captured_events[0]
    assert event.userId == "CronJob"
    assert event.objectId == mock_uuid_value
    assert event.objectType == ObjectType.ATTRIBUTE
    assert event.action == Action.CREATE
