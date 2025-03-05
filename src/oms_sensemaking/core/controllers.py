"""Sensemaker Controllers."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event, Lock, Thread

from oms_sensemaking.core.events import AuditLogEvent, AuditLogEventConsumer
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class SensemakerController:
    """Base class for sensemaker controllers."""

    def __init__(self, event_consumer: AuditLogEventConsumer, *args, **kwargs) -> None:
        """
        Create a new instance of the SensemakerController.

        The controller uses an ``Event`` to indicate if it is running. Other
        threads can wait on ``Sensemaker.stopped`` until it is set. For example::

            class SomeController(SensemakerController):
                def handle_event(
                    self, event: AuditLogEvent
                ) -> bool:
                    print(
                        f"Received {event.eventType} for {event.objectType}(id={event.objectId})"
                    )
                    return True


            controller: SensemakerController = SomeController(
                DummyAuditLogEventConsumer
            )
            controller.start()
            controller.stopped.wait()  # block until controller has been stopped

        This function will create a new instance of the controller in the
        "stopped" state. To start the controller, call
        ``SensemakerContorller.start()``, which will ensure that appropriate
        conditions have been met to run the controller and will also clear the
        ``SensemakerController.stopped`` Event.
        """
        if event_consumer is None:
            raise TypeError("event_consumer must have a value")

        self._registry: dict[str, Sensemaker] = {}
        self.event_consumer: AuditLogEventConsumer = event_consumer
        self.lock: Lock = Lock()
        self.stopped: Event = Event()
        self.oms_crud_tool: OmsCrudTool = OmsCrudTool()

        self.stopped.set()  # start off in the "stopped" state

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

        :param name: The name of the sensemaker to unregister.
        :return: True if the Sensemaker was unregistered and False otherwise.
        """
        with self.lock:
            return self._registry.pop(name, None) is not None

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
            LOGGER.debug("Stopping controller.")
            self.event_consumer.stop()
            self.stopped.set()

    @property
    def is_running(self) -> bool:
        """Indicate if the controller is running."""
        return not self.stopped.is_set()

    def handle_event(self, event: AuditLogEvent) -> bool:
        """
        Handle inbound OMS event.

        This function is intended as the entrypoint for controlling the flow of
        data to the sensemakers.

        :param event: The event to process.
        """

        LOGGER.debug(f"Received AuditLogEvent(objectId={event.objectId})")

        # extract info from OMS via API calls
        oms_obj = self.oms_crud_tool.rehydrate_oms_obj(event.objectId, event.objectType)
        if not oms_obj:
            return True

        try:
            with ThreadPoolExecutor() as executor:
                futures = []
                for sensemaker in self._registry.values():
                    future = executor.submit(sensemaker.execute, oms_obj)
                    futures.append(future)

                # make sure errors are caught
                for future in as_completed(futures):
                    _ = future.result()

                executor.shutdown(wait=True)
        except Exception:
            LOGGER.exception(f"Error encountered while processing object {event.objectId}")

        return True


def run_controller(controller: SensemakerController) -> None:
    """
    Run the given controller.

    This function will block the current thread until the controller's
    "stopped" event is set or an exception occurs.

    :param controller: The controller to run.
    """
    try:
        LOGGER.info("Starting thread for %s", controller.__class__.__name__)
        controller.start()
        controller.stopped.wait()
        LOGGER.info("Done waiting for %s", controller.__class__.__name__)
    finally:
        if controller.is_running:
            LOGGER.warning("A controller was left running. Stopping it now.")
            controller.stop()


def start_controller_and_wait(controller: SensemakerController) -> None:
    """
    Start a controller in a thread and waits for it to finish.

    This function blocks the current thread. If a ``KeyboardInterrupt`` is
    raised, the controller will be stopped.
    """
    controller_thread: Thread = Thread(target=run_controller, args=(controller,))

    try:
        controller_thread.start()
        controller_thread.join()
    except KeyboardInterrupt:
        LOGGER.debug("Preparing to exit after KeyboardInterrupt")
        controller.stop()

        if controller_thread.is_alive():
            LOGGER.warning("Thread status: %s", controller_thread.is_alive())
            controller_thread.join()
