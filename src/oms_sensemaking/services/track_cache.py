import asyncio
import logging
import os
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import shapely
from oms_sensemaking.models.processed_point import ProcessedPoint
from oms_sensemaking.models.track import Track
from oms_sensemaking.services.cotravel import CotravelService
from oms_sensemaking.services.loiter import LoiterService
from oms_sensemaking.services.similar_tracks import MostSimilarTrackService

LOGGER = logging.getLogger(__name__)


CACHE_ENTRY_EXPIRE_SEC = timedelta(seconds=int(os.environ["CACHE_ENTRY_EXPIRE_SEC"]))
DETECT_LOITERS = os.environ["DETECT_LOITERS"].lower() in ["true", "yes", "on"]
DETECT_COTRAVELS = os.environ["DETECT_COTRAVELS"].lower() in ["true", "yes", "on"]
SIMILAR_TRACKS = os.environ["SIMILAR_TRACKS"].lower() in ["true", "yes", "on"]
POLL_PERIOD_SECONDS = int(os.environ["POLL_PERIOD_SECONDS"])


class Attribute:
    def __init__(self, identifier: str, lat: float, lon: float, timestamp=None):
        self.identifier = identifier
        self.lat = lat
        self.lon = lon
        self.timestamp = timestamp

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class TrackCacheService:
    def __init__(self, q: asyncio.Queue):
        self.q = q
        self.cache: Dict[str, List[Tuple[datetime, Attribute]]] = defaultdict(list)

    async def add_point(self, point):
        self.cache[point.identifier].append((datetime.now(), point))

    async def check_expirations(self):
        """Check for Points that have waited past the expiration time and should be processed"""

        LOGGER.info("Checking Expirations")
        now = datetime.now()
        for key in list(self.cache.keys()):
            if self.cache[key][-1][0] + CACHE_ENTRY_EXPIRE_SEC < now:
                points: List[Attribute] = self.cache.pop(key)

                track = await self.create_track(points)
                await self.further_processing(track)

    async def wait_for_events(self) -> None:
        """Wait for events to enter the queue"""

        while True:
            LOGGER.info("Requesting messages from the queue")
            while not self.q.empty():
                event = await self.q.get()

                # this could be where we filter events for the points we want
                await self.handle_event(event)
                self.q.task_done()

            await self.check_expirations()
            # wait 10 seconds
            await asyncio.sleep(POLL_PERIOD_SECONDS)

    async def handle_event(self, point) -> None:
        """Handle incoming event"""
        await self.add_point(point)

    async def create_track(self, points) -> Track:
        """Combine the points into a Track object

        :param points: List of Point objects
        :return: The created Track
        """
        processed_points = [
            ProcessedPoint(
                shapely.Point(point[1].lon, point[1].lat),
                point[1].timestamp,
                idx == 0,
                idx == len(points) - 1,
            )
            for idx, point in enumerate(points)
        ]
        return Track(uuid.uuid4(), processed_points)

    async def further_processing(self, track: Track) -> None:
        """Initiate Analytics

        :param track: Track to perform detections on
        :return: None
        """
        LOGGER.info(f"Additional Processing on {track}")
        LOGGER.debug(shapely.LineString([(point.geometry.x, point.geometry.y) for point in track.points]))

        # TODO maybe these shouldn't be hard coded and should be "registered"?
        if DETECT_COTRAVELS:
            _ = await CotravelService.detect_cotravels(track)

        if DETECT_LOITERS:
            _ = await LoiterService.detect_loiters(track)

        if SIMILAR_TRACKS:
            _ = await MostSimilarTrackService.most_similar_track_node_ids(track)
