"""Utilities for working with documents as relations."""


class DocumentHasRelation:
    """Represents a document as a relation."""

    def __init__(self, object_id: str, document_id: str, ner_entity):
        """
        Create a new instance of DocumentHasRelation.

        :param object_id: The unique identifier of the object.
        :param document_id: The unique identifier of the document.
        :param ner_entity: The NER entity.
        """
        self.object_id = object_id
        self.document_id = document_id  # This is the link back to the document, not including text itself
        self.ner_entity = ner_entity
        self.type = "Document_Contains_Entity"

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
