from dataclasses import dataclass
from uuid import UUID


@dataclass
class DocumentAsEntity:
    document_id: str | UUID
    text: str
    entity_type: str = "DOCUMENT"
