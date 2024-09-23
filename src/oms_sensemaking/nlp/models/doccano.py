"""Classes to support working with Doccano."""
from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class DoccanoEntity:
    """Represents an entity in Doccano."""

    id: int
    label: str
    start_offset: int
    end_offset: int


@dataclass(frozen=True, eq=True)
class DoccanoRelation:
    """Represents a relation in Doccano."""

    id: int
    from_id: int
    to_id: int
    type: str


@dataclass
class DoccanoResult:
    """Represents a result from Doccano."""

    id: int
    text: str
    entities: set[DoccanoEntity]
    relations: set[DoccanoRelation]
    comments: list[str]
