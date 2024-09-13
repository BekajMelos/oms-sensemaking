from dataclasses import dataclass

from collections_extended import RangeMap

from oms_sensemaking.nlp.models.processed_relation import ProcessedRelation
from oms_sensemaking.nlp.models.token_reference import TokenReference


@dataclass
class ProcessedResult:
    doc_id: int
    doc_token_map: RangeMap
    entity_token_ref: dict[int, TokenReference]
    processed_relation_set: set[ProcessedRelation]
