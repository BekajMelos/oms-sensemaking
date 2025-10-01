from uuid import uuid4

import pytest
import shapely
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Confidence

from oms_sensemaking.models.geo import Point


def point_factory(detection_time):
    return Point(
        node_id=uuid4(),
        node_version=1,
        source_id=uuid4(),
        observation_id=uuid4(),
        observation_version=1,
        observation_confidence=Confidence.LOW,
        location=shapely.Point(-0.030890, 51.509420).wkt,
        altitude=0,
        detection_time=detection_time,
        acm=DEFAULT_ACM,
        weight=1,
    )


@pytest.mark.parametrize(
    "p1, p2, expected",
    [
        (point_factory("2024-01-02T00:00:00+00:00"), point_factory("2025-01-02T00:00:00+00:00"), True),
        (point_factory("2025-01-02T00:00:00+00:00"), point_factory("2024-01-02T00:00:00+00:00"), False),
        (point_factory("2025-01-02T00:00:00+00:00"), point_factory("2025-01-02T00:00:00+00:00"), False),
    ],
    ids=["p1 is less than p2", "p1 is greater than p2", "p1 is equal to p2"],
)
def test_less_than_point_comparison(p1, p2, expected):
    assert (p1 < p2) == expected
