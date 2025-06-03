"""Utilities for working with Doccano results."""

from dataclasses import dataclass

from oms_sensemaking.nlp.models.doccano_entity import DoccanoEntity
from oms_sensemaking.nlp.models.doccano_relation import DoccanoRelation


@dataclass
class DoccanoResult:
    """Represents a result from Doccano."""

    id: int
    text: str
    entities: set[DoccanoEntity]
    relations: set[DoccanoRelation]
    comments: list[str]
