from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.models.geo import Point
from oms_sensemaking.models.track_weavers import ExtendedKalmanTrackWeaver


@pytest.fixture
def ekf_weaver() -> ExtendedKalmanTrackWeaver:
    return ExtendedKalmanTrackWeaver()


def test_ekf_process_point(ekf_weaver: ExtendedKalmanTrackWeaver):
    node_id = uuid4()
    source_id = uuid4()
    observation_id = uuid4()
    detection_time = datetime.now(timezone.utc)
    point = Point(
        node_id=node_id,
        node_version=1,
        source_id=source_id,
        observation_id=observation_id,
        observation_version=1,
        location="POINT (-120.0000 35.0000)",
        altitude=None,
        detection_time=detection_time,
        acm=DEFAULT_ACM,
        observation_confidence=None,
        weight=1.0,
    )
    ekf_weaver._init_ekf(point)
    assert ekf_weaver.ekf is not None
    ekf_weaver.dt = 1.0  # 1 second time step
    ekf_weaver.process_point(point)
    state = ekf_weaver.ekf.x.flatten()
    assert len(state) == ekf_weaver.dimensions  # position and velocity for each dimension
    assert state[0] == pytest.approx(-120.0)
    assert state[1] == pytest.approx(35.0)


def test_ekf_multiple_points(ekf_weaver: ExtendedKalmanTrackWeaver):
    node_id = uuid4()
    source_id = uuid4()
    observation_id = uuid4()
    start_time = datetime.now(timezone.utc)
    points = []
    for i in range(5):
        lat = -120.0000 + i * 0.001
        point = Point(
            node_id=node_id,
            node_version=1,
            source_id=source_id,
            observation_id=observation_id,
            observation_version=1,
            location=f"POINT ({lat} 35.0000)",
            altitude=None,
            detection_time=start_time.replace(microsecond=0) + timedelta(seconds=i),
            acm=DEFAULT_ACM,
            observation_confidence=None,
            weight=1.0,
        )
        points.append(point)
    ekf_weaver._init_ekf(points[0])
    for i in range(1, len(points)):
        ekf_weaver.dt = (points[i].detection_time - points[i - 1].detection_time).total_seconds()
        ekf_weaver.process_point(points[i])
    state = ekf_weaver.ekf.x.flatten()
    assert state[0] == pytest.approx(-119.997215)
    assert state[1] == pytest.approx(35.00057)


def test_ekf_with_weights(ekf_weaver: ExtendedKalmanTrackWeaver):
    node_id = uuid4()
    source_id = uuid4()
    observation_id = uuid4()
    start_time = datetime.now(timezone.utc)
    points = []
    weights = [1.0, 0.5, 1.0, 0.2, 1.0]
    for i in range(5):
        lat = -120.0000 + i * 0.001
        point = Point(
            node_id=node_id,
            node_version=1,
            source_id=source_id,
            observation_id=observation_id,
            observation_version=1,
            location=f"POINT ({lat} 35.0000)",
            altitude=None,
            detection_time=start_time.replace(microsecond=0) + timedelta(seconds=i),
            acm=DEFAULT_ACM,
            observation_confidence=None,
            weight=weights[i],
        )
        points.append(point)
    ekf_weaver._init_ekf(points[0])
    for i in range(1, len(points)):
        ekf_weaver.dt = (points[i].detection_time - points[i - 1].detection_time).total_seconds()
        ekf_weaver.process_point(points[i])
    state = ekf_weaver.ekf.x.flatten()
    assert state[0] == pytest.approx(-120.0000 + 3 * 0.001)
    assert state[1] == pytest.approx(35.0005409)
