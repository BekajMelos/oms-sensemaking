"""Tests for similar tracks sensemaker."""

from datetime import datetime
from typing import Iterator
from uuid import uuid4

import pytest
import shapely
from oms_sdk import DEFAULT_ACM
from sqlalchemy.orm import Session

from oms_sensemaking.geospatial.sensemakers import SimilarTracksSensemaker
from oms_sensemaking.models.geo import Point, Track

NODE_UUID1 = uuid4()
NODE_UUID2 = uuid4()
NODE_UUID3 = uuid4()
DATA: list = [  # Latitude, Longitude, Altitude (m), Description, Node ID, Attr ID, detection_time,
    # Track 1
    [51.482286, -0.165222, None, "London", NODE_UUID1, uuid4(), datetime.fromisoformat("2024-03-20T12:00:00-04:00")],
    [51.466103, -0.210562, None, "London", NODE_UUID1, uuid4(), datetime.fromisoformat("2024-03-20T12:10:00-04:00")],
    [51.487613, -0.229466, None, "London", NODE_UUID1, uuid4(), datetime.fromisoformat("2024-03-20T12:20:00-04:00")],
    # # Track 2
    [41.467810, 2.289575, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-08-20T16:00:00-04:00")],
    [41.399953, 2.217167, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-08-20T16:10:00-04:00")],
    [41.356069, 2.183748, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-08-20T16:20:00-04:00")],
    [41.296465, 2.130487, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-08-20T16:30:00-04:00")],
    # # Track 3
    [41.467811, 2.289576, None, "Barcelona", NODE_UUID3, uuid4(), datetime.fromisoformat("2024-08-20T16:19:00-04:00")],
    [41.399954, 2.217168, None, "Barcelona", NODE_UUID3, uuid4(), datetime.fromisoformat("2024-08-20T16:29:00-04:00")],
    [41.356070, 2.183749, None, "Barcelona", NODE_UUID3, uuid4(), datetime.fromisoformat("2024-08-20T16:39:00-04:00")],
]


@pytest.fixture
def tester_db(db: Session) -> Iterator[Session]:
    for row in DATA:
        point: Point = Point(
            node_id=row[4],
            node_version=1,
            attribute_id=row[5],
            attribute_version=1,
            location=f"POINT({row[1]} {row[0]})",  # lng lat
            altitude=row[2],
            detection_time=row[6],
            acm=DEFAULT_ACM
        )

        db.add(point)

    db.commit()

    yield db


def test_most_similar_tracks_success_exact_same_path(tester_db):
    """Test similar track with same path."""
    node_id = uuid4()
    # first point is wayyy east of london
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(2.289575, 41.467810).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1)

    p2 = Point(acm=DEFAULT_ACM, location=shapely.Point(2.217167, 41.399953).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1)

    p3 = Point(acm=DEFAULT_ACM, location=shapely.Point(2.183748, 41.356069).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:25:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1)

    # Create Track Object
    track = Track(points=[p1, p2, p3], node_id=uuid4())

    similar_tracks = SimilarTracksSensemaker().execute(track)

    assert len(similar_tracks.top_similarities.queue) == 2
    assert similar_tracks.top_similarities.queue[0][0] == .75
    assert similar_tracks.top_similarities.queue[0][1] == NODE_UUID2
    assert similar_tracks.top_similarities.queue[1][0] == 1
    assert similar_tracks.top_similarities.queue[1][1] == NODE_UUID3


def test_most_similar_tracks_success_start(tester_db):
    """Test similar track where ending point doesn't match the similar track."""
    node_id = uuid4()

    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.165222, 51.482286).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1)

    p2 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.210562, 51.466103).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1)

    # last point is wayyy west of london
    p3 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.405754, 51.489425).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:25:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1)

    # Create Track Object
    track = Track(points=[p1, p2, p3], node_id=uuid4())

    similar_tracks = SimilarTracksSensemaker().execute(track)

    assert len(similar_tracks.top_similarities.queue) == 1
    assert similar_tracks.top_similarities.queue[0][0] == 0.75


def test_most_similar_tracks_success_end(tester_db):
    """Test similar track where starting point doesn't match the similar track."""
    node_id = uuid4()
    # first point is wayyy east of london
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(0.226432, 51.479597).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1)

    p2 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.186849, 51.465229).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1)

    p3 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.225258, 51.476589).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:25:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1)

    # Create Track Object
    track = Track(points=[p1, p2, p3], node_id=uuid4())

    similar_tracks = SimilarTracksSensemaker().execute(track)

    assert len(similar_tracks.top_similarities.queue) == 1
    assert similar_tracks.top_similarities.queue[0][0] == 0.75
