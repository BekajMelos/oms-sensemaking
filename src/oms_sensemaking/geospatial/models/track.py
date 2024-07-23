"""Provides Track model."""

from typing import List
from uuid import UUID

from .processed_point import ProcessedPoint


class Track:
    """
    Represents a track.

    A track must have at least 3 points.
    """

    def __init__(self, track_node_id: UUID, points: List[ProcessedPoint]):
        self.track_node_id = track_node_id

        if len(points) < 2:
            raise ValueError("A Track must consist of at least 3 points.")
        self.points = points

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
