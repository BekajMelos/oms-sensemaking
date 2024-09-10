"""Similar Tracks Sensemakers."""
import logging
import uuid
from datetime import datetime, timedelta
from queue import PriorityQueue
from typing import List, Set

import shapely
from geoalchemy2.elements import WKTElement
from geolib import geohash
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.geospatial.models.group_by_track_node_id_projection import GroupByTrackNodeIdProjection
from oms_sensemaking.models.geo import SRID, Point, Track

CACHE_ENTRY_EXPIRE_SEC = timedelta(seconds=SETTINGS.cache_entry_expire_sec)

LOGGER = logging.getLogger(__name__)

TRACK_CREATED_EVENT: str = "track_created"

# FAKE DB
NODE_UUID1 = uuid.uuid4()

NODE_UUID2 = uuid.uuid4()

SOURCE_UUID = uuid.uuid4()






LOGGER = logging.getLogger(__name__)


class ComparisonResult:
    def __init__(self, track_node_id: uuid.UUID, similarity_score: float):
        self.track_node_id = track_node_id
        self.similarity_score = similarity_score

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class TopSimilar:
    def __init__(self):
        self.top_similarities = PriorityQueue(maxsize=SETTINGS.n_tracks)

    def __str__(self):
        return str((self.top_similarities.maxsize, list(self.top_similarities.queue)))

    def __repr__(self):
        return self.__str__()

    def add_comparison_result(self, comparison_result: ComparisonResult) -> None:
        self.top_similarities.put((comparison_result.similarity_score, comparison_result.track_node_id))


class SimilarTracksSensemaker(Sensemaker):
    """A sensemaker for detecting similar tracks."""

    def __init__(self) -> None:
        super().__init__()

    def process_data(self, data: Track) -> TopSimilar:
        """
        Primary method to obtain N-most similar track objects to the track provided.

        :param track: Track object to detect cotravels on
        :return: List[PotentialMatch] list of TopSimilar tracks
        """
        LOGGER.info(f"Looking for similar tracks to {data.node_id}")

        similar_results: TopSimilar = TopSimilar()

        first: Point = data.points[0]
        last: Point = data.points[-1]
        ref_track_geohash_set: Set[str] = self.get_buffered_geohash_set(data.points)

        # query for tracks that start and end within the QUERY_DISTANCE
        LOGGER.debug(f"Reference track has first {first} and last {last} points")
        similar_track_groups: List[GroupByTrackNodeIdProjection] = self.query_for_similar_tracks(
            first.coordinates, last.coordinates, SETTINGS.within_meters
        )

        seen_groups = []
        for similar_track_group in similar_track_groups:
            # Remove any representations of the track of interest itself
            if similar_track_group.track_node_id == data.node_id:
                continue

            #
            if similar_track_group.track_node_id in seen_groups:
                continue
            seen_groups.append(similar_track_group.track_node_id)

            similar_track: Track = self.get_track_from_group_projection(similar_track_group)

            # obtain buffered hashSet for prospective similar track
            eval_track_geohash_set = self.get_buffered_geohash_set(similar_track.points)

            # calculate similarity by Jaccard measure of bufferedHashSets
            comparison_result: ComparisonResult = self.determine_jaccard_similarity(
                ref_track_geohash_set, eval_track_geohash_set, similar_track.node_id
            )

            similar_results.add_comparison_result(comparison_result)

        return similar_results

    @staticmethod
    def determine_jaccard_similarity(
        ref_track_geohash_set: Set[str], eval_track_geohash_set: Set[str], eval_track_node_id: uuid.UUID
    ) -> ComparisonResult:
        # intersection of two sets
        intersection = len(ref_track_geohash_set.intersection(eval_track_geohash_set))
        # Unions of two sets
        union = len(ref_track_geohash_set.union(eval_track_geohash_set))
        score = intersection / union
        LOGGER.debug(f"Overall similarity for {eval_track_geohash_set}, {score}")
        return ComparisonResult(eval_track_node_id, score)

    @classmethod
    def get_track_from_group_projection(cls, group_projection: GroupByTrackNodeIdProjection) -> Track:
        """
        Obtain object for processing from groupBy query projection results.

        :param group_projection: GroupByTrackNodeIdProjection
        :return: Track object
        """
        return cls.get_track(group_projection.track_node_id)

    @staticmethod
    def get_buffered_geohash_set(points: List[Point]) -> Set[str]:
        """
        Obtain a bufferedGeoHash set from the points provided.

        For each point, a reference geohash with one less character is added to
        the empty set. The neighbors of the reference hash are added to the set.

            Note: The lower precision geohash was used initially for test and
            evaluation purposes. This method should be tested with a more
            robust set of representative data in order to determine the most
            appropriate hash levels.

        :param points: list of track points
        :return: Set of geohashes
        """
        buffered_geohash_set: Set[str] = set()

        for point in points:
            # reduce precision of the geohash by one to generate set for comparison to expand range for 'similar' tracks
            point_geohash_low = geohash.encode(
                lat=point.coordinates[1],
                lon=point.coordinates[0],
                precision=SETTINGS.geohash_low
            )
            base_geohash = point_geohash_low[0:-1]
            buffered_geohash_set.add(base_geohash)

            neighbors = geohash.neighbours(base_geohash)
            for neighbor in neighbors:
                buffered_geohash_set.add(neighbor)

        return buffered_geohash_set

    @staticmethod
    def query_for_similar_tracks(
            first: List[float],
            last: List[float],
            query_distance: float) -> List[GroupByTrackNodeIdProjection]:
        """
        Primary method to obtain the other tracks that have either the same start or end point provided.

        The distance is the range from the point to include in the results.
        The query requires that a track has at least 2 points.

        SELECT track_node_id, ARRAY_AGG(ST_AsGeoJSON(ST_Transform(geometry, 4326), 9, 2)
            ORDER BY start_time) AS track_bookends
            FROM tracks
            WHERE (is_start = true AND ST_DWithin(geometry, ST_Transform(ST_GeomFromGeoJSON(:geoJsonStart)::geometry,
                4326), :distance)) OR (is_end = true AND ST_DWithin(geometry,
                ST_Transform(ST_GeomFromGeoJSON(:geoJsonEnd)::geometry, 4326), :distance))
            GROUP BY track_node_id
            HAVING COUNT(geometry) >= 2

        :param first: Point of the first point in the track.
        :param last: Point of the last point in the track.
        :param query_distance: Threshold .
        :return: List of GroupByTrackNodeIdProjections
        """
        return [GroupByTrackNodeIdProjection(NODE_UUID1, [])]

    @staticmethod
    def get_track(track_node_id: uuid.UUID) -> Track:
        """
        Get Track by UUID.

        :param track_node_id: node id of the Track to retrieve
        :return: Track object
        """
        return Track(
            [
                Point(
                    DEFAULT_ACM,
                    WKTElement(shapely.Point((-0.165222, 51.482286)).wkt, srid=SRID),
                    altitude=None,
                    detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
                    node_id=track_node_id,
                    node_version=1,
                    attribute_id=uuid.uuid4(),
                    attribute_version=1
                ),
                Point(
                    DEFAULT_ACM,
                    WKTElement(shapely.Point((-0.210562, 51.466103)).wkt, srid=SRID),
                    altitude=None,
                    detection_time=datetime.fromisoformat("2024-03-20T12:10:00-04:00"),
                    node_id=track_node_id,
                    node_version=1,
                    attribute_id=uuid.uuid4(),
                    attribute_version=1
                ),
                Point(
                    DEFAULT_ACM,
                    WKTElement(shapely.Point((-0.229466, 51.487613)).wkt, srid=SRID),
                    altitude=None,
                    detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"),
                    node_id=track_node_id,
                    node_version=1,
                    attribute_id=uuid.uuid4(),
                    attribute_version=1
                ),
            ]
            ,
            track_node_id
        )
