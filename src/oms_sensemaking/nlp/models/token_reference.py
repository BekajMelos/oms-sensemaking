"""Utlities for working with tokens."""

from dataclasses import dataclass


@dataclass
class TokenReference:
    """Represents a reference to a token."""

    token: str
    index: int
    start_offset: int
    end_offset: int
    label: str
    pos_tag: str
