"""Similar Tracks Sensemakers."""

import logging
import uuid
from collections import defaultdict
from queue import PriorityQueue
from typing import Any

from geoalchemy2.types import Geography
from geolib import geohash
from sqlalchemy import and_, desc, func, join, select
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.sql import cast

from oms_sensemaking.clients.instances import db_engine, db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.geospatial.models.group_by_track_id_projection import GroupByTrackIdProjection
from oms_sensemaking.models.geo import Point, Track, get_track, track_points_table

LOGGER = logging.getLogger(__name__)

TRACK_CREATED_EVENT: str = "track_created"

ST_TRANSFORM_MAX_DECIMAL_DIGITS: int = 9  # maxdecimaldigits parameter in Postgis ST_TRANSFORM
ST_TRANSFORM_OPTION_GEOJSON_SHORT_CRS: int = 2  # option 2: GeoJSON Short CRS (e.g EPSG:4326)


class ComparisonResult:
    """Represents the results of a track comparison."""

    def __init__(self, track_uuid: uuid.UUID, similarity_score: float):
        """
        Create a new instance of ComparisonResult.

        :param track_uuid: The unique identifier for the Track.
        :param similarity_score: The similarity score.
        """
        self.track_uuid = track_uuid
        self.similarity_score = similarity_score

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class TopSimilar:
    """Represents the top similar tracks."""

    def __init__(self):
        """Create a new instance of TopSimilar."""
        self.top_similarities = PriorityQueue(maxsize=SETTINGS.n_tracks)

    def __str__(self):
        return str((self.top_similarities.maxsize, list(self.top_similarities.queue)))

    def __repr__(self):
        return self.__str__()

    def add_comparison_result(self, comparison_result: ComparisonResult) -> None:
        """
        Add a comparison result the to top similarities queue.

        :param comparison_result: The results to enqueue.
        """
        self.top_similarities.put((comparison_result.similarity_score, comparison_result.track_uuid))


class SimilarTracksSensemaker(Sensemaker):
    """
    A sensemaker for detecting similar tracks.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial "similar tracks" algorithm implementation.

    """

    def __init__(self) -> None:
        """Create a new instance of SimilarTracksSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.config = {"n_tracks": SETTINGS.n_tracks}

    def process_data(self, data: Track, config: dict) -> TopSimilar:
        """
        Primary method to obtain N-most similar track objects to the track provided.

        :param data: Track object to detect cotravels on
        :return: list[PotentialMatch] list of TopSimilar tracks
        """
        LOGGER.debug(f"Looking for similar tracks to {data.node_id}")
        # Update the config with specific geo settings
        self.config.update(config)

        similar_results: TopSimilar = TopSimilar()

        first: Point = data.points[0]
        last: Point = data.points[-1]
        ref_track_geohash_set: set[str] = self.get_buffered_geohash_set(data.points)

        # query for tracks that start and end within the QUERY_DISTANCE
        LOGGER.debug(f"Reference track has first {first} and last {last} points")
        similar_track_groups: list[GroupByTrackIdProjection] = self.query_for_similar_tracks(
            first.coordinates, last.coordinates, self.config["within_meters"]
        )

        seen_groups = []
        for similar_track_group in similar_track_groups:
            # Remove any representations of the track of interest itself
            if similar_track_group.track_uuid == data.track_uuid:
                continue

            # filter to one entry per trackId
            if similar_track_group.track_uuid in seen_groups:
                continue
            seen_groups.append(similar_track_group.track_uuid)

            similar_track: Track = self.get_track_from_group_projection(similar_track_group)

            # obtain buffered hashSet for prospective similar track
            eval_track_geohash_set = self.get_buffered_geohash_set(similar_track.points)

            # calculate similarity by Jaccard measure of bufferedHashSets
            comparison_result: ComparisonResult = self.determine_jaccard_similarity(
                ref_track_geohash_set, eval_track_geohash_set, similar_track_group.track_uuid
            )

            similar_results.add_comparison_result(comparison_result)

        return similar_results

    @staticmethod
    def determine_jaccard_similarity(
        ref_track_geohash_set: set[str], eval_track_geohash_set: set[str], track_uuid: uuid.UUID
    ) -> ComparisonResult:
        """
        Determine the Jaccard similairty between two track geohash sets.

        :param ref_track_geohash_set: The references track geohash set.
        :param eval_track_geohash_set:
        :param track_uuid:
        :return: A comparison result with similarity score.
        """
        # intersection of two sets
        intersection = len(ref_track_geohash_set.intersection(eval_track_geohash_set))
        # Unions of two sets
        union = len(ref_track_geohash_set.union(eval_track_geohash_set))
        score = intersection / union
        LOGGER.debug(f"Overall similarity for {eval_track_geohash_set}, {score}")
        return ComparisonResult(track_uuid, score)

    @classmethod
    def get_track_from_group_projection(cls, group_projection: GroupByTrackIdProjection) -> Track:
        """
        Obtain object for processing from groupBy query projection results.

        :param group_projection: GroupByTrackIdProjection
        :return: Track object
        """
        with db_session() as db:
            return get_track(db, group_projection.track_uuid)

    def get_buffered_geohash_set(self, points: list[Point]) -> set[str]:
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
        buffered_geohash_set: set[str] = set()

        for point in points:
            # reduce precision of the geohash by one to generate set for comparison to expand range for 'similar' tracks
            point_geohash = point.geohash[: self.config["similar_tracks_geohash"]]
            base_geohash = point_geohash[0:-1]
            buffered_geohash_set.add(base_geohash)

            neighbors = geohash.neighbours(base_geohash)
            for neighbor in neighbors:
                buffered_geohash_set.add(neighbor)

        return buffered_geohash_set

    @staticmethod
    def query_for_similar_tracks(
        first: list[float], last: list[float], query_distance: float
    ) -> list[GroupByTrackIdProjection]:
        """
        Primary method to obtain the other tracks that have either the same start or end point provided.

        The distance is the range from the point to include in the results.

        E.g. Query for the end "bookends". Note the DESC column
        SELECT points.track_id, array_agg(
            ST_AsGeoJSON(ST_Transform(points.location, 4326), 9, 2) ORDER BY points.detection_time) AS bookend
        FROM points
        JOIN (
            SELECT anon_2.track_id AS track_id, anon_2.observation_id AS observation_id,
            anon_2.detection_time AS detection_time
            FROM (
                SELECT points.track_id AS track_id, points.node_version AS node_version,
                points.observation_id AS observation_id, points.observation_version AS observation_version,
                points.location AS location, points.altitude AS altitude, points.detection_time AS detection_time,
                points.acm AS acm, points.created_at AS created_at, points.updated_at AS updated_at,
                ROW_NUMBER() OVER (PARTITION BY points.track_id ORDER BY points.detection_time DESC) AS row_number
                    FROM points
            ) AS anon_2
            WHERE anon_2.row_number = 1
        ) AS anon_1 ON points.track_id = anon_1.track_id AND points.observation_id = anon_1.observation_id
        WHERE ST_DWithin(
            CAST(points.location AS geography(GEOMETRY,-1)),
            CAST(ST_Transform(ST_GeomFromGeoJSON('{''type'': ''Point'', ''coordinates'': [2.183748, 41.356069]}'), 4326)
                 AS geography(GEOMETRY,-1)), 3000.0)
        GROUP BY points.track_id

        :param first: Point of the first point in the track
        :return: List of GroupByTrackIdProjections
        """

        def generate_query(order_col, geojson):
            # sub-subquery to label the rows in the Point table after ordering by order_col
            sub_subquery = (
                select(
                    Point.observation_id,
                    Point.detection_time,
                    Track.track_uuid,
                    func.ROW_NUMBER().over(partition_by=Track.track_uuid, order_by=order_col).label("row_number"),
                )
                .select_from(
                    join(
                        Point,
                        track_points_table,
                        track_points_table.c.point_id == Point.point_id,
                    ).join(Track, track_points_table.c.track_id == Track.track_id)
                )
                .subquery()
            )

            # use the row number to find the first value. This subquery gives us either the set of starting track
            # points or the set of ending track points depending on the order_col order (desc or not)
            subquery = (
                select(sub_subquery.c.track_uuid, sub_subquery.c.observation_id, sub_subquery.c.detection_time)
                .where(sub_subquery.c.row_number == 1)
                .subquery()
            )

            # This query will join the original Point table with the sorted start or end table in order to look at the
            # entire set of starting (or ending) points. Then look for points that are within the query_distance.
            # The points are casted to the Geography type to allow the query_distance to be in meters.
            # Overall, this query will find tracks that have starting points that are within the query_distance of the
            # given track. Then with the end query, it will find tracks that end within the query distance of the given
            # track.
            query = (
                select(
                    Track.track_uuid,
                    func.array_agg(  # the array_agg will return the point as a geojson
                        aggregate_order_by(
                            func.ST_asGeoJSON(
                                func.ST_Transform(Point.location, SETTINGS.srid),
                                ST_TRANSFORM_MAX_DECIMAL_DIGITS,  # maxdecimaldigits
                                ST_TRANSFORM_OPTION_GEOJSON_SHORT_CRS,  # option 2: GeoJSON Short CRS (e.g EPSG:4326)
                            ),
                            Point.detection_time,
                        )
                    ).label("bookend"),
                )
                .select_from(
                    join(
                        Point,
                        track_points_table,
                        track_points_table.c.point_id == Point.point_id,
                    )
                    .join(Track, track_points_table.c.track_id == Track.track_id)
                    .join(
                        subquery,
                        and_(
                            subquery.c.track_uuid == Track.track_uuid,
                            subquery.c.observation_id == Point.observation_id,
                        ),
                    )
                )
                .where(
                    func.ST_DWithin(
                        cast(Point.location, Geography(srid=-1)),
                        cast(
                            func.ST_Transform(func.ST_GeomFromGeoJSON(str(geojson)), SETTINGS.srid), Geography(srid=-1)
                        ),
                        query_distance,
                    )
                )
                .group_by(Track.track_uuid)
            )

            return query

        with db_session() as db:
            start_geojson = {"type": "Point", "coordinates": first}

            start_query = generate_query(Point.detection_time, start_geojson)
            LOGGER.debug(f"Start bookend query {start_query.compile(db_engine, compile_kwargs={'literal_binds':True})}")
            res = db.execute(start_query)
            start_groups = res.all()

            end_geojson = {"type": "Point", "coordinates": last}
            end_query = generate_query(desc(Point.detection_time), end_geojson)
            LOGGER.debug(f"End bookend query {end_query.compile(db_engine, compile_kwargs={'literal_binds':True})}")
            res = db.execute(end_query)
            end_groups = res.all()

            # combine the start bookends with the end bookends by track_uuid
            groups = defaultdict(list)
            for track_uuid, bookend in start_groups + end_groups:
                groups[track_uuid].append(bookend)

        return [GroupByTrackIdProjection(track_uuid, bookends) for track_uuid, bookends in groups.items()]

    def save_findings(self, similar_track: Any) -> None:
        """Save findings to the database."""
        # Will Implement in a future Ticket
        pass
