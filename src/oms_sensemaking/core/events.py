"""Common event consumers."""

import json
import logging
import socket
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Event, Thread
from time import sleep, time
from typing import Protocol
from uuid import UUID, uuid4

import pika
import pika.spec
from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel
from pika.channel import Channel
from pika.exceptions import AMQPChannelError, AMQPConnectionError

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.event_model import AuditLogHeaders, DefaultHeaders, HeaderParser
from oms_sensemaking.core.observability import record_processing_failure, record_processing_success
from oms_sensemaking.core.settings import Settings as AppSettings

LOGGER: logging.Logger = logging.getLogger(__name__)


class Properties(pika.spec.BasicProperties):
    """Basic wrapper for encapsulating message properties from a consumer"""

    pass


class AuditLogEvent:
    """Represents an audit log event from OMS."""

    def __init__(self, userId: str, objectId: UUID, objectType: ObjectType, action: Action):
        """
        Create a new instance of AuditLogEvent.

        :param userId: The id of the user that triggered the event.
        :param objectId: The unique id of the object in OMS.
        :param objectType: The type of object that the event was triggered on.
        :param action: They type of event (e.g. create, update, or delete).
        """
        self.userId: str = userId
        self.objectId: UUID = objectId
        self.objectType: ObjectType = objectType
        self.action: Action = action
        self._headers: AuditLogHeaders = DefaultHeaders()

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value: AuditLogHeaders):
        """The setter for the headers"""
        if not value:
            raise ValueError("headers cannot be empty")
        self._headers = value

    def to_json(self) -> str:
        """Return a JSON representation of the event."""
        return json.dumps(self.__dict__)

    @staticmethod
    def from_dict(data: dict):
        """
        Create a new instance of AuditLogEvent from a dictionary.

        This function will set the ``objectType`` to ``ATTRIBUTE`` by default,
        if ``objectType`` is not set or returns None.
        """
        return AuditLogEvent(
            str(data.get("userId")),
            UUID(data.get("objectId", "")),
            ObjectType(data.get("objectType", "ATTRIBUTE")),
            Action(data.get("action", "")),
        )

    @classmethod
    def from_json(cls, json_data: str):
        """
        Create a new instance of AuditLogEvent from a JSON string.

        This function will set the ``objectType`` to ``ATTRIBUTE`` by default,
        if ``objectType`` is not set or returns None.
        """
        return cls.from_dict(json.loads(json_data))


EVENT_HANDLER = Callable[[AuditLogEvent], bool]


class EventFilter(Protocol):
    def passes_filter(self, audit_log_event: AuditLogEvent) -> bool: ...


class AuditLogEventConsumer(ABC):
    """Provides a client interface to a data source (i.e. a data producer)."""

    def __init__(self, handle_event: EVENT_HANDLER | None = None):
        """
        Create a new instances of EventConsumer.

        This method sets the event handler and should be invoked by subclasses if they override ``__init__()``.

        :param handle_event: The event handler (i.e. a Callable with the event as a single argument).
        """
        #: An event handler callable that accepts a reference to this consumer and the event.
        self.handle_event: EVENT_HANDLER | None = handle_event

        #: Indicates if the consumer is running (i.e. cleared) or stopped (i.e. set).
        self.stopped: Event = Event()

        self.__data_consumer: Thread | None = None

    def start(self) -> None:
        """
        Start consuming events.

        This method should be overridden by subclasses to begin producing
        """
        if self.__data_consumer is None:
            self.__data_consumer = Thread(target=self.process_audit_log_events)
            self.stopped.clear()
            self.__data_consumer.start()

    def stop(self) -> None:
        """Stop consuming events."""
        self.stopped.set()  # this signals to the data consumer that it should stop processing and exit.

        if self.__data_consumer is not None:
            LOGGER.debug("Stopping data consumer thread.")
            self.__data_consumer.join()

    @abstractmethod
    def process_audit_log_events(self) -> None:
        """
        Process audit log events from a data source.

        Subclasses should override this and call ``self.event_handler.handle_event`` for
        each ``AuditLogEvent`` processed.
        """
        raise NotImplementedError()


class BaseRabbitMQListener(AuditLogEventConsumer):
    """An abstract base class for RabbitMQ audit log event consumers."""

    def __init__(
        self,
        name: str,
        queue_name: str,
        app_settings: AppSettings,
        handle_event: EVENT_HANDLER | None = None,
        event_filter: EventFilter | None = None,
    ):
        """Create a new instance of BaseRabbitMQListener."""
        super().__init__(handle_event)
        self._name = name
        self._queue_name = queue_name
        self._event_filter = event_filter
        self._connection: BlockingConnection = None
        self._channel: BlockingChannel = None
        settings_dict = app_settings.get_settings()
        self._prefetch_count = settings_dict.get("rabbitmq_prefetch_count", SETTINGS.rabbitmq_prefetch_count)

    def _connect(self) -> bool:
        """Establish connection to RabbitMQ server."""
        LOGGER.info(
            "Trying to connect to %s at %s:%s", self._queue_name, SETTINGS.rabbitmq_host, SETTINGS.rabbitmq_port
        )
        try:
            credentials = PlainCredentials(SETTINGS.rabbitmq_username, SETTINGS.rabbitmq_password)
            parameters = ConnectionParameters(
                host=SETTINGS.rabbitmq_host,
                port=SETTINGS.rabbitmq_port,
                virtual_host=SETTINGS.rabbitmq_vhost,
                credentials=credentials,
            )
            self._connection = BlockingConnection(parameters)
            self._channel = self._connection.channel()
            self._channel.queue_declare(
                queue=self._queue_name, durable=True, arguments={"x-delivery-limit": -1, "x-queue-type": "quorum"}
            )
            self._channel.basic_qos(0, self._prefetch_count, False)
            LOGGER.info("Connected to RabbitMQ queue: %s", self._queue_name)
            return True
        except (AMQPConnectionError, AMQPChannelError, socket.gaierror) as ex:
            LOGGER.error("%s Failed to connect to RabbitMQ: %s", self._name, ex)
            return False

    def _disconnect(self):
        """Close connection to RabbitMQ server."""
        if self._connection and self._connection.is_open:
            try:
                self._connection.close()
                LOGGER.info("%s Disconnected from RabbitMQ", self._name)
            except Exception as ex:
                LOGGER.error("%s Error disconnecting from RabbitMQ: %s", self._name, ex)

    @abstractmethod
    def process_audit_log_events(self) -> None:
        """
        Process audit log events from a RabbitMQ queue.

        Subclasses should override this and call ``self.event_handler.handle_event`` for
        each ``AuditLogEvent`` processed.
        """
        raise NotImplementedError()


class RabbitMQListener(BaseRabbitMQListener):
    """A RabbitMQ AuditLogEventConsumer that consumes OMS events."""

    def __init__(
        self,
        name: str,
        queue_name: str,
        workers: int,
        app_settings: AppSettings,
        handle_event: EVENT_HANDLER | None = None,
        event_filter: EventFilter | None = None,
    ):
        """Create a new instance of RabbitMQListener."""
        super().__init__(name, queue_name, app_settings, handle_event, event_filter)
        self.pool = ThreadPoolExecutor(max_workers=workers)

    def callback(
        self, ch: Channel, method: pika.spec.Basic.Deliver, properties: pika.spec.BasicProperties, body: bytes
    ):
        if self.stopped.is_set():
            LOGGER.debug("Shutting down %s", self._name)
            return
        try:
            self.pool.submit(self._process_message, ch, method, properties, body)
        except Exception:
            LOGGER.exception("%s Failed to submit worker task", self._name)
            try:
                self._connection.add_callback_threadsafe(
                    lambda: ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                )
            except Exception:
                LOGGER.exception("%s Failed to schedule nack after submission failure", self._name)

    def _process_message(self, ch, method, properties, body):
        object_id = None
        start_time = time()  # Record when we start processing

        try:
            audit_log: AuditLogEvent = AuditLogEvent.from_json(body.decode("utf-8"))
            audit_log.headers = HeaderParser().parse(properties)
            LOGGER.info("%s Received %s %s: %s", self._name, audit_log.action, audit_log.objectType, audit_log.objectId)
            object_id = audit_log.objectId

            if self._event_filter and not self._event_filter.passes_filter(audit_log):
                LOGGER.warning(
                    "%s Filtered %s %s: from queue %s",
                    self._name,
                    audit_log.action,
                    audit_log.objectType,
                    self._queue_name,
                )
                self._connection.add_callback_threadsafe(lambda: ch.basic_ack(delivery_tag=method.delivery_tag))
                return

            if self.handle_event and self.handle_event(audit_log):
                LOGGER.info("Acknowledging processed object %s from %s", audit_log.objectId, self._queue_name)
                self._connection.add_callback_threadsafe(lambda: ch.basic_ack(delivery_tag=method.delivery_tag))

                # Record successful processing metrics
                record_processing_success(self._queue_name, start_time)

            else:
                LOGGER.warning(
                    "%s Audit log event (Object ID: %s) was not processed successfully.", self._name, object_id
                )
                self._connection.add_callback_threadsafe(
                    lambda: ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                )

                # Record failed processing metrics
                record_processing_failure(self._queue_name, start_time)

        except Exception:
            LOGGER.error(
                "%s Error processing message (Object ID: %s): %s", self._name, object_id, traceback.format_exc()
            )
            self._connection.add_callback_threadsafe(
                lambda: ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            )

            # Record failed processing metrics
            record_processing_failure(self._queue_name, start_time)

    def process_audit_log_events(self) -> None:
        """Process audit log events from RabbitMQ."""
        if not callable(self.handle_event):
            raise ValueError(f"{self._name}'s handle_event must be a callable object, got {type(self.handle_event)}")

        while not self.stopped.is_set():
            LOGGER.info("%s waiting for events in RabbitMQ queue %s", self._name, self._queue_name)

            if not self._connect():
                LOGGER.error("%s failed to connect to RabbitMQ. Retrying in a few seconds...", self._name)
                sleep(SETTINGS.rmq_read_wait_seconds)
                continue

            self._consume_messages()

    def _consume_messages(self):
        try:
            # Start consuming messages
            self._channel.basic_consume(queue=self._queue_name, on_message_callback=self.callback, auto_ack=False)  # type: ignore

            while not self.stopped.is_set():
                try:
                    self._connection.process_data_events(time_limit=1)
                except Exception as ex:
                    LOGGER.error("%s Error processing RabbitMQ events: %s", self._name, ex)
                    break

        except (AMQPConnectionError, AMQPChannelError) as ex:
            LOGGER.error("%s RabbitMQ connection error: %s. Reconnecting...", self._name, ex)
            sleep(SETTINGS.rmq_read_wait_seconds)
        except Exception as ex:
            LOGGER.error("%s Unexpected error in RabbitMQ listener: %s", self._name, ex)
            sleep(SETTINGS.rmq_read_wait_seconds)
        finally:
            if not self.stopped.is_set():
                try:
                    self._disconnect()
                except Exception:
                    LOGGER.exception("_disconnect() failed in finally")

            if not self.stopped.is_set():
                sleep(SETTINGS.rmq_read_wait_seconds)

    def stop(self) -> None:
        """Stop consuming events and close the connection."""
        self.stopped.set()
        self.pool.shutdown(wait=True)

        try:
            if self._connection and self._connection.is_open and self._channel and self._channel.is_open:
                self._connection.add_callback_threadsafe(lambda: self._channel.stop_consuming())
        except Exception:
            LOGGER.exception("%s Failed to schedule channel.stop_consuming", self._name)
        try:
            super().stop()
        except Exception:
            LOGGER.exception("%s Error joining consumer thread in stop()", self._name)
        try:
            self._disconnect()
        except Exception:
            LOGGER.exception("%s Error during final disconnect()", self._name)


class CronEventEmitter(AuditLogEventConsumer):
    """Emits an event repeatedly on a set time interval."""

    def __init__(self, interval: timedelta, handle_event: EVENT_HANDLER | None = None):
        """
        Create a new instance of CronEventEmitter.

        :param interval: The time interval between emitted events.
        :param handle_event: The event handler to call for each emitted event.
        """
        super().__init__(handle_event)
        self.interval = interval

    def process_audit_log_events(self) -> None:
        """Emits events on set interval until stopped."""
        while not self.stopped.is_set():
            event = AuditLogEvent(
                userId="CronJob", objectId=uuid4(), objectType=ObjectType.ATTRIBUTE, action=Action.CREATE
            )

            if callable(self.handle_event):
                LOGGER.info("Emitting periodic event at %s", datetime.now())
                self.handle_event(event)

            # sleep for the interval or until stopped
            self.stopped.wait(timeout=self.interval.total_seconds())


class DummyAuditLogEventConsumer(AuditLogEventConsumer):
    """A simple audit log event consumer for testing purposes."""

    def __init__(self, handle_event: EVENT_HANDLER | None = None):
        """Create a new instance of DummyAuditLogEventConsumer."""
        super().__init__(handle_event)

    def process_audit_log_events(self) -> None:
        """Mimics event processing."""
        count: int = 0
        LOGGER.info("subscribing to RMQ events")

        while not self.stopped.is_set():
            sleep(5)
            event: AuditLogEvent = AuditLogEvent(SETTINGS.user_dn, uuid4(), ObjectType.ATTRIBUTE, Action.CREATE)

            if callable(self.handle_event):
                self.handle_event(event)
                count = count + 1


class NoOpEventConsumer(AuditLogEventConsumer):
    """A simple audit log event consumer intended as a placeholder."""

    def __init__(self, handle_event: EVENT_HANDLER | None = None):
        """Create a new instance ofr NoOpEventConsumer."""
        super().__init__(handle_event)

    def process_audit_log_events(self) -> None:
        """No-Op."""
        pass
