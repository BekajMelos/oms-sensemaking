from dataclasses import dataclass

from oms_sensemaking.nlp.models.doccano_entity import DoccanoEntity
from oms_sensemaking.nlp.models.doccano_relation import DoccanoRelation


@dataclass
class DoccanoResult:
    id: int
    text: str
    entities: set[DoccanoEntity]
    relations: set[DoccanoRelation]
    comments: list[str]
