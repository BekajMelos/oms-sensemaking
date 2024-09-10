# TODO: Add attributes as we learn what is needed to submit with oms_sdk as a relation
class DocumentHasRelation:
    def __init__(self, object_id: str, document_id: int, ner_entity):
        self.object_id = object_id
        self.document_id = document_id  # This is the link back to the document, not including text itself
        self.ner_entity = ner_entity
        self.type = "Document_Contains_Entity"

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
