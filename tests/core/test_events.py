"""Module for testing event listeners"""

import json
import socket
import time
import uuid
from datetime import timedelta
from unittest import mock
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.core.events import (
    AuditLogEvent,
    AuditLogEventConsumer,
    BaseRabbitMQListener,
    CronEventEmitter,
    DummyAuditLogEventConsumer,
    NoOpEventConsumer,
    RabbitMQListener,
)


def test_audit_log_from_dict():
    obj = {
        "userId": "Sam Snow",
        "objectId": "12345678-1234-5678-1234-567812345678",
        "objectType": ObjectType.NODE,
        "action": Action.CREATE,
    }
    audit_log = AuditLogEvent.from_dict(obj)

    assert audit_log.userId == "Sam Snow"
    assert audit_log.objectId == uuid.UUID("12345678-1234-5678-1234-567812345678")
    assert audit_log.objectType == ObjectType.NODE
    assert audit_log.action == Action.CREATE


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


class TestAuditLogEvent:
    def test_to_json_roundtrip(self):
        event = AuditLogEvent(
            userId="user123",
            objectId="12345",
            objectType=ObjectType.ATTRIBUTE,
            action=Action.CREATE,
        )

        json_str = event.to_json()
        parsed = json.loads(json_str)

        assert parsed["userId"] == "user123"
        assert parsed["objectId"] == "12345"
        assert parsed["objectType"] == ObjectType.ATTRIBUTE.value
        assert parsed["action"] == Action.CREATE.value

    def test_from_dict_with_defaults(self):
        obj_id = uuid4()
        data = {
            "userId": "user456",
            "objectId": str(obj_id),
            "action": Action.UPDATE.value,
            # objectType intentionally omitted
        }

        event = AuditLogEvent.from_dict(data)

        assert event.userId == "user456"
        assert event.objectId == obj_id
        assert event.objectType == ObjectType.ATTRIBUTE  # default
        assert event.action == Action.UPDATE

    def test_from_json_roundtrip(self):
        obj_id = uuid4()
        data = {
            "userId": "user789",
            "objectId": str(obj_id),
            "objectType": ObjectType.ATTRIBUTE.value,
            "action": Action.DELETE.value,
        }
        json_str = json.dumps(data)

        event = AuditLogEvent.from_json(json_str)

        assert event.userId == "user789"
        assert event.objectId == obj_id
        assert event.objectType == ObjectType.ATTRIBUTE
        assert event.action == Action.DELETE


def test_audit_log_event_headers_rejects_empty():
    event = AuditLogEvent(
        userId="user",
        objectId=uuid4(),
        objectType=ObjectType.ATTRIBUTE,
        action=Action.CREATE,
    )

    with pytest.raises(ValueError):
        event.headers = None


class DummyConsumer(AuditLogEventConsumer):
    def process_audit_log_events(self):
        while not self.stopped.is_set():
            break


def long_running_stub(self):
    time.sleep(5)


class TestAuditLogEventConsumer:
    def test_stop_sets_stopped_flag(self):
        consumer = DummyConsumer()
        consumer.start()
        consumer.stop()
        assert consumer.stopped.is_set()

    def test_handle_event_is_called(self):
        mock_handler = MagicMock()
        consumer = DummyConsumer(handle_event=mock_handler)

        event = AuditLogEvent(
            userId="user123",
            objectId=uuid4(),
            objectType=ObjectType.ATTRIBUTE,
            action=Action.CREATE,
        )

        # simulate calling the handler manually
        consumer.handle_event(consumer, event)
        mock_handler.assert_called_once_with(consumer, event)


@mock.patch("oms_sensemaking.core.events.HeaderParser")
@mock.patch("oms_sensemaking.core.events.record_processing_success")
def test_rabbitmq_listener_process_message_success(mock_metric, mock_header_parser):
    # must be truthy or headers.setter raises ValueError
    mock_header_parser.return_value.parse.return_value = {"foo": "bar"}

    handler = MagicMock(return_value=True)

    listener = RabbitMQListener(
        name="TestListener",
        queue_name="test-q",
        workers=1,
        handle_event=handler,
    )

    listener._connection = MagicMock()
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "abc123"

    body = json.dumps(
        {
            "userId": "u1",
            "objectId": str(uuid4()),
            "objectType": ObjectType.NODE.value,
            "action": Action.CREATE.value,
        }
    ).encode()

    listener._process_message(ch, method, MagicMock(), body)

    handler.assert_called_once()
    listener._connection.add_callback_threadsafe.assert_called()
    mock_metric.assert_called()


@mock.patch("oms_sensemaking.core.events.HeaderParser")
@mock.patch("oms_sensemaking.core.events.record_processing_failure")
def test_rabbitmq_listener_process_message_failure(mock_metric, mock_header_parser):
    mock_header_parser.return_value.parse.return_value = {"foo": "bar"}

    handler = MagicMock(return_value=False)

    listener = RabbitMQListener(
        name="TestListener",
        queue_name="test-q",
        workers=1,
        handle_event=handler,
    )

    listener._connection = MagicMock()
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "abc123"

    body = json.dumps(
        {
            "userId": "u1",
            "objectId": str(uuid4()),
            "objectType": ObjectType.NODE.value,
            "action": Action.UPDATE.value,
        }
    ).encode()

    listener._process_message(ch, method, MagicMock(), body)

    handler.assert_called_once()
    listener._connection.add_callback_threadsafe.assert_called()
    mock_metric.assert_called()


class AlwaysFilter:
    def passes_filter(self, *_):
        return False


@mock.patch("oms_sensemaking.core.events.HeaderParser")
def test_rabbitmq_listener_filters_messages(mock_header_parser):
    mock_header_parser.return_value.parse.return_value = {}

    handler = MagicMock()

    listener = RabbitMQListener(
        name="TestListener",
        queue_name="test-q",
        workers=1,
        handle_event=handler,
        event_filter=AlwaysFilter(),
    )

    listener._connection = MagicMock()
    ch = MagicMock()
    method = MagicMock()
    method.delivery_tag = "abc"

    body = json.dumps(
        {
            "userId": "u1",
            "objectId": str(uuid4()),
            "objectType": ObjectType.ATTRIBUTE.value,
            "action": Action.CREATE.value,
        }
    ).encode()

    listener._process_message(ch, method, MagicMock(), body)

    handler.assert_not_called()
    listener._connection.add_callback_threadsafe.assert_called()


def test_rabbitmq_listener_requires_callable():
    listener = RabbitMQListener(
        name="TestListener",
        queue_name="q",
        workers=1,
        handle_event=None,
    )

    with pytest.raises(ValueError):
        listener.process_audit_log_events()


def test_noop_event_consumer_runs_and_stops():
    consumer = NoOpEventConsumer()
    consumer.start()
    consumer.stop()
    assert consumer.stopped.is_set()


def test_dummy_audit_log_consumer_lifecycle():
    consumer = DummyAuditLogEventConsumer()
    consumer.start()
    consumer.stop()
    assert consumer.stopped.is_set()


def test_rabbitmq_listener_stop_closes_resources():
    handler = MagicMock(return_value=True)

    listener = RabbitMQListener(
        name="TestListener",
        queue_name="q",
        workers=1,
        handle_event=handler,
    )

    listener._connection = MagicMock()
    listener._connection.is_open = True

    listener._channel = MagicMock()
    listener._channel.is_open = True

    listener.stop()

    # pool shutdown should happen without error
    assert listener.stopped.is_set()

    # stop_consuming should have been scheduled
    listener._connection.add_callback_threadsafe.assert_called()


def test_update_prefetch_no_change():
    listener = RabbitMQListener("L", "q", workers=1, handle_event=lambda *_: True)
    listener._prefetch_count = 10
    listener._connection = MagicMock(is_open=True)

    listener.update_prefetch(10)

    listener._connection.add_callback_threadsafe.assert_not_called()


def test_update_prefetch_schedules_callback():
    listener = RabbitMQListener("L", "q", workers=1, handle_event=lambda *_: True)
    listener._prefetch_count = 5
    listener._connection = MagicMock(is_open=True)

    listener.update_prefetch(20)

    listener._connection.add_callback_threadsafe.assert_called_once()


@mock.patch("oms_sensemaking.core.events.Thread")
def test_apply_prefetch_update_cancels_consumer_and_starts_thread(mock_thread):
    listener = RabbitMQListener("L", "q", workers=1, handle_event=lambda *_: True)

    listener._channel = MagicMock(is_open=True)
    listener._consumer_tag = "tag123"
    listener._prefetch_count = 5

    listener._apply_prefetch_update(15)

    listener._channel.basic_cancel.assert_called_once_with("tag123")
    assert listener._consumer_tag is None
    assert listener._prefetch_count == 15
    mock_thread.assert_called_once()


@mock.patch("oms_sensemaking.core.events.ThreadPoolExecutor")
def test_drain_pool_and_reconnect_recreates_pool(mock_executor):
    listener = RabbitMQListener("L", "q", workers=4, handle_event=lambda *_: True)

    mock_pool = MagicMock()
    listener.pool = mock_pool

    listener._connection = MagicMock(is_open=True)
    listener._disconnect = MagicMock()

    listener._drain_pool_and_reconnect()

    mock_pool.shutdown.assert_called_once_with(wait=True)
    assert mock_executor.call_args_list[-1] == mock.call(max_workers=4)
    listener._disconnect.assert_called_once()


def test_drain_pool_without_connection():
    listener = RabbitMQListener("L", "q", workers=1, handle_event=lambda *_: True)

    mock_pool = MagicMock(_max_workers=2)
    listener.pool = mock_pool

    listener._drain_pool_and_reconnect()

    mock_pool.shutdown.assert_called_once_with(wait=True)


def test_update_prefetch_logs_exception():
    listener = RabbitMQListener("L", "q", workers=1, handle_event=lambda *_: True)

    listener._connection = MagicMock()
    listener._connection.is_open = True
    listener._connection.add_callback_threadsafe.side_effect = Exception("boom")

    # Should not raise
    listener.update_prefetch(20)
