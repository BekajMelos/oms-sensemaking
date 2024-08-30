"""NLP sensemaker controller."""

import logging

from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import ObjectEvent, ObjectEventConsumer

LOGGER: logging.Logger = logging.getLogger(__name__)


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
