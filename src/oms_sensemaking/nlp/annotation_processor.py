"""Annotation Processor."""

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

    def extract_info(self, data: SubmissionData, annotation) -> EntitiesAndRelationships:
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

    def find_entities(self, annotation) -> list:
        """Grab the nodes from the annotation."""
        entity_mentions = []
        # for sentence in annotation.sentence:  # Loop through the annotation
        #     for mention in sentence.mentions:  # Loop through each of the entities in the annotation
        #         entity_mentions.append(mention)  # Adds the entity to a list
        for sentence in annotation["sentences"]:  # Loop through the annotation
            for mention in sentence["entitymentions"]:  # Loop through each of the entities in the annotation
                entity_mentions.append(mention)  # Adds the entity to a list
        return entity_mentions

    def find_relationships(self, annotation) -> list:
        """Grab the relationships from the annotation."""
        # TODO: Figure out how to properly get relationships from CoreNLP docker instance
        relationships = []
        # for sentence in annotation["sentences"]:  # Loop through the annotation
        #     print("SENTENCE HERE")
        #     print(sentence)
        #     for relation in sentence.relation:  # Takes each of the relations in the document and adds to the list
        #         if relation.type != "_NR":  # Skips relations without a relation type
        #             relationships.append(relation)
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
            # print(entity["docTokenBegin"])
            document_relationship = DocumentHasRelation(
                object_id=doc_rel_obj_id,
                document_id=data.document_id,
                # ner_entity=entity.entityMentionIndex,
                ner_entity=entity["docTokenBegin"],
            )
            document_relationships.append(document_relationship)
            doc_rel_index += 1
        return EntitiesAndRelationships(
            ner_entities=entities,
            ner_relationships=relationships,
            document_entity=document_entity,
            document_relationships=document_relationships,
        )
