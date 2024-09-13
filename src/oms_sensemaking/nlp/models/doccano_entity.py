from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class DoccanoEntity:
    id: int
    label: str
    start_offset: int
    end_offset: int

    def __init__(self, doccano_entity: dict):
        object.__setattr__(self, "id", doccano_entity["id"])
        object.__setattr__(self, "label", doccano_entity["label"])
        object.__setattr__(self, "start_offset", doccano_entity["start_offset"])
        object.__setattr__(self, "end_offset", doccano_entity["end_offset"])
