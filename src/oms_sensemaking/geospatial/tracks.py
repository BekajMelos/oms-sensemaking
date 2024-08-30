"""Provides utilities for working with tracks."""

import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from queue import PriorityQueue
from typing import Dict, List

import pandas as pd
import shapely
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.pubsub import PubSub
from oms_sensemaking.geospatial.models.group_by_track_node_id_projection import GroupByTrackNodeIdProjection
from oms_sensemaking.geospatial.models.track_entry import TrackEntry
from oms_sensemaking.models.geo import Point, Track

CACHE_ENTRY_EXPIRE_SEC = timedelta(seconds=SETTINGS.cache_entry_expire_sec)

LOGGER = logging.getLogger(__name__)

TRACK_CREATED_EVENT: str = "track_created"

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
    def query_for_similar_tracks(
        first: List[float], last: List[float], query_distance: float
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
                    shapely.Point((-0.165222, 51.482286)).wkt,
                    altitude=None,
                    detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
                    node_id=track_node_id,
                    node_version=1,
                    attribute_id=uuid.uuid4(),
                    attribute_version=1
                ),
                Point(
                    DEFAULT_ACM,
                    shapely.Point((-0.210562, 51.466103)).wkt,
                    altitude=None,
                    detection_time=datetime.fromisoformat("2024-03-20T12:10:00-04:00"),
                    node_id=track_node_id,
                    node_version=1,
                    attribute_id=uuid.uuid4(),
                    attribute_version=1
                ),
                Point(
                    DEFAULT_ACM,
                    shapely.Point((-0.229466, 51.487613)).wkt,
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


class TrackCacheService(PubSub):
    def __init__(self, point_ingest_queue: asyncio.Queue):
        super().__init__()
        self.point_ingest_queue = point_ingest_queue
        # cache for collecting points into a track
        self._point_cache: Dict[uuid.UUID, PriorityQueue[Point]] = defaultdict(PriorityQueue)
        # cache for tracking the latest observed timestamp per track_node_id. the track_node_id should match the track
        # being collected in the point cache
        self._timestamp_cache: Dict[uuid.UUID, datetime] = {}

    async def add_point(self, point: Point):
        """
        Add a point to the cache. Point goes to the point_cache and observed timestamp goes to the timestamp
        cache

        :param point: Point object to cache and collect into track
        :return: None
        """
        self._point_cache[point.node_id].put(point)
        self._timestamp_cache[point.node_id] = datetime.now()

    async def check_expirations(self) -> None:
        """Check for Points that have waited past the expiration time and should be processed."""

        LOGGER.info("Checking Expirations")
        now = datetime.now()
        for track_node_id in list(self._timestamp_cache.keys()):
            if self._timestamp_cache[track_node_id] + CACHE_ENTRY_EXPIRE_SEC < now:
                points: PriorityQueue[Point] = self._point_cache.pop(track_node_id)
                # expire timestamp cache entry which we don't need anymore
                _ = self._timestamp_cache.pop(track_node_id)

                # TODO need to test why some are less than 2
                if len(points.queue) > 2:
                    await self.create_track(track_node_id, points)
                else:
                    LOGGER.warn(f"Track with fewer than two points found: {track_node_id} - ({points})")

    async def wait_for_events(self) -> None:
        """Wait for events to enter the queue."""
        while True:
            LOGGER.info("Requesting messages from the queue")
            while not self.point_ingest_queue.empty():
                event = await self.point_ingest_queue.get()

                # this could be where we filter events for the points we want
                await self.handle_event(event)
                self.point_ingest_queue.task_done()

            await self.check_expirations()
            # wait 10 seconds
            await asyncio.sleep(SETTINGS.poll_period_seconds)

    async def handle_event(self, point) -> None:
        """Handle incoming event."""
        await self.add_point(point)

    async def create_track(self, track_node_id: uuid.UUID, points: PriorityQueue) -> Track:
        """
        Combine the points into a Track object.

        :param points: List of Point objects
        :return: The created Track
        """

        track_points = []

        # get points in order
        while not points.empty():
            point: Point = points.get_nowait()
            track_points.append(point)

        track: Track = Track(points=track_points, node_id=track_node_id)

        self.publish(TRACK_CREATED_EVENT, track)

        return track


async def produce_attributes_from_csv(q: asyncio.Queue, file_name: str) -> None:
    """
    Publish CSV data to an asyncio Queue.

    :param q: The Queue to publish data to.
    :param file_name: The CSV file to parse.
    """
    LOGGER.info("Producer: Running")

    df = pd.read_csv(file_name)
    LOGGER.debug(df)
    for _, row in df.iterrows():
        point = Point(
            acm=DEFAULT_ACM,
            location=shapely.Point(row["lon"], row["lat"]).wkt,
            altitude=None,
            detection_time=datetime.fromtimestamp(int(row["now"]), tz=timezone.utc),
            node_id=row["r"],
            node_version=1,
            attribute_id=uuid.uuid4(),
            attribute_version=1
        )
        await q.put(point)
