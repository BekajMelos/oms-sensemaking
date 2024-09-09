"""Provides utilities for working with tracks."""
import logging
import uuid
from datetime import datetime

import shapely

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


