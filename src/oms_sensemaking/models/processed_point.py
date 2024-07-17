import os
from datetime import datetime

import pygeohash as pgh
from dotenv import load_dotenv

load_dotenv()


GEOHASH_LOW = int(os.environ["GEOHASH_LOW"])
GEOHASH_HIGH = int(os.environ["GEOHASH_HIGH"])


class ProcessedPoint:
    def __init__(self, lat: float, lon: float, timestamp: datetime, is_start: bool, is_end: bool):
        self.lat = lat
        self.lon = lon
        # TODO: should require timezone
        self.timestamp = timestamp
        self.is_start = is_start
        self.is_end = is_end
        self.geohash_low = pgh.encode(self.lat, self.lon, GEOHASH_LOW)
        self.geohash_high = pgh.encode(self.lat, self.lon, GEOHASH_HIGH)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
