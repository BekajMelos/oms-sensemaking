import logging
import uuid
from datetime import datetime
from typing import List

import shapely

from oms_sensemaking.geospatial.models.group_by_track_node_id_projection import GroupByTrackNodeIdProjection
from oms_sensemaking.geospatial.models.processed_point import ProcessedPoint
from oms_sensemaking.geospatial.models.track import Track
from oms_sensemaking.geospatial.models.track_entry import TrackEntry

LOGGER = logging.getLogger(__name__)


# FAKE DB
NODE_UUID1 = uuid.uuid4()
NODE_UUID2 = uuid.uuid4()
SOURCE_UUID = uuid.uuid4()
TRACK_ENTRIES_DB = {
    "gcpuu": [
        TrackEntry(
            uuid.uuid4(),
            NODE_UUID1,
            SOURCE_UUID,
            shapely.Point((-0.165222, 51.482286)),
            "gcpuu",
            "gcpugab",
            "abcdef",
            "abcdefgh",
            True,
            False,
            datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
        )
    ],
    "gcpug": [
        TrackEntry(
            uuid.uuid4(),
            NODE_UUID1,
            SOURCE_UUID,
            shapely.Point((-0.210562, 51.466103)),
            "gcpug",
            "gcpugab",
            "abcdef",
            "abcdefgh",
            False,
            False,
            datetime.fromisoformat("2024-03-20T12:10:00-04:00"),
        )
    ],
    "gcpuf": [
        TrackEntry(
            uuid.uuid4(),
            NODE_UUID1,
            SOURCE_UUID,
            shapely.Point((-0.229466, 51.487613)),
            "gcpuf",
            "gcpugab",
            "abcdef",
            "abcdefgh",
            False,
            True,
            datetime.fromisoformat("2024-03-20T12:20:00-04:00"),
        )
    ],
    "abcdef": [
        TrackEntry(
            uuid.uuid4(),
            NODE_UUID2,
            SOURCE_UUID,
            shapely.Point((0, 1)),
            "abcdef",
            "abcdefgh",
            "abcdef",
            "abcdefgh",
            False,
            False,
            datetime.fromisoformat("2024-03-20T12:10:00-04:00"),
        )
    ],
}


class BaseTrackService:
    @staticmethod
    def find_location_by_geohash(
        geohash_low: str, track_node_id: uuid.UUID, min_time: datetime, max_time: datetime, target_time: datetime
    ) -> List[TrackEntry]:
        """
        Find points in other tracks that match the geohash of the given point within the time
        intervals.
        This query:

        SELECT distinct on (track_node_id) track_node_id, source_id, start_time
                FROM tracks
                WHERE geohash_low = :geohash and track_node_id != :trackNodeId and start_time > :minimumTime
        and start_time < :maximumTime
                ORDER BY track_node_id, abs(extract(epoch from(start_time - :targetTime)))

        :param geohash_low: Geohash to match in the DB
        :param track_node_id: Track node to ignore
        :param min_time: Min allowed time to lag by
        :param max_time: Max allowed time to lag by
        :param target_time: time to sort the response by
        :return: List of cotravels

        """
        # TODO actually hit the database
        return TRACK_ENTRIES_DB.get(geohash_low, [])

    @staticmethod
    async def query_for_similar_tracks(
        first: shapely.Point, last: shapely.Point, query_distance: float
    ) -> List[GroupByTrackNodeIdProjection]:
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

        :param first: Point of the first point in the track
        :return: List of GroupByTrackNodeIdProjections
        """
        return [GroupByTrackNodeIdProjection(NODE_UUID1, [])]

    @staticmethod
    async def get_track(track_node_id: uuid.UUID) -> Track:
        """
        Get Track by UUID

        :param track_node_id: node id of the Track to retrieve
        :return: Track object
        """
        # TODO actually hit a DB
        return Track(
            track_node_id,
            [
                ProcessedPoint(
                    TRACK_ENTRIES_DB["gcpuu"][0].geometry,
                    TRACK_ENTRIES_DB["gcpuu"][0].start_time,
                    TRACK_ENTRIES_DB["gcpuu"][0].is_start,
                    TRACK_ENTRIES_DB["gcpuu"][0].is_end,
                ),
                ProcessedPoint(
                    TRACK_ENTRIES_DB["gcpug"][0].geometry,
                    TRACK_ENTRIES_DB["gcpug"][0].start_time,
                    TRACK_ENTRIES_DB["gcpug"][0].is_start,
                    TRACK_ENTRIES_DB["gcpug"][0].is_end,
                ),
                ProcessedPoint(
                    TRACK_ENTRIES_DB["gcpuf"][0].geometry,
                    TRACK_ENTRIES_DB["gcpuf"][0].start_time,
                    TRACK_ENTRIES_DB["gcpuf"][0].is_start,
                    TRACK_ENTRIES_DB["gcpuf"][0].is_end,
                ),
            ],
        )
