"""Utilities for working with CoreNLP."""

import requests

from oms_sensemaking.config import SETTINGS


class CoreNlpService:
    """Utility class for interacting with the Stanza CoreNLP client."""

    def __init__(self, props: dict, host: str = SETTINGS.corenlp_dockerhost):
        """
        Create a new instance of CoreNlpService.

        :param props:
        """
        if not props:
            self.props = {
                "annotators": "tokenize, pos, lemma, ner, depparse, relation, openie",
            }
        else:
            self.props = props
        self.corenlp_host = host
        self.url = f"http://{self.corenlp_host}/?properties={self.props}"

    def annotate_document(self, text: str):
        """
        Annotate the given document text.

        Uses the configure properties with CoreNLP and annotate a document.

        :param text: The document text to annotate.
        :return: The annotated document.
        """
        result = requests.post(self.url, data=text.encode("utf-8"))
        annotated_doc = result.json()
        return annotated_doc
