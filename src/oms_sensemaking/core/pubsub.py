"""Provides support a simple event pub/sub API."""

import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import Any, Callable, Optional

LOGGER: logging.Logger = logging.getLogger(__name__)
SHUTDOWN_EVENT: str = "shutdown"


@dataclass
class PubSubEvent:
    """Represents a simple event."""

    event_type: str
    data: Optional[Any] = None


class PubSub:
    """Simple pub/sub API."""

    def __init__(self) -> None:
        """
        Create a new instance of PubSub.

        This method initializes the event queue and starts a thread for
        dispatching events to subscribers.

        Subclasses should invoke this method if they override ``__init__.py``.
        For example::

            class Foo(PubSub):
                def __init__(self):
                    super().__init__()

                def do_something(self):
                    self.publish("some-event", {})

        """
        self.__event_queue: Queue[PubSubEvent] = Queue()
        self.__subscribers: dict[str, list[Callable]] = defaultdict(list)
        self.__dispatcher = Thread(target=self.__dispatch)
        self.__dispatcher.start()
        LOGGER.debug(f"Initialized event pub/sub for {self.__class__}")

    def subscribe(self, event_type: str, fn: Callable) -> None:
        """
        Subscribe the given callable to an specific event type.

        :param event_type: The event type to subscribe to.
        :param fn: The subscriber. This callable should accept a single argument.
        """
        self.__subscribers[event_type].append(fn)

    def unsubscribe(self, event_type: str, fn: Callable) -> bool:
        """
        Unsubscribes the given callable from an event type.

        :param event_type: The event type to unsubscribe from.
        :param fn: The subscriber.
        :return: A bool indicating if the subscriber was removed.
        """
        if event_type in self.__subscribers:
            try:
                self.__subscribers[event_type].remove(fn)
                return True
            except ValueError:
                LOGGER.warning("subscriber does not exist for event type %s", event_type)

        return False

    def publish(self, event_type: str, data: Optional[Any] = None) -> None:
        """
        Publish an event to the message queue.

        :param event_type: The event type to publish.
        :param data: The data payload to include in the published event.
        """
        self.__event_queue.put(PubSubEvent(event_type, data))

    def __dispatch(self) -> None:
        """Dispatch events to subscribers."""
        with ThreadPoolExecutor() as executor:
            while (event := self.__event_queue.get()) and event.event_type != SHUTDOWN_EVENT:
                LOGGER.debug("handling event: %s", event.event_type)

                for subscriber in self.__subscribers.get(event.event_type, []):
                    if event.data is None:
                        executor.submit(subscriber)
                    else:
                        executor.submit(subscriber, event.data)

                self.__event_queue.task_done()

            self.__event_queue.task_done()  # acknowledge the shutdown event
            executor.shutdown()  # shutdown executor after event loop exists

    def stop(self) -> None:
        """Stop the event dispatcher."""
        self.publish(SHUTDOWN_EVENT)
        self.__dispatcher.join()
        self.__event_queue.join()

    @property
    def is_running(self) -> bool:
        """Indicates if the pub/sub dispatcher is currently running."""
        return self.__dispatcher is not None and self.__dispatcher.is_alive()
