"""Utilities for working with CoreNLP."""

import logging

import httpx
import xmltodict

from oms_sensemaking.config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)


class CoreNlpService:
    """Utility class for interacting with the Stanza CoreNLP client."""

    def __init__(self, props: dict, host: str = SETTINGS.corenlp_dockerhost):
        """
        Create a new instance of CoreNlpService.

        :param props:
        """
        if not props:
            self.props = {"annotators": "tokenize, pos, lemma, ner, depparse, relation", "outputFormat": "xml"}
        else:
            self.props = props
        self.corenlp_host = host
        self.url = f"http://{self.corenlp_host}/?properties={self.props}"

    def annotate_document(self, text: str) -> list:
        """
        Annotate the given document text.

        Uses the configure properties with CoreNLP and annotate a document.

        :param text: The document text to annotate.
        :return: The annotated document.
        """
        data = {"text": text}
        result = httpx.post(self.url, data=data, timeout=None)
        formatted_annotations = xmltodict.parse(result.text)["root"]["document"]["sentences"]["sentence"]
        return formatted_annotations
