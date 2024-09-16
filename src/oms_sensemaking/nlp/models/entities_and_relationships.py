from oms_sensemaking.nlp.models.document_as_entity import DocumentAsEntity
from oms_sensemaking.nlp.models.document_has_relation import DocumentHasRelation


class EntitiesAndRelationships:
    def __init__(
        self,
        ner_entities: list,
        ner_relationships: list,
        document_entity: DocumentAsEntity,
        document_relationships: list[DocumentHasRelation],
    ):
        self.ner_entities = ner_entities
        self.ner_relationships = ner_relationships
        self.document_entity = document_entity
        self.document_relationships = document_relationships

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
