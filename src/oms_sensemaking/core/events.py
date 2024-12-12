"""Common event consumers."""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from threading import Event, Thread
from time import sleep
from typing import Optional
from uuid import UUID, uuid4

import boto3
from botocore.client import BaseClient
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
            ObjectType(data.get("objectType", "OBSERVATION")),
            Action(data.get("eventType", ""))
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


class SQSListener(ObjectEventConsumer):
    """An abstract base class for SQS object event consumers."""

    def __init__(self, handle_event: Optional[EVENT_HANDLER] = None):
        """Create a new instance of SQSListener."""
        super().__init__(handle_event)

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


class DummyObjectEventConsumer(ObjectEventConsumer):
    """A simple object event consumer for testing purposes."""

    def __init__(self, handle_event: Optional[EVENT_HANDLER] = None):
        """Create a new instance of DummyObjectEventConsumer."""
        super().__init__(handle_event)

    def process_object_events(self) -> None:
        """Mimics event processing."""
        count: int = 0
        LOGGER.info('subscribing to SQS events')

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
