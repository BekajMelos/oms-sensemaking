import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List
from uuid import UUID

from dotenv import load_dotenv
from shapely import LineString

from oms_sensemaking.models.track import Track
from oms_sensemaking.models.processed_point import ProcessedPoint


load_dotenv()

LOGGER = logging.getLogger(__name__)


# TODO could use pydantic for these settings or a python settings file
VALID_OBSERVED_THRESHOLD_SECONDS = timedelta(seconds=int(
    os.environ["VALID_OBSERVED_THRESHOLD_SECONDS"]))
LOITER_MIN_TIME = timedelta(seconds=int(os.environ["LOITER_MIN_TIME"]))


class PotentialLoiter:

    def __init__(self, start_time: datetime, latest_time: datetime):
        self.start_time = start_time
        self.latest_time = latest_time

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class Loiter:

    def __init__(self, track_node_id: UUID, geohash_low: str, start_time: datetime,
                 end_time: datetime, processed_points: List[ProcessedPoint], geometry: str):
        self.track_node_id = track_node_id
        self.geohash_low = geohash_low
        self.start_time = start_time
        self.end_time = end_time
        self.processed_points = processed_points
        self.geometry = geometry

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class LoiterService:
    """Service for detecting loiter events"""

    @classmethod
    def detect_loiters(cls, track: Track) -> List[Loiter]:
        """
        Check for Loiter Events. Collect a list of prospective loiters. Check each of them to make 
        sure they are long enough aka > LOITER_MIN_TIME.
        If not, it wasn't long enough. Ignore.
	    If so, it's a valid loiter.
        Create a Loiter Object and add it to the list to be returned
	    :param Track object:
	    :return: List[Loiter] list of loiter events found
        """

        LOGGER.info(f"Detecting Loiters in {track}")
        confirmed_loiters: List[Loiter] = []
        prospective_loiters: Dict[str, List[PotentialLoiter]] = cls.find_prospective_loiters(track.points)

        # check for potential lotiers that are long enough (> LOITER_MIN_TIME)
        # TODO could also check for loiters across geohashes that could be combined
        for geohash, potential_loiters in prospective_loiters.items():
            LOGGER.debug(f"Prospective Loiter: {geohash}: {potential_loiters}")
            for potential_loiter in potential_loiters:
                time_diff = abs(potential_loiter.latest_time - potential_loiter.start_time)
                if time_diff >= LOITER_MIN_TIME:
                    # if craft loitered long enough
                    loiter_points: List[ProcessedPoint] = []
                    for point in track.points:
                        # check for points within the loiter time window
                        if (point.timestamp >= potential_loiter.start_time and 
                            point.timestamp <= potential_loiter.latest_time):
                            loiter_points.append(point)

                    geometry = LineString([(point.lon, point.lat) for point in loiter_points]).wkt
                    loiter = Loiter(track.track_node_id, geohash, loiter_points[0].timestamp,
                                    loiter_points[-1].timestamp, loiter_points, geometry)
                    LOGGER.debug(f"Found Loiter: {loiter}")
                    confirmed_loiters.append(loiter)

        return confirmed_loiters     
    

    @staticmethod
    def find_prospective_loiters(points: List[ProcessedPoint]) -> Dict[str, List[PotentialLoiter]]:
        """
        Find Prospective Loiters
        Checks through the points and captures all points that are within a single geohash and 
        within the VALID_OBSERVED_THRESHOLD_SECONDS to build a list of prospective loiters 
	    (PotentialLoiters). Keep adding points to a prospective loiter if they are within the 
        geohash and the time threshold. Avoid accidentally removing valid loiters

        :param points: List of track points
	    :return: Map of geohashes to a list of potential loiters within that geohash
        """

        prospective_loiters = {}
        # Find potential loiters - consecutive points within a geohash within a time threshold
        for point in points:
            if point.geohash_low in prospective_loiters.keys():
                # existing geohash
                last_loiters: List[PotentialLoiter] = prospective_loiters.get(point.geohash_low)
                last_loiter = last_loiters[-1]
                time_diff = abs((last_loiter.latest_time - point.timestamp))
                if time_diff <= VALID_OBSERVED_THRESHOLD_SECONDS:
                    # valid point, update the latest time for the last loiter for that geohash
                    last_loiter.latest_time = point.timestamp
                else:
                    # Points are too far apart - they've been unobserved for too long.
                    # Expire if it's not already a valid loiter
                    validity_time_diff = abs(last_loiter.latest_time - last_loiter.start_time)
                    if validity_time_diff < LOITER_MIN_TIME:
                        prospective_loiters.pop(point.geohash_low)
                    else:
                        # it must be a new loiter at the same location
                        potential_loiter = PotentialLoiter(point.timestamp, point.timestamp)
                        last_loiters.append(potential_loiter)
            else:
                # new geohash
                potential_loiter = PotentialLoiter(point.timestamp, point.timestamp)
                prospective_loiters[point.geohash_low] = [potential_loiter]

        return prospective_loiters
