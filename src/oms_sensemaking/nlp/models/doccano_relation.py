"""Utilities for working with Doccano relations."""

from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class DoccanoRelation:
    """Represents a relation in Doccano."""

    id: int
    from_id: int
    to_id: int
    type: str
