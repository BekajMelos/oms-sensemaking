"""Tests for similar tracks sensemaker."""

import uuid
from datetime import datetime

import shapely
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.geospatial.sensemakers import SimilarTracksSensemaker
from oms_sensemaking.models.geo import Point, Track


def test_most_similar_tracks_success():
    node_id = uuid.uuid4()
    # Note these points/timestamps are set to match the base_track_service hard coded "DB"
    # first point is wayyy east of london
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(0.226432, 51.479597).wkt, altitude=None,
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

    similar_tracks = SimilarTracksSensemaker().execute(track)

    assert len(similar_tracks.top_similarities.queue) == 1
    assert similar_tracks.top_similarities.queue[0][0] == 0.75
