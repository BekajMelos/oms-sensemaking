"""Loiter Sensemakers."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from geolib import geohash
from shapely import LineString

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.models.geo import Point, Track

LOGGER = logging.getLogger(__name__)

VALID_OBSERVED_THRESHOLD_SECONDS = timedelta(seconds=SETTINGS.valid_observed_threshold_seconds)

LOITER_MIN_TIME = timedelta(seconds=SETTINGS.loiter_min_time)


class PotentialLoiter:
    def __init__(self, start_time: datetime, latest_time: datetime):
        self.start_time = start_time
        self.latest_time = latest_time

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class Loiter:
    def __init__(
        self,
        track_node_id: UUID,
        geohash_low: str,
        start_time: datetime,
        end_time: datetime,
        processed_points: list[Point],
        geometry: str,
    ):
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


class LoiterSensemaker(Sensemaker):
    """
    A sensemaker for analyzing tracks for loiters.

    Algorithm ChangeLog
    ===================

    [1.0.0]
    - Initial "loiter" algorithm implementation.

    """

    def __init__(self) -> None:
        super().__init__()
        self.version = (1, 0, 0)

    def process_data(self, data: Track) -> list[Loiter]:
        """
        Check for Loiter Events.

        Collect a list of prospective loiters. Check each of them to make sure
        they are long enough aka > LOITER_MIN_TIME. If not, it wasn't long
        enough. Ignore. If so, it's a valid loiter. Create a Loiter Object and
        add it to the list to be returned.

        :param data: The track to analyze.
        :return: List[Loiter] list of loiter events found
        """
        LOGGER.info(f"Detecting Loiters in {data.node_id}")
        confirmed_loiters: list[Loiter] = []
        prospective_loiters: dict[str, list[PotentialLoiter]] = self.find_prospective_loiters(data.points)

        # check for potential loiters that are long enough (> LOITER_MIN_TIME)
        # TODO could also check for loiters across geohashes that could be combined
        for point_geohash, potential_loiters in prospective_loiters.items():
            LOGGER.debug(f"Prospective Loiter: {point_geohash}: {potential_loiters}")
            for potential_loiter in potential_loiters:
                time_diff = abs(potential_loiter.latest_time - potential_loiter.start_time)
                if time_diff >= LOITER_MIN_TIME:
                    # if craft loitered long enough
                    loiter_points: list[Point] = []
                    for point in data.points:
                        # check for points within the loiter time window
                        if (point.detection_time >= potential_loiter.start_time
                                and point.detection_time <= potential_loiter.latest_time
                        ):
                            loiter_points.append(point)

                    geometry = LineString([point.coordinates for point in loiter_points]).wkt
                    loiter = Loiter(
                        data.node_id,
                        point_geohash,
                        loiter_points[0].detection_time,
                        loiter_points[-1].detection_time,
                        loiter_points,
                        geometry,
                    )
                    confirmed_loiters.append(loiter)

        if confirmed_loiters:
            LOGGER.info(f"Found Loiters: {confirmed_loiters}")
        return confirmed_loiters

    @staticmethod
    def find_prospective_loiters(points: list[Point]) -> dict[str, list[PotentialLoiter]]:
        """
        Find Prospective Loiters.

        Checks through the points and captures all points that are within a single geohash and
        within the VALID_OBSERVED_THRESHOLD_SECONDS to build a list of prospective loiters
        (PotentialLoiters). Keep adding points to a prospective loiter if they are within the
        geohash and the time threshold. Avoid accidentally removing valid loiters

        :param points: List of track points
        :return: Map of geohashes to a list of potential loiters within that geohash
        """
        prospective_loiters: dict[str, list[PotentialLoiter]] = {}
        # Find potential loiters - consecutive points within a geohash within a time threshold
        for point in points:

            point_geohash_low = geohash.encode(
                lat=point.coordinates[1],
                lon=point.coordinates[0],
                precision=SETTINGS.geohash_low
            )

            if point_geohash_low in prospective_loiters:
                # existing geohash
                last_loiters: list[PotentialLoiter] = prospective_loiters[point_geohash_low]
                last_loiter = last_loiters[-1]
                time_diff = abs((last_loiter.latest_time - point.detection_time))
                if time_diff <= VALID_OBSERVED_THRESHOLD_SECONDS:
                    # valid point, update the latest time for the last loiter for that geohash
                    last_loiter.latest_time = point.detection_time
                else:
                    # Points are too far apart - they've been unobserved for too long.
                    # Expire if it's not already a valid loiter
                    validity_time_diff = abs(last_loiter.latest_time - last_loiter.start_time)
                    if validity_time_diff < LOITER_MIN_TIME:
                        prospective_loiters.pop(point_geohash_low)
                    else:
                        # it must be a new loiter at the same location
                        potential_loiter = PotentialLoiter(point.detection_time, point.detection_time)
                        last_loiters.append(potential_loiter)
            else:
                # new geohash
                potential_loiter = PotentialLoiter(point.detection_time, point.detection_time)
                prospective_loiters[point_geohash_low] = [potential_loiter]

        return prospective_loiters
