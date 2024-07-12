from typing import List
from uuid import UUID

from .processed_point import ProcessedPoint

class Track:

    def __init__(self, track_node_id: UUID, points: List[ProcessedPoint]):
        self.track_node_id = track_node_id
        self.points = points