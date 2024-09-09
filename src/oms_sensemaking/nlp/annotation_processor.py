from oms_sensemaking.nlp.models.document_as_entity import DocumentAsEntity
from oms_sensemaking.nlp.models.document_has_relation import DocumentHasRelation
from oms_sensemaking.nlp.models.entities_and_relationships import EntitiesAndRelationships
from oms_sensemaking.nlp.models.submission_data import SubmissionData


class AnnotationProcessor:
    """
    This takes the annotated document, gets entities and relationships, and returns them all.
    It also creates relationships between a document and each of the entities found within it.
    """

    def extract_info(self, data: SubmissionData, annotation) -> EntitiesAndRelationships:
        """Takes the result of the CoreNLP annotation and extracts entities and relationships between them"""
        entities = self.find_entities(annotation)  # Get entities from annotation
        relationships = self.find_relationships(annotation)  # Get relations from annotation
        entities_and_relationships = self.relate_to_document(data, entities, relationships)
        return entities_and_relationships

    def find_entities(self, annotation) -> list:
        """Grabs the nodes from the annotation"""
        entity_mentions = []
        for sentence in annotation.sentence:  # Loop through the annotation
            for mention in sentence.mentions:  # Loop through each of the entities in the annotation
                entity_mentions.append(mention)  # Adds the entity to a list
        return entity_mentions

    def find_relationships(self, annotation) -> list:
        """Grabs the relationships from the annotation"""
        relationships = []
        for sentence in annotation.sentence:  # Loop through the annotation
            for relation in sentence.relation:  # Takes each of the relations in the document and adds to the list
                if relation.type != "_NR":  # Skips relations without a relation type
                    relationships.append(relation)
        return relationships

    def relate_to_document(self, data: SubmissionData, entities: list, relationships: list) -> EntitiesAndRelationships:
        """Turns the document itself into a node, and creates a relationship to each entity found in the document"""
        # 1. Create entity for document
        # 2. Relate each entity in the document to the document's entity

        # TODO: Make document relationships/entities the same data type as normal relationships/entities? Maybe no need
        document_relationships = []
        # TODO: Might just be able to use DataSubmission type, depends on how things go in next ticket
        # Creates an entity for the document
        document_entity = DocumentAsEntity(document_id=data.document_id, text=data.text)
        for entity in entities:
            # Loop through all the entities and creates a DocumentHasRelationship for each of them
            document_relationship = DocumentHasRelation(
                document_id=data.document_id, document_entity=document_entity, ner_entity=entity
            )
            document_relationships.append(document_relationship)
        return EntitiesAndRelationships(
            ner_entities=entities,
            ner_relationships=relationships,
            document_entity=document_entity,
            document_relationships=document_relationships,
        )
