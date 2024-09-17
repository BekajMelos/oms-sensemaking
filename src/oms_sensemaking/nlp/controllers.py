"""NLP sensemaker controller."""

import logging
from typing import Optional
from uuid import uuid4

from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.enums import Action

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import EVENT_HANDLER, ObjectEvent, ObjectEventConsumer, ObjectType
from oms_sensemaking.nlp.models.submission_data import SubmissionData
from oms_sensemaking.nlp.sensemakers.nlp_sensemaker import NlpSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class NlpApiReceiver(ObjectEventConsumer):
    """An ObjectEventConsumer to interact with OMS API calls"""

    def __init__(
        self, text: str, default_acm: dict, default_user_dn: str, handle_event: Optional[EVENT_HANDLER] = None
    ):
        """
        Create a new instance of NlpApiReceiver.

        :param text: The string of text to process.
        :param default_acm: The ACM to apply to all records in the CSV file.
        :param default_user_dn: The user DN to apply to all records in the CSV file.
        :param handle_event: A callback that will receive the processed tracks.
        """
        super().__init__(handle_event)
        self.default_acm: dict = default_acm
        self.default_user_dn: str = default_user_dn
        self.text = text  # This could also be a file, depending on how it is submitted by the API
        # TODO: Add other attributes? Title, primary and secondary topics, though only if needed

    def process_object_events(self) -> None:
        """
        Calls the handle_event function of the NlpSensemakerController, passing it an ObjectEvent with the
        user_dn, a UUID for the text/document, a SOURCE ObjectType, and a CREATE Action. Returns bool based on
        result of calling handle_event.
        """
        success: bool = self.handle_event(
            ObjectEvent(
                self.default_user_dn,
                uuid4(),
                ObjectType.SOURCE,
                Action.CREATE,
            )
        )

        if success:
            LOGGER.info("Successfully analyzed and processed text for NER.")
        else:
            LOGGER.info("Text was unsuccessfully processed for NER.")


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
        success: bool = self.handle_event(
            ObjectEvent(
                self.default_user_dn,
                uuid4(),
                ObjectType.SOURCE,
                Action.CREATE,
            )
        )

        if success:
            LOGGER.info("Successfully analyzed and processed text file for NER.")
        else:
            LOGGER.info("Text file was unsuccessfully processed for NER.")


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

        nlp_sensemaker = NlpSensemaker()

        # If we are running this from the command line and reading in a file specified by the filepath
        if isinstance(self.event_consumer, TextFileReader):
            # Gathering the file contents
            text_file = self.event_consumer.filename
            with open(text_file, "r") as file:
                text = file.read()

            # Running the NLP pipeline to get entities and relationships
            ents_and_rels = nlp_sensemaker.process_data(SubmissionData(document_id=event.objectId, text=text))
            print(ents_and_rels)
            # TODO: use the (future) EntityDecorator to submit objects to oms using event data

        # If we are using the API to call the NlpSensemaker (through the command line for now)
        elif isinstance(self.event_consumer, NlpApiReceiver):
            # Gathering the text
            text = self.event_consumer.text

            # Running the NLP pipeline to get entities and relationships
            ents_and_rels = nlp_sensemaker.process_data(SubmissionData(document_id=event.objectId, text=text))
            print(ents_and_rels)
            # TODO: use the (future) EntityDecorator to submit objects to oms using event data

        # Telling the controller to stop once the entities and relations have been returned
        self.stopped.set()

        LOGGER.warning("NLP %s", event.objectId)
        return True


def run_nlp_controller(nlp_controller: NlpSensemakerController):
    try:
        LOGGER.info("Starting thread fo %s", nlp_controller.__class__.__name__)
        nlp_controller.start()
        nlp_controller.stopped.wait()
        LOGGER.info("Done waiting for %s", nlp_controller.__class__.__name__)
    finally:
        if nlp_controller.is_running:
            LOGGER.warning("A controller was left running. Stopping it now.")
            nlp_controller.stop()


# TODO: Delete main once the API is up and running. Do the following in the API call
if __name__ == "__main__":
    text = (
        "EU rejects German call to boycott British lamb. Peter Blackburn BRUSSELS 1996-08-22 "
        "The European Commission said on Thursday it disagreed with German advice to consumers "
        "to shun British lamb until scientists determine whether mad cow disease can be transmitted"
        " to sheep. Germany's representative to the European Union's veterinary committee Werner Zwingmann"
        " said on Wednesday consumers should buy sheepmeat from countries other than Britain until the "
        "scientific advice was clearer."
    )
    controller = NlpSensemakerController(NlpApiReceiver(text, DEFAULT_ACM, SETTINGS.user_dn))
    run_nlp_controller(nlp_controller=controller)
