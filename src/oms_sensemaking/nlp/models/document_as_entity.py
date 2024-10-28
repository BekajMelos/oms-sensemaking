"""Utilities for working with Documents as Entities."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class DocumentAsEntity:
    """Represents a document as an entity."""

    """
    Create a new instance of DocumentAsEntity.

    :param document_id: The unique identifier of the document.
    :param text: The text content of the document.
    """

    document_id: str | UUID
    value: str
    entity_type: str = "DOCUMENT"
