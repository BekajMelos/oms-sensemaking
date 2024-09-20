"""Utilities for working with Documents as Entities."""


class DocumentAsEntity:
    """Represents a document as an entity."""

    def __init__(self, document_id: str, text: str):
        """
        Create a new instance of DocumentAsEntity.

        :param document_id: The unique identifier of the document.
        :param text: The text content of the document.
        """
        self.document_id = document_id
        self.text = text
        self.entityType = "DOCUMENT"  # key format entityType matches the same field as CoreNLP Entities

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
