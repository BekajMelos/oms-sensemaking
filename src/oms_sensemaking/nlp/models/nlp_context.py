"""Utilities for working with CoreNLP context."""
from dataclasses import dataclass


@dataclass
class NlpContext:
    """Represents a context in CoreNLP."""

    user_dn: str
