import os
from datetime import datetime

import shapely
from geolib import geohash

GEOHASH_LOW = int(os.environ["GEOHASH_LOW"])
GEOHASH_HIGH = int(os.environ["GEOHASH_HIGH"])


class ProcessedPoint:
    def __init__(self, geometry: shapely.Point, timestamp: datetime, is_start: bool, is_end: bool):
        self.geometry = geometry
        # TODO: should require timezone
        self.timestamp = timestamp
        self.is_start = is_start
        self.is_end = is_end
        self.geohash_low = geohash.encode(self.geometry.y, self.geometry.x, GEOHASH_LOW)
        self.geohash_high = geohash.encode(self.geometry.y, self.geometry.x, GEOHASH_HIGH)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
