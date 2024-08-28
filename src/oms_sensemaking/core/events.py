"""Common event consumers."""

import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from threading import Event, Thread
from time import sleep
from typing import Optional
from uuid import UUID, uuid4

import boto3
from botocore.client import BaseClient

from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)


class ObjectType(Enum):
    """Enumeration of OMS object types."""

    # alternatively -> from oms_sdk.generated.generated_graphql_client.enums import ObjectType
    SOURCE = 0
    ATTRIBUTE = 1
    ORIGINATOR = 2
    PROVIDER = 3
    ACM = 4
    GEO = 5
    RELATIONSHIP = 6
    NODE = 7
    NODE_LINK = 8
    RESOLVED_OBJECT_CONFIG = 9
    NODE_IDENTIFIER = 10
    COMMENT = 11
    ALERT = 12
    OBJECT_COLLECTION = 13
    USER_PREFERENCES = 14


class EventType(Enum):
    """Enumeration of OMS event types."""

    # alternatively -> from oms_sdk.generated.generated_graphql_client.enums import Action?
    CREATE = 0
    UPDATE = 1
    DELETE = 2


class ObjectEvent:
    """Represents an object event from OMS."""

    def __init__(self, user_dn: str, object_id: UUID, object_type: ObjectType, event_type: EventType):
        """
        Create a new instance of ObjectEvent.

        :param user_dn: The distinguished name (DN) of the user that triggered the event.
        :param object_id: The unique if of the object in OMS.
        :param object_type: The type of object that the event was triggered on.
        :param event_type: They type of event (e.g. create, update, or delete).
        """
        self.user_dn: str = user_dn
        self.object_id: UUID = object_id
        self.object_type: ObjectType = object_type
        self.event_type: EventType = event_type

    def to_json(self) -> str:
        """Return a JSON representation of the event."""
        return json.dumps(self.__dict__)


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
        self.__data_consumer: Optional[Thread] = None
        self.__stop: Event = Event()

    @property
    def is_stopped(self) -> bool:
        """Indicates if the consumer is running (False) or stopped (True)."""
        return self.__stop.is_set()

    def start(self) -> None:
        """
        Start consuming events.

        This method should be overridden by subclasses to begin producing
        """
        if self.__data_consumer is None:
            self.__data_consumer = Thread(target=self.process_object_events)
            self.__stop.clear()
            self.__data_consumer.start()

    def stop(self) -> None:
        """Stop consuming events."""
        self.__stop.set()
        if self.__data_consumer is not None:
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

    def process_object_events(self):
        """Mimics event processing."""
        count: int = 0
        LOGGER.info('subscribing to SQS events')

        while not self.is_stopped:
            sleep(5)
            event: ObjectEvent = ObjectEvent(SETTINGS.user_dn, uuid4(), ObjectType.ATTRIBUTE, EventType.CREATE)
            self.handle_event(event)
            count = count + 1
