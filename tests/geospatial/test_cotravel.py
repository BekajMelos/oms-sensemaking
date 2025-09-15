from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from oms_sensemaking.geospatial.sensemakers.cotravel import (
    Colocation,
    Cotravel,
    CotravelType,
    PotentialMatch,
)


def test_cotravel_type_get_name():
    assert CotravelType.get_name(CotravelType.potential_duplicate) == "Potential Duplicate"
    assert CotravelType.get_name(CotravelType.cotravel) == "Cotravel"
    assert CotravelType.get_name(CotravelType.lag_lead) == "LagLead"
    with pytest.raises(ValueError):
        CotravelType.get_name("invalid")  # type: ignore


def test_potential_match_post_init():
    config = {
        "max_potential_duplicate_time_diff_seconds": 10,
        "max_lag_lead_duration_seconds": 20,
    }
    now = datetime.utcnow()
    pm = PotentialMatch(
        vehicle_id1=uuid4(),
        vehicle_id2=uuid4(),
        start_time1=now,
        start_time2=now + timedelta(seconds=5),
        last_time1=now,
        last_time2=now + timedelta(seconds=5),
        track_id1=uuid4(),
        track_id2=uuid4(),
        config=config,
    )
    assert pm.is_true_cotravel is True
    assert pm.cotravel_type == CotravelType.potential_duplicate


def test_potential_match_tentative_add():
    config = {
        "max_potential_duplicate_time_diff_seconds": 10,
        "max_lag_lead_duration_seconds": 20,
        "valid_observed_threshold_seconds": 5,
        "min_lag_lead_duration_seconds": 2,
    }
    now = datetime.utcnow()
    pm = PotentialMatch(
        vehicle_id1=uuid4(),
        vehicle_id2=uuid4(),
        start_time1=now,
        start_time2=now,
        last_time1=now,
        last_time2=now,
        track_id1=uuid4(),
        track_id2=uuid4(),
        config=config,
    )

    updated = pm.tentative_add(now + timedelta(seconds=3), now + timedelta(seconds=3))
    assert updated
    assert pm.num_points == 1
    assert isinstance(pm.total_time_diff, timedelta)


def test_check_valid_cotravel_duration():
    config = {"min_cotravel_duration_seconds": 10, "max_potential_duplicate_time_diff_seconds": 30}
    now = datetime.utcnow()
    pm = PotentialMatch(
        vehicle_id1=uuid4(),
        vehicle_id2=uuid4(),
        start_time1=now,
        start_time2=now,
        last_time1=now + timedelta(seconds=15),
        last_time2=now + timedelta(seconds=15),
        track_id1=uuid4(),
        track_id2=uuid4(),
        config=config,
    )
    assert pm.check_valid_cotravel_duration() is True


def test_cotravel_post_init():
    # Mock Track and Point
    mock_point = MagicMock()
    mock_point.coordinates = (0.0, 0.0)
    mock_point.acm = {"some": "data"}

    mock_track = MagicMock()
    mock_track.points = [mock_point, mock_point]

    c = Cotravel(
        track1=mock_track,
        track2=mock_track,
        start_time=datetime.utcnow(),
        last_time=datetime.utcnow(),
        cotravel_type=CotravelType.cotravel,
    )

    # Check that geometry is MultiLineString
    assert c.geometry.geom_type == "MultiLineString"
    assert len(c.geometry.geoms) == 2


def test_cotravel_to_geojson():
    mock_point = MagicMock()
    mock_point.coordinates = (1.0, 2.0)

    mock_track = MagicMock()
    mock_track.points = [mock_point, mock_point]

    c = Cotravel(
        track1=mock_track,
        track2=mock_track,
        start_time=datetime.utcnow(),
        last_time=datetime.utcnow(),
        cotravel_type=CotravelType.cotravel,
    )

    geojson = c.to_geojson()
    assert geojson["type"] == "MultiLineString"
    assert geojson["coordinates"][0] == [(1.0, 2.0), (1.0, 2.0)]


def test_colocation_str():
    shapely_point = Point(1, 2)
    mock_point1 = MagicMock()
    mock_point1.detection_time = datetime.utcnow()
    mock_point2 = MagicMock()
    mock_point2.detection_time = datetime.utcnow()
    mock_point1.location = from_shape(shapely_point, srid=4326)  # returns WKBElement
    mock_point2.location = from_shape(shapely_point, srid=4326)

    col = Colocation(
        track1_node_id=uuid4(),
        track2_node_id=uuid4(),
        track1_id=uuid4(),
        track2_id=uuid4(),
        point=mock_point1,
        db_point=mock_point2,
    )

    s = str(col)
    assert "Colocation:" in s
