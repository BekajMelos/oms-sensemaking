"""Common event consumers."""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from threading import Event, Thread
from time import sleep
from typing import Optional, Protocol
from uuid import UUID, uuid4

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError
from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)


class ObjectEvent:
    """Represents an object event from OMS."""

    def __init__(self, userDn: str, objectId: UUID, objectType: ObjectType, eventType: Action):
        """
        Create a new instance of ObjectEvent.

        :param userDn: The distinguished name (DN) of the user that triggered the event.
        :param objectId: The unique if of the object in OMS.
        :param objectType: The type of object that the event was triggered on.
        :param eventType: They type of event (e.g. create, update, or delete).
        """
        self.userDn: str = userDn
        self.objectId: UUID = objectId
        self.objectType: ObjectType = objectType
        self.eventType: Action = eventType

    def to_json(self) -> str:
        """Return a JSON representation of the event."""
        return json.dumps(self.__dict__)

    @staticmethod
    def from_dict(data: dict):
        """
        Create a new instance of ObjectEvent from a dictionary.

        This function will set the ``objectType`` to ``ATTRIBUTE`` by default,
        if ``objectType`` is not set or returns None.
        """
        return ObjectEvent(
            str(data.get("userDn")),
            UUID(data.get("objectId", "")),
            ObjectType(data.get("objectType", "ATTRIBUTE")),
            Action(data.get("eventType", "")),
        )

    @classmethod
    def from_json(cls, json_data: str):
        """
        Create a new instance of ObjectEvent from a JSON string.

        This function will set the ``objectType`` to ``ATTRIBUTE`` by default,
        if ``objectType`` is not set or returns None.
        """
        return cls.from_dict(json.loads(json_data))


EVENT_HANDLER = Callable[[ObjectEvent], bool]


class EventFilter(Protocol):
    def passes_filter(self, object_event: ObjectEvent) -> bool: ...


class ObjectEventConsumer(ABC):
    """Provides a client interface to a data source (i.e. a data producer)."""

    def __init__(self, handle_event: Optional[EVENT_HANDLER] = None):
        """
        Create a new instances of EventConsumer.

        This method sets the event handler and should be invoked by subclasses if they override ``__init__()``.

        :param handle_event: The event handler (i.e. a Callable with the event as a single argument).
        """
        #: An event handler callable that accepts a reference to this consumer and the event.
        self.handle_event: Optional[EVENT_HANDLER] = handle_event

        #: Indicates if the consumer is running (i.e. cleared) or stopped (i.e. set).
        self.stopped: Event = Event()

        self.__data_consumer: Optional[Thread] = None

    def start(self) -> None:
        """
        Start consuming events.

        This method should be overridden by subclasses to begin producing
        """
        if self.__data_consumer is None:
            self.__data_consumer = Thread(target=self.process_object_events)
            self.stopped.clear()
            self.__data_consumer.start()

    def stop(self) -> None:
        """Stop consuming events."""
        self.stopped.set()  # this signals to the data consumer that it should stop processing and exit.

        if self.__data_consumer is not None:
            LOGGER.debug("Stopping data consumer thread.")
            self.__data_consumer.join()

    @abstractmethod
    def process_object_events(self) -> None:
        """
        Process object events from a data source.

        Subclasses should override this and call ``self.event_handler.handle_event`` for
        each ``ObjectEvent`` processed.
        """
        raise NotImplementedError()


class BaseSQSListener(ObjectEventConsumer):
    """An abstract base class for SQS object event consumers."""

    def __init__(
        self,
        name: str,
        queue_url: str,
        handle_event: Optional[EVENT_HANDLER] = None,
        event_filter: Optional[EventFilter] = None,
    ):
        """Create a new instance of SQSListener."""
        super().__init__(handle_event)
        self._name = name
        self._queue_url = queue_url
        self._event_filter = event_filter

        #: SQS client.
        self.sqs: BaseClient = boto3.client(
            "sqs",
            region_name=SETTINGS.aws_region_name,
            use_ssl=SETTINGS.aws_use_ssl,
            verify=SETTINGS.aws_verify,
            endpoint_url=SETTINGS.aws_endpoint_url,
            aws_access_key_id=SETTINGS.aws_access_key_id,
            aws_secret_access_key=SETTINGS.aws_secret_access_key,
        )

    @abstractmethod
    def process_object_events(self) -> None:
        """
        Process object events from an SQS queue.

        Subclasses should override this and call ``self.event_handler.handle_event`` for
        each ``ObjectEvent`` processed.
        """
        raise NotImplementedError()


class SQSListener(BaseSQSListener):
    """An SQS ObjectEventConsumer that consumes OMS events."""

    def __init__(
        self,
        name: str,
        queue_url: str,
        handle_event: Optional[EVENT_HANDLER] = None,
        event_filter: Optional[EventFilter] = None,
    ):
        """Create a new instance of SqsObjectEventConsumer."""
        super().__init__(name, queue_url, handle_event, event_filter)

    def process_object_events(self) -> None:
        """Process object events from OMS."""
        if not callable(self.handle_event):
            raise ValueError(f"handle_event must be a callable object, got {type(self.handle_event)}")

        while not self.stopped.is_set():
            LOGGER.info("Waiting for events in SQS")

            for _ in range(0, SETTINGS.sqs_read_loops):
                if self.stopped.is_set():
                    LOGGER.debug(f"Shutting down {self._name}")
                    break

                # Receive message from SQS queue
                LOGGER.info(f"{self._name} checking queue with url {self._queue_url}")
                try:
                    response = self.sqs.receive_message(
                        QueueUrl=self._queue_url,
                        AttributeNames=["SentTimestamp"],
                        MaxNumberOfMessages=10,
                        MessageAttributeNames=["All"],
                        VisibilityTimeout=0,
                        WaitTimeSeconds=0,
                    )
                except (BotoCoreError, self.sqs.exceptions.QueueDoesNotExist) as ex:
                    LOGGER.error(f"Unable to connect to SQS: {ex}. Trying again...")
                    break

                if "Messages" not in response:
                    LOGGER.debug("No Messages in response.")
                    sleep(SETTINGS.sqs_read_wait_seconds)
                    continue

                for message in response["Messages"]:
                    object_event: ObjectEvent = ObjectEvent.from_json((message["Body"]))

                    if self._event_filter and not self._event_filter.passes_filter(object_event):
                        LOGGER.warning(
                            f"{self._name} Filtered {object_event.eventType} {object_event.objectType}:"
                            + f"{object_event.objectId} from queue {self._queue_url}"
                        )
                        self.sqs.delete_message(QueueUrl=self._queue_url, ReceiptHandle=message["ReceiptHandle"])
                        continue

                    LOGGER.info(
                        f"{self._name} Received {object_event.eventType} {object_event.objectType}:"
                        + f"{object_event.objectId}"
                    )

                    if self.handle_event(object_event):
                        # Delete received message from queue - required, so you don't get the same message
                        LOGGER.info(f"Deleting processed object {object_event.objectId} from {self._queue_url}")
                        self.sqs.delete_message(QueueUrl=self._queue_url, ReceiptHandle=message["ReceiptHandle"])
                    else:
                        LOGGER.warning("object event was not processed successfully.")


class DummyObjectEventConsumer(ObjectEventConsumer):
    """A simple object event consumer for testing purposes."""

    def __init__(self, handle_event: Optional[EVENT_HANDLER] = None):
        """Create a new instance of DummyObjectEventConsumer."""
        super().__init__(handle_event)

    def process_object_events(self) -> None:
        """Mimics event processing."""
        count: int = 0
        LOGGER.info("subscribing to SQS events")

        while not self.stopped.is_set():
            sleep(5)
            event: ObjectEvent = ObjectEvent(SETTINGS.user_dn, uuid4(), ObjectType.ATTRIBUTE, Action.CREATE)

            if callable(self.handle_event):
                self.handle_event(event)
                count = count + 1


class NoOpEventConsumer(ObjectEventConsumer):
    """A simple object event consumer intended as a placeholder."""

    def __init__(self, handle_event: Optional[EVENT_HANDLER] = None):
        """Create a new instance ofr NoOpEventConsumer."""
        super().__init__(handle_event)

    def process_object_events(self) -> None:
        """No-Op."""
        pass
