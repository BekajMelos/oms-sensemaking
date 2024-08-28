"""Sensemaker Controllers."""

import logging
from abc import ABC, abstractmethod
from threading import Event, Lock

from oms_sensemaking.core.events import ObjectEvent, ObjectEventConsumer
from oms_sensemaking.core.sensemakers import Sensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class SensemakerController(ABC):
    """Abstract base class for sensemaker controllers."""

    def __init__(self, event_consumer: ObjectEventConsumer) -> None:
        """Create a new instance of the sensemaker."""
        if event_consumer is None:
            raise TypeError("event_consumer must have a value")

        self.event_consumer: ObjectEventConsumer = event_consumer

        self.lock: Lock = Lock()
        self.stopped: Event = Event()
        self._registry: dict[str, Sensemaker] = {}

        if self.event_consumer.handle_event is None:
            # register this controller's handle_event as a callback on the event consumer
            self.event_consumer.handle_event = self.handle_event

    def register(self, name, sensemaker: Sensemaker) -> bool:
        """
        Register a sensemaker.

        :param name: A short name for the sensemaker.
        :param sensemaker: The sensemaker (i.e. an instance of ``Sensemaker``).
        :return: True if the sensemaker was registered as a result of the function, False otherwise.
        """
        if name in self._registry:
            LOGGER.warning("A sensemaker named %s is already registered, skipping")
            return False

        with self.lock:
            LOGGER.debug("Registering '%s' %s", name, sensemaker.__class__)
            self._registry[name] = sensemaker

        return True

    def unregister(self, name: str) -> bool:
        """
        Unregister a sensemaker.

        :param sensemaker: The sensemaker (i.e. an instance of ``Sensemaker``).
        """
        with self.lock:
            return self._registry.pop(name, None) or True

    def start(self) -> None:
        """Start the controller."""
        with self.lock:
            # 1. register sensemakers
            # TODO: register sensemakers here?

            # 2. setup oms event consumer
            self.event_consumer.start()

            # 3. set "running" event
            self.stopped.clear()

    def stop(self):
        """Stop the controller."""
        with self.lock:
            self.event_consumer.stop()
            self.stopped.set()

    @abstractmethod
    def handle_event(self, event: ObjectEvent) -> bool:
        """
        Handle inbound OMS event.

        This function is intended as the entrypoint for controlling the flow of
        data to the sensemakers.

        :param event: The event to process.
        :return: True if the object event was successfully processed, False otherwise.
        """
        raise NotImplementedError()


def run_controller(controller: SensemakerController) -> None:
    """
    Run the given controller.

    This function will block the current thread until the controller's
    "running" event is cleared or an exception occurs.

    :param controller: The controller to run.
    """
    try:
        LOGGER.info("Starting thread %s", controller.__class__.__name__)
        controller.start()
        controller.stopped.wait()
        LOGGER.info("Done waiting for %s", controller.__class__.__name__)
    except KeyboardInterrupt:
        LOGGER.warning("telling the controller to stop.")
        controller.stop()
    finally:
        LOGGER.info("Already stopped thread %s", controller.__class__.__name__)
