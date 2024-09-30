"""Utilities for working with CoreNLP."""

import logging

import httpx
import xmltodict

LOGGER: logging.Logger = logging.getLogger(__name__)


class CoreNlpClient:
    """Utility class for interacting with the CoreNLP Docker container server."""

    def __init__(self, props: dict, client: str):
        """
        Create a new instance of CoreNlpService.

        :param props:
        """
        if not props:
            self.props = {"annotators": "tokenize, pos, lemma, ner, depparse, relation", "outputFormat": "xml"}
        else:
            self.props = props
        self.corenlp_client = client
        self.url = f"http://{self.corenlp_client}/?properties={self.props}"

    def annotate_document(self, text: str) -> list:
        """
        Annotate the given document text.

        Uses the configure properties with CoreNLP and annotate a document.

        :param text: The document text to annotate.
        :return: The annotated document.
        """
        # Handling empty text submission case
        if not text:
            return []

        # Formatting text for submission and sending it to the CoreNLP container
        data = {"text": text}
        result = httpx.post(self.url, data=data, content=text, timeout=None)

        # Parsing the xml response to get it as a dictionary for easy indexing later
        formatted_annotations = xmltodict.parse(result.text)["root"]["document"]["sentences"]["sentence"]

        # If there is only one sentence it by default returns a dict instead of a list of dicts, so this corrects that
        return [formatted_annotations] if isinstance(formatted_annotations, dict) else formatted_annotations


class MockCoreNlpClient(CoreNlpClient):
    def __init__(self, props: dict, host: str):
        super().__init__(props, host)
        self.response: list = []

    def set_response(self, response: list):
        self.response = response

    def annotate_document(self, text: str) -> list:
        return self.response
