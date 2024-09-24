"""Utilities for working with processed relation data."""
from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class ProcessedRelation:
    """Represents a processed relation."""

    from_token_index: int
    to_token_index: int
    relation_type: str
