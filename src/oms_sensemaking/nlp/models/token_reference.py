from dataclasses import dataclass


@dataclass
class TokenReference:
    token: str
    index: int
    start_offset: int
    end_offset: int
    label: str
    pos_tag: str
