from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class ProcessedRelation:
    from_token_index: int
    to_token_index: int
    relation_type: str
