"""NLP sensemaker controller."""

import logging

from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import ObjectEvent, ObjectEventConsumer

LOGGER: logging.Logger = logging.getLogger(__name__)


class NlpApiReceiver(ObjectEventConsumer):
    def __init__(self):
        super().__init__()


class NlpSensemakerController(SensemakerController):
    """
    Natural Language Processing sensemaker controller.

    This class manages a collection of NLP sensemakers.
    """

    def __init__(self, event_consumer: ObjectEventConsumer) -> None:
        """Create a new instance of NlpSensemakerController."""
        super().__init__(event_consumer)

    def handle_event(self, event: ObjectEvent) -> bool:
        """
        Handle inbound OMS event.

        :param event: The event to process.
        :return: True if the object event was successfully processed, False otherwise.
        """
        LOGGER.warning("NLP %s", event.objectId)
        return True


def run_nlp_controller(nlp_controller: NlpSensemakerController):
    print("Hello there")
    try:
        LOGGER.info("Starting thread fo %s", nlp_controller.__class__.__name__)
        nlp_controller.start()
        nlp_controller.stopped.wait()
        LOGGER.info("Done waiting for %s", nlp_controller.__class__.__name__)
    finally:
        if nlp_controller.is_running:
            LOGGER.warning("A controller was left running. Stopping it now.")
            nlp_controller.stop()


if __name__ == "__main__":
    controller = NlpSensemakerController(ObjectEventConsumer())
    run_nlp_controller(nlp_controller=controller)
