from stanza.server import CoreNLPClient


class CoreNlpService:
    """
    This class is for interacting with the Stanza CoreNLP client
    """

    def __init__(self, props: dict):
        if not props:
            self.props = {
                "annotators": "tokenize, pos, lemma, ner, depparse, relation",
                "relation.trainUsePipelineNER": "true",
            }
        else:
            self.props = props
        self.client = CoreNLPClient(
            properties=self.props, endpoint="http://localhost:9000", timeout=60000, memory="16G"
        )

    def annotate_document(self, text: str):
        """
        Uses the client with the props specified above to access CoreNLP and annotate a document
        """
        with self.client:
            annotated_doc = self.client.annotate(text)

        return annotated_doc
