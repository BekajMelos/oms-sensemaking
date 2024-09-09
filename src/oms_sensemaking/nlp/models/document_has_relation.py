from oms_sensemaking.nlp.models.document_as_entity import DocumentAsEntity


# TODO: Add unique identifier for each relation
# TODO: Add attributes as we learn what is needed to submit with oms_sdk as a relation
class DocumentHasRelation:
    def __init__(self, document_id: int, document_entity: DocumentAsEntity, ner_entity):
        self.object_id = document_id
        self.document_entity = document_entity
        self.ner_entity = ner_entity
        self.type = "Document_Contains_Entity"

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
