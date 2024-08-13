"""Provides GroupByTrackNodeIdProjection model."""

from typing import List
from uuid import UUID


class GroupByTrackNodeIdProjection:
    def __init__(self, track_node_id: UUID, track_bookends: List[str]):
        self.track_node_id = track_node_id
        self.track_bookends = track_bookends

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
