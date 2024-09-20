"""Provides GroupByTrackNodeIdProjection model."""

from typing import List
from uuid import UUID


class GroupByTrackNodeIdProjection:
    """Represents a track node and it's bookends."""

    def __init__(self, track_node_id: UUID, track_bookends: List[str]):
        """
        Create a new instance of GroupByTrackNodeIdProject.

        :param track_node_id: The unique identifier for the Node associated with a track.
        :param track_bookends: A list containing the track bookends.
        """
        self.track_node_id = track_node_id
        self.track_bookends = track_bookends

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
