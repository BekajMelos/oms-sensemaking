"""Tests for co-travler sensemaker."""

import uuid
from datetime import datetime

import shapely
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.geospatial.cotravel import CotravelService
from oms_sensemaking.models.geo import Point, Track


def test_cotravel_success():

    node_id = uuid.uuid4()

    # Note these points/timestamps are set to match the base_track_service hard coded "DB"
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.148931, 51.484423).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)

    p2 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.186849, 51.465229).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)

    p3 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.225258, 51.476589).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:25:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)

    # Create Track Object
    track = Track(points=[p1, p2, p3], node_id=uuid.uuid4())

    cotravels = CotravelService.detect_cotravels(track)

    assert len(cotravels) == 1
    cotravel = cotravels[0]
    assert cotravel.track1 == track.node_id
    assert cotravel.start_time1 == p1.detection_time
    assert cotravel.start_time2 == datetime.fromisoformat("2024-03-20T12:00:00-04:00")
    assert cotravel.last_time1 == p3.detection_time
    assert cotravel.last_time2 == datetime.fromisoformat("2024-03-20T12:20:00-04:00")
