"""Cotravel Sensemakers."""
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from geolib import geohash
from shapely import LineString, MultiLineString
from sqlalchemy import func, select
from sqlalchemy.orm import with_expression

from oms_sensemaking.clients import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.models.geo import Point, Track, get_track

LOGGER = logging.getLogger(__name__)

VALID_OBSERVED_THRESHOLD_SECONDS = timedelta(seconds=SETTINGS.valid_observed_threshold_seconds)

MIN_COTRAVEL_DURATION_SECONDS = timedelta(seconds=SETTINGS.min_cotravel_duration_seconds)

MIN_LAG_LEAD_DURATION_SECONDS = timedelta(seconds=SETTINGS.min_lag_lead_duration_seconds)

MAX_LAG_LEAD_DURATION_SECONDS = timedelta(seconds=SETTINGS.max_lag_lead_duration_seconds)


class PotentialMatch:
    """Represents a potential co-travel match."""

    def __init__(
        self,
        track1: UUID,
        track2: UUID,
        start_time1: datetime,
        start_time2: datetime,
        last_time1: datetime,
        last_time2: datetime,
        true_cotravel: bool,
    ):
        """Create a new instance of PotentialMatch."""
        self.track1 = track1
        self.track2 = track2
        self.start_time1 = start_time1
        self.start_time2 = start_time2
        self.last_time1 = last_time1
        self.last_time2 = last_time2
        self.true_cotravel = true_cotravel

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def tentative_add(self, time1: datetime, time2: datetime) -> bool:
        """
        Check if a new colocation can fit into a cotravel that is being created and adds it if so.

        :param time1:
        :param time2:
        :return: boolean indicating if the PotentialMatch was updated
        """
        if (
            abs(self.last_time1 - time1) <= VALID_OBSERVED_THRESHOLD_SECONDS
            and abs(self.last_time2 - time2) <= VALID_OBSERVED_THRESHOLD_SECONDS
        ):
            self.last_time1 = time1
            self.last_time2 = time2
            self.true_cotravel = self.true_cotravel and (abs(time1 - time2) <= MIN_LAG_LEAD_DURATION_SECONDS)
            return True
        return False

    def check_valid(self) -> bool:
        """Check whether a PotentialMatch has met the duration requirements."""
        return (
            self.last_time1 - self.start_time1 >= MIN_COTRAVEL_DURATION_SECONDS
            and self.last_time2 - self.start_time2 >= MIN_COTRAVEL_DURATION_SECONDS
        )

    def calculate_and_set_geometry(self, track1: Track, track2: Track) -> None:
       """
       Set the geometry for the cotravel.

       :param track1: First track
       :param track2: Second track
       """
       start_time = min(self.start_time1, self.start_time2)
       end_time = max(self.last_time1, self.last_time2)
       ls1 = LineString(CotravelSensemaker.extract_coordinate_track(track1, start_time, end_time))
       ls2 = LineString(CotravelSensemaker.extract_coordinate_track(track2, start_time, end_time))
       self.geometry = MultiLineString([ls1, ls2])


class Colocation:
    """For CotravelService use, a Colocation stores the data for two tracks' intersection."""

    def __init__(self, track1: UUID, track2: UUID, point: Point, db_point: Point):
        """Create a new instance of Colocation."""
        self.track1 = track1
        self.track2 = track2
        self.point = point
        self.db_point = db_point

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class CotravelSensemaker(Sensemaker):
    """
    A sensemaker for analyzing tracks for cotravelers.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial "co-travel" algorithm implementation.

    """

    def __init__(self) -> None:
        """Create a new instance of CotravelSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)

    def process_data(self, data: Track) -> list[PotentialMatch]:
        """Run the *cotravel* algorithm on the given track."""
        LOGGER.info(f"Detecting Cotravels in {data.node_id}")

        cotravels: list[PotentialMatch] = []
        matches: list[Colocation] = []

        # find matching points (colocations) for each point in the track
        for point in data.points:
            time = point.detection_time

            point_geohash_low = geohash.encode(
                lat=point.coordinates[1],
                lon=point.coordinates[0],
                precision=SETTINGS.geohash_low
            )

            db_points: List[Point] = self.get_points(
                point_geohash_low,
                data.node_id,
                (time - MAX_LAG_LEAD_DURATION_SECONDS),
                (time + MAX_LAG_LEAD_DURATION_SECONDS),
                time,
            )

            # Create colocations from track entries
            match_points: List[Colocation] = [
                Colocation(data.node_id, db_point.node_id, point, db_point) for db_point in db_points
            ]

            if matches:
                matches.extend(match_points)
            else:
                matches = match_points

        if not matches:
            return []

        # group points by track2
        groups = defaultdict(list)
        for entry in matches:
            groups[entry.track2].append(entry)

        # determine cotravels on each list
        for _, colocations in groups.items():
            sorted_entries = sorted(colocations, key=lambda colocation: colocation.db_point.detection_time)
            cotravels.extend(self.determine_cotravels(sorted_entries))

        for idx, cotravel in enumerate(cotravels):
            with db_session() as db:
                track2: Track = get_track(db, cotravel.track2)

                cotravel.calculate_and_set_geometry(data, track2)
                LOGGER.info(f"Found Cotravel {idx+1}/{len(cotravels)}: {cotravel}")
                LOGGER.debug("Cotravel geometry: " + cotravel.geometry.wkt)

        return cotravels

    @classmethod
    def get_points(
        cls, geohash_low: str, track_node_id: uuid.UUID, min_time: datetime, max_time: datetime, target_time: datetime
    ) -> List[Point]:
        """
        Find points in other tracks that match the geohash of the given point within the time intervals.

        This query:

        SELECT DISTINCT ST_GeoHash(points.location) AS "ST_GeoHash_1", points.node_id, points.node_version,
            points.attribute_id, points.attribute_version, ST_AsEWKB(points.location) AS location,
            points.altitude, points.detection_time, points.acm, points.created_at, points.updated_at
        FROM points
        WHERE ST_GeoHash(points.location) LIKE :ST_GeoHash_2
            AND points.node_id != :node_id_1
            AND points.detection_time > :detection_time_1
            AND points.detection_time < :detection_time_2
        ORDER BY points.node_id, abs(EXTRACT(epoch FROM points.detection_time - :detection_time_3))

        :param geohash_low: Geohash to match in the DB
        :param track_node_id: Track node to ignore
        :param min_time: Min allowed time to lag by
        :param max_time: Max allowed time to lag by
        :param target_time: time to sort the response by
        :return: List of cotravels

        """
        with db_session() as db:
            query = db.execute(
                select(
                    Point
                ).filter(
                    Point.location.ST_Geohash().like(f"{geohash_low}%")
                ).where(
                    Point.node_id != track_node_id,
                    Point.detection_time > min_time,
                    Point.detection_time < max_time
                ).order_by(
                    Point.node_id, func.abs(func.extract('epoch', Point.detection_time - target_time))
                ).options(
                    with_expression(Point.geohash, func.ST_GeoHash(Point.location))
                ).distinct(Point.node_id)
            )

            return list(query.scalars().all())

    @staticmethod
    def determine_cotravels(colocations: list[Colocation]) -> list[PotentialMatch]:
        """
        Given the list of colocations, that they meet the time requirements.

        :param colocations: List of colocations
        :return: List of cotravels
        """
        completed: list[PotentialMatch] = []
        to_add_to: Optional[PotentialMatch] = None

        for colocation in colocations:
            if to_add_to:
                # if we have a potential match already, keep checking
                if (
                    not to_add_to.tentative_add(colocation.point.detection_time, colocation.db_point.detection_time)
                    and to_add_to.check_valid()
                ):
                    # the next colocation point doesn't meet the observation threshold but we still
                    # have a valid cotravel. Add the cotravel to the list and start over with a new
                    # potential match

                    completed.append(to_add_to)
                    true_cotravel = (
                        abs(colocation.point.detection_time - colocation.db_point.detection_time)
                        <= MIN_LAG_LEAD_DURATION_SECONDS
                    )
                    to_add_to = PotentialMatch(
                        colocation.track1,
                        colocation.track2,
                        colocation.point.detection_time,
                        colocation.db_point.detection_time,
                        colocation.point.detection_time,
                        colocation.db_point.detection_time,
                        true_cotravel,
                    )
            else:
                # if no potential match already exists, create and start checking
                true_cotravel = (
                    abs(colocation.point.detection_time - colocation.db_point.detection_time)
                    <= MIN_LAG_LEAD_DURATION_SECONDS
                )

                to_add_to = PotentialMatch(
                    colocation.track1,
                    colocation.track2,
                    colocation.point.detection_time,
                    colocation.db_point.detection_time,
                    colocation.point.detection_time,
                    colocation.db_point.detection_time,
                    true_cotravel,
                )

        # check the last point for a valid cotravel
        if to_add_to and to_add_to.check_valid():
            completed.append(to_add_to)

        return completed

    # TODO maybe move to utility
    @staticmethod
    def extract_coordinate_track(track: Track, start_time: datetime, end_time: datetime) -> List[List[float]]:
        """
        Return points within provided time bounds.

        :param track: Track to extract points from
        :param start_time: earliest point timestamp
        :param end_time: latest point timestamp
        :return: List of valid points
        """
        points = []
        for point in track.points:
            if point.detection_time >= start_time and point.detection_time <= end_time:
                points.append(point.coordinates)
        return points
