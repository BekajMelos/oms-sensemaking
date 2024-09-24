"""Utilities for working with CoreNLP."""

import requests

# from stanza.server import CoreNLPClient


class CoreNlpService:
    """Utility class for interacting with the Stanza CoreNLP client."""

    def __init__(self, props: dict):
        """
        Create a new instance of CoreNlpService.

        :param props:
        """
        if not props:
            self.props = {
                "annotators": "tokenize, pos, lemma, ner, depparse, relation",
            }
        else:
            self.props = props
        # self.client = CoreNLPClient(
        #     properties=self.props, endpoint="http://localhost:9000", timeout=60000, memory="16G"
        # )
        # TODO: Use configs to set the url
        self.url = f"http://localhost:9000/?properties={self.props}"
        # self.url = f'http://host.docker.internal:9000/?properties={self.props}'

    def annotate_document(self, text: str):
        """
        Annotate the given document text.

        Uses the configure properties with CoreNLP and annotate a document.

        :param text: The document text to annotate.
        :return: The annotated document.
        """
        # with self.client:
        #     annotated_doc = self.client.annotate(text)
        annotated_doc = requests.post(self.url, data=text).json()
        # print(annotated_doc)
        return annotated_doc
