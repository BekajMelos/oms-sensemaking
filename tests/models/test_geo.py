from uuid import uuid4

import shapely
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Confidence

from oms_sensemaking.models.geo import Point


def test_point_comparison():
    detection_time = "2024-01-02T00:00:00+00:00"
    geopoint = shapely.Point(-0.030890, 51.509420).wkt
    point = Point(
        node_id=uuid4(),
        node_version=1,
        source_id=uuid4(),
        observation_id=uuid4(),
        observation_version=1,
        observation_confidence=Confidence.LOW,
        location=geopoint,
        altitude=0,
        detection_time=detection_time,
        acm=DEFAULT_ACM,
        weight=1,
    )

    detection_time2 = "2025-01-02T00:00:00+00:00"
    geopoint2 = shapely.Point(-11.3726, 25.92723).wkt
    point2 = Point(
        node_id=uuid4(),
        node_version=1,
        source_id=uuid4(),
        observation_id=uuid4(),
        observation_version=1,
        observation_confidence=Confidence.LOW,
        location=geopoint2,
        altitude=0,
        detection_time=detection_time2,
        acm=DEFAULT_ACM,
        weight=1,
    )

    assert point < point2
