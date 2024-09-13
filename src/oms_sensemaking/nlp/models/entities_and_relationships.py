from dataclasses import dataclass

from oms_sensemaking.nlp.models.document_as_entity import DocumentAsEntity
from oms_sensemaking.nlp.models.document_has_relation import DocumentHasRelation


@dataclass
class EntitiesAndRelationships:
    ner_entities: list
    ner_relationships: list
    document_entity: DocumentAsEntity
    document_relationships: list[DocumentHasRelation]
