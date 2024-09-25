"""Utilities for working with documents as relations."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class DocumentHasRelation:
    """Represents a document as a relation."""

    """
    Create a new instance of DocumentHasRelation.

    :param object_id: The unique identifier of the object.
    :param document_id: The unique identifier of the document.
    :param ner_entity: The NER entity.
    """

    object_id: str
    document_id: str | UUID
    ner_entity: Any
    type: str = "Document_Contains_Entity"
