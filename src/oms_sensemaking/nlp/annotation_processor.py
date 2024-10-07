"""Annotation Processor."""

import re

from oms_sensemaking.nlp.models.document_as_entity import DocumentAsEntity
from oms_sensemaking.nlp.models.document_has_relation import DocumentHasRelation
from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.models.submission_data import SubmissionData


class AnnotationProcessor:
    """
    A utility class for extracting entities and relationships from annotated documents.

    This takes the annotated document, gets entities and relationships, and returns them all.
    It also creates relationships between a document and each of the entities found within it.
    """

    def __init__(self):
        self.entity_pattern = re.compile(
            r"EntityMention \[type=(?P<type>\w+), objectId=(?P<objectId>EntityMention-\d+), hstart=(?P<hstart>\d+), "
            r"hend=(?P<hend>\d+), estart=(?P<estart>\d+), eend=(?P<eend>\d+), "
            r'headPosition=(?P<headPosition>\d+), value="(?P<value>[^"]+)", corefID=(?P<corefID>-?\d+)]'
        )
        self.relation_pattern = re.compile(
            r"RelationMention \[type=(?P<type>\w+), start=(?P<start>\d+), end=(?P<end>\d+), \{(?P<relations>[^}]+)}\n"
            r"(?P<entities>(?:\s+EntityMention \[type=\w+, objectId=EntityMention-\d+, "
            r"hstart=\d+, hend=\d+, estart=\d+, "
            r'eend=\d+, headPosition=\d+, value="[^"]+", corefID=-?\d+]\n)+)]'
        )

    def extract_info(self, data: SubmissionData, annotation: str) -> EntitiesAndRelationships:
        """
        Extract the entities and relationships the given CoreNLP annotation.

        :param data: The document data.
        :param annotation: The annotation.
        :return: An object representing the entities and relationships.
        """
        entities = self.find_entities(annotation)  # Get entities from annotation
        relationships = self.find_relationships(annotation)  # Get relations from annotation
        entities_and_relationships = self.relate_to_document(data, entities, relationships)
        return entities_and_relationships

    def find_entities(self, annotation: str) -> list:
        """Grab the nodes from the annotation."""
        entities = []

        matches = self.entity_pattern.finditer(annotation)
        for match in matches:
            entity = {
                "type": match.group("type"),
                "objectId": match.group("objectId"),
                "hstart": int(match.group("hstart")),
                "hend": int(match.group("hend")),
                "estart": int(match.group("estart")),
                "eend": int(match.group("eend")),
                "headPosition": int(match.group("headPosition")),
                "value": match.group("value"),
                "corefID": int(match.group("corefID")),
            }
            entities.append(entity)
        return entities

    def find_relationships(self, annotation: str) -> list:
        """Grab the relationships from the annotation."""
        relationships = []

        relation_matches = self.relation_pattern.finditer(annotation)
        for match in relation_matches:
            relation = {
                "type": match.group("type"),
                "start": int(match.group("start")),
                "end": int(match.group("end")),
                "relations": match.group("relations").split("; "),
                "entities": [],
            }

            # Find nested entity mentions within each relation mention
            nested_entities = self.entity_pattern.finditer(match.group("entities"))
            for entity_match in nested_entities:
                entity = {
                    "type": entity_match.group("type"),
                    "objectId": entity_match.group("objectId"),
                    "hstart": int(entity_match.group("hstart")),
                    "hend": int(entity_match.group("hend")),
                    "estart": int(entity_match.group("estart")),
                    "eend": int(entity_match.group("eend")),
                    "headPosition": int(entity_match.group("headPosition")),
                    "value": entity_match.group("value"),
                    "corefID": int(entity_match.group("corefID")),
                }
                relation["entities"].append(entity)

            relationships.append(relation)
        return relationships

    def relate_to_document(self, data: SubmissionData, entities: list, relationships: list) -> EntitiesAndRelationships:
        """
        Convert document into a node and create a relationship to each entity found in the document.

        :param data: The document data.
        :param entities: A list of entities.
        :param relationships:
        :return:
        """
        # 1. Create entity for document
        # 2. Relate each entity in the document to the document's entity

        document_relationships = []
        # Creates an entity for the document
        document_entity = DocumentAsEntity(document_id=data.document_id, text=data.text)
        doc_rel_index = 1
        for entity in entities:
            # Loop through all the entities and creates a DocumentHasRelationship for each of them
            doc_rel_obj_id = "DocumentRelation-" + str(doc_rel_index)
            document_relationship = DocumentHasRelation(
                object_id=doc_rel_obj_id,
                document_id=data.document_id,
                ner_entity=entity["objectId"],
            )
            document_relationships.append(document_relationship)
            doc_rel_index += 1
        return EntitiesAndRelationships(
            ner_entities=entities,
            ner_relationships=relationships,
            document_entity=document_entity,
            document_relationships=document_relationships,
        )
