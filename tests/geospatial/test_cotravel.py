from collections.abc import Generator
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from oms_sdk.generated.generated_graphql_client import Confidence
from sqlalchemy.orm import Session

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
        CotravelType.get_name("invalid")


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


def test_potential_match_post_init_contravel():
    config = {
        "max_potential_duplicate_time_diff_seconds": 10,
        "max_lag_lead_duration_seconds": 20,
    }
    now = datetime.utcnow()
    pm = PotentialMatch(
        vehicle_id1=uuid4(),
        vehicle_id2=uuid4(),
        start_time1=now,
        start_time2=now + timedelta(seconds=15),
        last_time1=now + timedelta(17),
        last_time2=now + timedelta(seconds=30),
        track_id1=uuid4(),
        track_id2=uuid4(),
        config=config,
    )
    assert pm.is_true_cotravel is True
    assert pm.cotravel_type == CotravelType.cotravel


def test_potential_match_post_init_laglead():
    config = {
        "max_potential_duplicate_time_diff_seconds": 10,
        "max_lag_lead_duration_seconds": 20,
    }
    now = datetime.utcnow()
    pm = PotentialMatch(
        vehicle_id1=uuid4(),
        vehicle_id2=uuid4(),
        start_time1=now,
        start_time2=now + timedelta(seconds=30),
        last_time1=now + timedelta(17),
        last_time2=now + timedelta(seconds=80),
        track_id1=uuid4(),
        track_id2=uuid4(),
        config=config,
    )
    assert pm.is_true_cotravel is False
    assert pm.cotravel_type == CotravelType.lag_lead


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


def test_cotravel_get_acm():
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

    with patch("oms_sensemaking.clients.instances.aac_client.get_acm_rollup", return_value={"some": "data"}):
        assert c.get_acm() == {"some": "data"}


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
    assert geojson["coordinates"][1] == [(1.0, 2.0), (1.0, 2.0)]


def test_colocation_str():
    node_id = uuid4()
    p1 = Point(
        acm=DEFAULT_ACM,
        location="POINT (-87.63520 41.85677)",
        altitude=5,
        detection_time=datetime.utcnow(),
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
        detection_time=datetime.utcnow() + timedelta(seconds=10),
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


NODE_UUID1 = uuid4()
NODE_UUID2 = uuid4()
NODE_UUID3 = uuid4()
SOURCE_ID = uuid4()
TRACK_UUID1 = uuid4()
TRACK_UUID2 = uuid4()
TRACK_UUID3 = uuid4()
TRACK_UUID4 = uuid4()
DATA = {  # Latitude, Longitude, Altitude (m), Description, Node ID, Obs ID, detection_time, Obs confidence
    # Track 1
    TRACK_UUID1: [
        [
            51.482286,
            -0.165222,
            None,
            "London",
            NODE_UUID1,
            uuid4(),
            datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
            Confidence.HIGH,
        ],
        [
            51.466103,
            -0.210562,
            None,
            "London",
            NODE_UUID1,
            uuid4(),
            datetime.fromisoformat("2024-03-20T12:10:00-04:00"),
            Confidence.HIGH,
        ],
        [
            51.487613,
            -0.229466,
            None,
            "London",
            NODE_UUID1,
            uuid4(),
            datetime.fromisoformat("2024-03-20T12:20:00-04:00"),
            Confidence.HIGH,
        ],
        # point that shouldn't be included in the cotravel
        [
            50,
            0,
            None,
            "English Channel",
            NODE_UUID1,
            uuid4(),
            datetime.fromisoformat("2024-03-20T12:30:00-04:00"),
            Confidence.HIGH,
        ],
    ],
    # Track 2
    TRACK_UUID2: [
        [
            41.399953,
            2.217167,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:10:00-04:00"),
            Confidence.HIGH,
        ],
        [
            41.467810,
            2.289575,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:00:00-04:00"),
            Confidence.HIGH,
        ],
        [
            41.356069,
            2.183748,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:20:00-04:00"),
            Confidence.HIGH,
        ],
        [
            41.296465,
            2.130487,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:30:00-04:00"),
            Confidence.HIGH,
        ],
    ],
    # Track 3
    TRACK_UUID3: [
        [
            41.467811,
            2.289576,
            None,
            "Barcelona",
            NODE_UUID3,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:19:00-04:00"),
            Confidence.HIGH,
        ],
        [
            41.399954,
            2.217168,
            None,
            "Barcelona",
            NODE_UUID3,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:29:00-04:00"),
            Confidence.HIGH,
        ],
        [
            41.356070,
            2.183749,
            None,
            "Barcelona",
            NODE_UUID3,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:39:00-04:00"),
            Confidence.HIGH,
        ],
    ],
    # Track 4
    TRACK_UUID4: [
        [
            38.252533,
            15.650729,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-09-10T05:00:00-04:00"),
            Confidence.HIGH,
        ],
        [
            38.228556,
            15.610534,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-09-10T05:10:00-04:00"),
            Confidence.HIGH,
        ],
        [
            38.185378,
            15.594253,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-09-10T05:20:00-04:00"),
            Confidence.HIGH,
        ],
        [
            38.142175,
            15.578989,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-09-10T05:30:00-04:00"),
            Confidence.HIGH,
        ],
    ],
}


@pytest.fixture
def tester_db(db) -> Generator[Session, Any, None]:
    for track_uuid, rows in DATA.items():
        points: list[Point] = []
        for row in rows:
            point, _ = Point.get_or_create(
                session=db,
                node_id=row[4],
                node_version=1,
                observation_id=row[5],
                observation_version=1,
                location=f"POINT({row[1]} {row[0]})",  # lng lat
                altitude=row[2],
                detection_time=row[6],
                acm=DEFAULT_ACM,
                source_id=SOURCE_ID,
                observation_confidence=row[7],
                # geohash=geohash.encode(lat=row[1], lon=row[0], precision=10)
            )
            points.append(point)
        Track.get_or_create(
            session=db,
            defaults=dict(points=points, node_id=points[0].node_id, algorithm="cotravel_test_track", acm=DEFAULT_ACM),
            track_uuid=track_uuid,
        )

    yield db


@pytest.fixture
def test_point():
    p1 = Point(
        acm=DEFAULT_ACM,
        location="POINT (-0.165222 51.482286)",
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"),
        node_id=NODE_UUID1,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        observation_confidence=Confidence.HIGH,
        source_id=uuid4(),
    )
    return p1


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


def test_publish_potential_duplicate_calls_publish_relationships(sensemaker, sample_track):
    # Arrange
    cotravel = MagicMock()
    cotravel.track1.node_id = "track1-id"
    cotravel.track2.node_id = "track2-id"
    cotravel.get_acm.return_value = {"acm": "fake"}

    sensemaker.publish_potential_duplicate(sample_track, cotravel)

    # Assert
    sensemaker.oms_crud_tool.publish_relationships.assert_called_once()
    args, _ = sensemaker.oms_crud_tool.publish_relationships.call_args
    [relationship_input] = args[0]

    assert relationship_input.startNodeId == "track1-id"
    assert relationship_input.endNodeId == "track2-id"
    assert relationship_input.acm == {"acm": "fake"}
    assert relationship_input.sourceId == sample_track.points[0].source_id


def test_publish_cotravel_creates_node_and_relationships(sensemaker, sample_track):
    # Arrange
    cotravel = MagicMock()
    cotravel.cotravel_type = CotravelType.cotravel
    cotravel.track1.node_id = "track1-id"
    cotravel.track2.node_id = "track2-id"
    cotravel.get_acm.return_value = {"acm": "fake"}
    cotravel.start_time = "start"
    cotravel.last_time = "end"
    cotravel.to_geojson.return_value = {"type": "LineString"}

    # Fake published node with an ID
    published_node = MagicMock()
    published_node.id = "node-id"

    sensemaker.oms_crud_tool.create_node.return_value = published_node

    # Act
    sensemaker.publish_cotravel(sample_track, cotravel)

    # Assert: node creation
    sensemaker.oms_crud_tool.create_node.assert_called_once()
    create_node_input = sensemaker.oms_crud_tool.create_node.call_args.kwargs["node_input"]
    assert create_node_input.name == "Cotravel"
    assert create_node_input.acm == {"acm": "fake"}

    # Assert: relationships published
    sensemaker.oms_crud_tool.publish_relationships.assert_called_once()
    relationships = sensemaker.oms_crud_tool.publish_relationships.call_args[0][0]
    assert len(relationships) == 2
    assert relationships[0].startNodeId == "node-id"
    assert relationships[0].endNodeId == "track1-id"
    assert relationships[1].endNodeId == "track2-id"

    # Assert: attribute published
    sensemaker.oms_crud_tool.publish_attributes.assert_called_once()
    [attribute_input] = sensemaker.oms_crud_tool.publish_attributes.call_args[0][0]
    assert attribute_input.nodeId == "node-id"
    assert attribute_input.geometry == {"type": "LineString"}
    assert attribute_input.valueStart == "start"
    assert attribute_input.valueEnd == "end"
