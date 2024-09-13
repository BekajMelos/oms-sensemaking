"""NLP sensemaker controller."""

import logging
from typing import Optional

from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import EVENT_HANDLER, ObjectEvent, ObjectEventConsumer
from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker

# from oms_sensemaking.nlp.models.submission_data import SubmissionData

LOGGER: logging.Logger = logging.getLogger(__name__)


# class NlpApiReceiver(ObjectEventConsumer):
#     """An ObjectEventConsumer to interact with OMS API calls"""
#     def __init__(self):
#         super().__init__()
#
#     def process_object_events(self) -> None:
#         self.handle_event()
#         pass


class TextFileReader(ObjectEventConsumer):
    """For reading from a text file if running NLP SM via CLI"""

    def __init__(
        self, filename: str, default_acm: dict, default_user_dn: str, handle_event: Optional[EVENT_HANDLER] = None
    ):
        """
        Create a new instance of TextFileReader.

        :param filename: The .txt file to process.
        :param default_acm: The ACM to apply to all records in the CSV file.
        :param default_user_dn: The user DN to apply to all records in the CSV file.
        :param handle_event: A callback that will receive the processed tracks.
        """
        super().__init__(handle_event)
        self.filename: str = filename
        self.default_acm: dict = default_acm
        self.default_user_dn: str = default_user_dn

    def process_object_events(self) -> None:
        text_file = self.filename
        with open(text_file, "r") as file:
            text = file.read()
        print(text)
        return super().process_object_events()


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

        if isinstance(self.event_consumer, TextFileReader):
            nlp_sensemaker = NlpSensemaker()
            nlp_sensemaker.process_data()
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


#
# if __name__ == "__main__":
#     controller = NlpSensemakerController(NlpApiReceiver())
#     run_nlp_controller(nlp_controller=controller)
