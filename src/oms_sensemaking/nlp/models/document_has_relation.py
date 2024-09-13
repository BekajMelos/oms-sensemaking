from typing import Any
from uuid import UUID

from attr import dataclass


@dataclass
class DocumentHasRelation:
    object_id: str
    document_id: str | UUID
    ner_entity: Any
    type: str = "Document_Contains_Entity"
