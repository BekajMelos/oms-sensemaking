"""Provides TrackEntry model."""
from datetime import datetime
from uuid import UUID

from shapely import Point


class TrackEntry:
    """Represents a track entry."""

    def __init__(
        self,
        id: UUID,
        track_node_id: UUID,
        source_id: UUID,
        geometry: Point,
        geohash_low: str,
        geohash_high: str,
        timehash_low: str,
        timehash_high: str,
        is_start: bool,
        is_end: bool,
        start_time: datetime,
    ):
        self.id = id
        self.track_node_id = track_node_id
        self.source_id = source_id
        self.geometry = geometry
        self.geohash_low = geohash_low
        self.geohash_high = geohash_high
        self.timehash_low = timehash_low
        self.timehash_high = timehash_high
        self.is_start = is_start
        self.is_end = is_end
        self.start_time = start_time

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
