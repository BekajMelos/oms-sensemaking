"""Utilities for working with CoreNLP."""

import logging

import httpx
import xmltodict

LOGGER: logging.Logger = logging.getLogger(__name__)


class CoreNlpClient:
    """Utility class for interacting with the CoreNLP Docker container server."""

    def __init__(self, props: dict, hostname: str):
        """
        Create a new instance of CoreNlpService.

        :param props:
        """
        if not props:
            self._props = {"annotators": "tokenize, pos, lemma, ner, depparse, relation", "outputFormat": "text"}
        else:
            self._props = props
        LOGGER.warning(f"CoreNLP Client 'outputFormat' is set to {self._props["outputFormat"]}")
        LOGGER.warning(f"CoreNLP Client 'properties' is set to {self._props}")

        self.hostname = hostname
        self.url = f"http://{self.hostname}/?properties={self._props}"

    def annotate_document_str(self, text: str) -> str:
        """
        Annotate the given document text.

        Uses the configure properties with CoreNLP and annotate a document.

        :param text: The document text to annotate.
        :return: The annotated document.
        """

        # Handling empty text submission case
        if not text:
            LOGGER.warning("Empty text submission to the CoreNLP Client")
            return ""

        # Formatting text for submission and sending it to the CoreNLP container
        data = {"text": text}
        result = httpx.post(self.url, data=data, content=text, timeout=None)
        return result.text

    def annotate_document_xml(self, text: str) -> list:
        """
        Annotate the given document text.

        Uses the configure properties with CoreNLP and annotate a document.

        :param text: The document text to annotate.
        :return: The annotated document.
        """

        # Handling empty text submission case
        if not text:
            LOGGER.warning("Empty text submission to the CoreNLP Client")
            return []

        # Formatting text for submission and sending it to the CoreNLP container
        data = {"text": text}
        result = httpx.post(self.url, data=data, content=text, timeout=None)

        # Parsing the xml response to get it as a dictionary for easy indexing later
        formatted_annotations = xmltodict.parse(result.text)["root"]["document"]["sentences"]["sentence"]

        # If there is only one sentence it by default returns a dict instead of a list of dicts, this corrects that
        return [formatted_annotations] if isinstance(formatted_annotations, dict) else formatted_annotations
