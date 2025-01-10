"""Provides GroupByTrackIdProjection model."""

from typing import List
from uuid import UUID


class GroupByTrackIdProjection:
    """Represents a track and it's bookends."""

    def __init__(self, track_id: UUID, track_bookends: List[str]):
        """
        Create a new instance of GroupByTrackIdProject.

        :param track_id: The unique identifier for the Track
        :param track_bookends: A list containing the track bookends.
        """
        self.track_id = track_id
        self.track_bookends = track_bookends

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
