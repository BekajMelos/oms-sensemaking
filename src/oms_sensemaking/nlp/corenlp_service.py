from stanza.models.common.doc import Document
from stanza.server import CoreNLPClient


class CoreNlpService:
    """
    This class is for interacting with the Stanza CoreNLP client
    TODO: expand documentation and code comments
    """

    def __init__(self, props, text):
        # TODO: Customization via API? And set custom NER and relation models
        self.PROPS = {
            "annotators": "tokenize, pos, lemma, ner, depparse, relation",
            "relation.trainUsePipelineNER": "true",
        }
        # TODO: Change to document intake
        self.text = "Chris Manning is a nice person. Chris wrote a simple sentence. He also gives oranges to people."
        self.client = CoreNLPClient(properties=self.PROPS, timeout=60000, memory="16G")

    def annotate_document(self, text: str) -> Document:
        """
        Uses the client with the props specified above to access CoreNLP and annotate a document
        """
        with self.client:
            annotated_doc = self.client.annotate(text)

        return annotated_doc
