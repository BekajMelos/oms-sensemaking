"""Utilities for working with the Doccano entities."""

from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class DoccanoEntity:
    """Represents a Doccano entity."""

    id: int
    label: str
    start_offset: int
    end_offset: int
