from collections_extended import RangeMap

from oms_sensemaking.nlp.models.processed_relation import ProcessedRelation
from oms_sensemaking.nlp.models.token_reference import TokenReference


class ProcessedResult:
    def __init__(
        self,
        doc_id: int,
        doc_token_map: RangeMap = None,
        entity_token_ref_map: dict[int, list[TokenReference]] = None,
        processed_relation_set: set[ProcessedRelation] = None,
    ):
        self.doc_id = doc_id
        self.doc_token_map = doc_token_map
        self.entity_token_ref = entity_token_ref_map
        self.processed_relation_set = processed_relation_set

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
