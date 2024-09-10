# TODO: Add attributes as we learn what is needed to submit with oms_sdk as a node
class DocumentAsEntity:
    def __init__(self, document_id: int, text: str):
        self.document_id = document_id
        self.text = text
        self.entity_type = "DOCUMENT"

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
