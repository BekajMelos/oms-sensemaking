import logging
import uuid
from datetime import datetime
from typing import List

from oms_sensemaking.models.track_entry import TrackEntry
from shapely import Point

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
            Point((-0.165222, 51.482286)),
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
            Point((-0.210562, 51.466103)),
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
            Point((-0.229466, 51.487613)),
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
            Point((0, 1)),
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
