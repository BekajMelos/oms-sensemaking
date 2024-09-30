from oms_sensemaking.nlp.corenlp_client import CoreNlpClient


class MockCoreNlpClient(CoreNlpClient):
    def __init__(self, props: dict, client: str):
        super().__init__(props, client)
        self.response = None

    def set_response(self, response):
        self.response = response

    def annotate_document(self, text: str) -> list:
        return self.response
