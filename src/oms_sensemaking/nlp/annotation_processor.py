class AnnotationProcessor:
    """"""

    # TODO: make a node to represent the document, and a relationship for each node found back to the document

    def extract_info(self, data, annotation) -> dict[str, list]:
        """Takes the result of the CoreNLP annotation and extracts entities and relationships between them"""
        entities = self.find_entities(annotation)
        relationships = self.find_relationships(annotation)
        entities_and_relationships = self.relate_to_document(data, entities, relationships)
        return entities_and_relationships

    def find_entities(self, annotation) -> list:
        """Grabs the nodes from the annotation"""
        entity_mentions = []
        for sentence in annotation.sentence:
            for mention in sentence.mentions:
                entity_mentions.append(mention)
        return entity_mentions

    def find_relationships(self, annotation) -> list:
        """Grabs the relationships from the annotation"""
        relationships = []
        for sentence in annotation.sentence:
            for relation in sentence.relation:
                if relation.type != "_NR":
                    relationships.append(relation)
        return relationships

    def relate_to_document(self, data, entities, relationships):
        """Turns the document itself into a node, and creates a relationship to each entity found in the document"""
        # 1. Create entity for document
        # 2. Relate each entity in the document to the document's entity
        document_entity = {
            "entityMentionIndex": data["document_id"],
            "entityType": "DOCUMENT",
            # "entityMentionText": data["text"]
        }
        for entity in entities:
            # TODO: Standardize this addition with a relationship data model
            # TODO: Do we want the document relationships to point to the entities or vice versa?
            document_relationship = {
                "objectID": "DocumentRelation",
                "type": "Document_Contains",
                "entities": [document_entity, entity],
            }
            relationships.append(document_relationship)
        entities.append(document_entity)
        return {"entities": entities, "relationships": relationships}
