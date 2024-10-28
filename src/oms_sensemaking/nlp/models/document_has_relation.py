"""Utilities for working with documents as relations."""

from dataclasses import dataclass


@dataclass
class DocumentHasRelation:
    """Represents a document as a relation."""

    """
    Create a new instance of DocumentHasRelation.

    :param doc_obj_id: The  identifier of the document object.
    :param document_uuid: The unique identifier of the document.
    :param entity_obj_id: The NER entity object id.
    :param entity_uuid: The unique id of the entity.
    """

    doc_obj_id: str
    document_uuid: str
    entity_obj_id: str
    entity_uuid: str
    type: str = "Document_Contains_Entity"
