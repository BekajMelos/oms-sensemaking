from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class DoccanoRelation:
    id: int
    from_id: int
    to_id: int
    type: str

    def __init__(self, doccano_relation: dict):
        object.__setattr__(self, "id", doccano_relation["id"])
        object.__setattr__(self, "from_id", doccano_relation["from_id"])
        object.__setattr__(self, "to_id", doccano_relation["to_id"])
        object.__setattr__(self, "type", doccano_relation["type"])
