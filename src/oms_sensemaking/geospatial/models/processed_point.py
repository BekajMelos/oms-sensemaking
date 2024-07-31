"""Provides ProcessedPoint model."""
from datetime import datetime

import shapely
from geolib import geohash

from oms_sensemaking.config import SETTINGS


class ProcessedPoint:
    """Represents a processed point."""

    def __init__(self, geometry: shapely.Point, timestamp: datetime, is_start: bool, is_end: bool):
        self.geometry = geometry
        # TODO: should require timezone
        self.timestamp = timestamp
        self.is_start = is_start
        self.is_end = is_end
        self.geohash_low = geohash.encode(self.geometry.y, self.geometry.x, SETTINGS.geohash_low)
        self.geohash_high = geohash.encode(self.geometry.y, self.geometry.x, SETTINGS.geohash_high)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
