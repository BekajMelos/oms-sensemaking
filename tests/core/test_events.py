"""Module for testing event listeners"""

import socket
from unittest import mock

from oms_sensemaking.core.events import BaseRabbitMQListener


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
@mock.patch("oms_sensemaking.core.logging.handlers.DatabaseHandler.emit")
def test_rmq_listeners(mock_database_logger, mock_connection: mock.MagicMock):
    """Test exception handling with rabbit mq connections"""
    mock_connection.side_effect = [socket.gaierror]
    listener = DummyRabbitMQListener("test", "test-queue", None, None)
    assert not listener.process_audit_log_events()
