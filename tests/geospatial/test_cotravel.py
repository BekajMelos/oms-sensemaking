from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from oms_sdk.generated.generated_graphql_client import Confidence

from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.sensemakers.cotravel import (
    Colocation,
    Cotravel,
    CotravelSensemaker,
    CotravelType,
    PotentialMatch,
)
from oms_sensemaking.models.geo import Point, Track

DEFAULT_ACM = {
    "version": "2.1.0",
    "classif": "U",
    "owner_prod": ["USA"],
    "atom_energy": [],
    "sar_id": [],
    "sci_ctrls": [],
    "disponly_to": [""],
    "dissem_ctrls": [],
    "non_ic": [],
    "rel_to": [],
    "fgi_open": [],
    "fgi_protect": [],
    "portion": "U",
    "banner": "UNCLASSIFIED",
    "dissem_countries": ["USA"],
    "accms": [],
    "macs": [],
    "oc_attribs": [{"orgs": [], "missions": [], "regions": []}],
    "f_clearance": ["u"],
    "f_sci_ctrls": [],
    "f_accms": [],
    "f_oc_org": [],
    "f_regions": [],
    "f_missions": [],
    "f_share": [],
    "f_sar_id": [],
    "f_atom_energy": [],
    "f_macs": [],
    "disp_only": "",
}


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
    now = datetime.now(datetime.timezone.utc)
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
    now = datetime.now(datetime.timezone.utc)
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
    now = datetime.now(datetime.timezone.utc)
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
        start_time=datetime.now(datetime.timezone.utc),
        last_time=datetime.now(datetime.timezone.utc),
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
        start_time=datetime.now(datetime.timezone.utc),
        last_time=datetime.now(datetime.timezone.utc),
        cotravel_type=CotravelType.cotravel,
    )

    geojson = c.to_geojson()
    assert geojson["type"] == "MultiLineString"
    assert geojson["coordinates"][0] == [(1.0, 2.0), (1.0, 2.0)]


def test_colocation_str():
    node_id = uuid4()
    p1 = Point(
        acm=DEFAULT_ACM,
        location="POINT (-87.63520 41.85677)",
        altitude=5,
        detection_time=datetime.now(datetime.timezone.utc),
        node_id=node_id,
        node_version=1,
        observation_id="obs_id1",
        observation_version=1,
        source_id="source1",
        observation_confidence=Confidence.HIGH,
    )
    p2 = Point(
        acm=DEFAULT_ACM,
        location="POINT (-87.67096 41.85733)",
        altitude=100,
        detection_time=datetime.now(datetime.timezone.utc) + timedelta(seconds=10),
        node_id=node_id,
        node_version=1,
        observation_id="obs_id2",
        observation_version=1,
        source_id="source1",
        observation_confidence=Confidence.HIGH,
    )

    col = Colocation(
        track1_node_id=uuid4(),
        track2_node_id=uuid4(),
        track1_id=uuid4(),
        track2_id=uuid4(),
        point=p1,
        db_point=p2,
    )

    s = str(col)
    assert "Colocation:" in s


@pytest.fixture
def mock_crud_tool():
    mock_tool = MagicMock(spec=OmsCrudTool)
    return mock_tool


@pytest.fixture
def sensemaker(mock_crud_tool):
    return CotravelSensemaker(oms_crud_tool=mock_crud_tool)


@pytest.fixture
def sample_track():
    track_uuid = uuid4()
    node_id = uuid4()
    p1 = Point(
        acm=DEFAULT_ACM,
        location="POINT (-0.148931 51.484423)",
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        observation_confidence=Confidence.HIGH,
        source_id=uuid4(),
    )

    p2 = Point(
        acm=DEFAULT_ACM,
        location="POINT (-0.186849 51.465229)",
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        observation_confidence=Confidence.HIGH,
        source_id=uuid4(),
    )
    points = [p1, p2]
    return Track(node_id=node_id, track_uuid=track_uuid, points=points, algorithm="test", observation_ids=[], acm=None)


@patch("oms_sensemaking.geospatial.sensemakers.CotravelSensemaker.get_points", return_value=[])
def test_process_data_no_matches(mock_get_points, sensemaker, sample_track):
    result = sensemaker.process_data(
        sample_track,
        config={
            "cotravel_geohash": 4,
            "max_lag_lead_duration_seconds": 2700,
        },
    )
    assert result == []


def test_extract_coordinate_track(sensemaker, sample_track):
    start_time = sample_track.points[0].detection_time
    end_time = start_time + timedelta(seconds=5)
    points = sensemaker.extract_coordinate_track(sample_track, start_time, end_time)
    assert all(start_time <= p.detection_time <= end_time for p in points)


def test_publish_calls_correct_method(sensemaker, sample_track):
    cotravel = MagicMock()
    cotravel.cotravel_type = CotravelType.cotravel
    with patch.object(sensemaker, "publish_cotravel") as mock_pub_cotravel:
        sensemaker.publish(sample_track, cotravel)
        mock_pub_cotravel.assert_called_once()

    cotravel.cotravel_type = CotravelType.potential_duplicate
    with patch.object(sensemaker, "publish_potential_duplicate") as mock_pub_dup:
        sensemaker.publish(sample_track, cotravel)
        mock_pub_dup.assert_called_once()
