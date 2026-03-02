import random
from datetime import datetime, timedelta, timezone
from unittest import mock
from uuid import uuid4

import pytest
import shapely
from oms_sdk.generated.generated_graphql_client import NodeNode
from oms_sdk.generated.generated_graphql_client.enums import Confidence
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.sensemakers.loiters import Loiter, LoiterSensemaker, PotentialLoiter
from oms_sensemaking.models.geo import Point, Track
from oms_sensemaking.models.sensemaking import AtomsType

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


@pytest.fixture
def mock_crud_tool(mocker: MockerFixture):
    mock_tool = mocker.Mock(spec=OmsCrudTool)
    return mock_tool


def get_random_stamford_bridge_point() -> str:
    #  Get point near Stamford Bridge - all within geohash5 gcpug
    lon_max = -0.189286
    lon_min = -0.192512
    lat_max = 51.482857
    lat_min = 51.480729

    return shapely.Point(random.uniform(lon_min, lon_max), random.uniform(lat_min, lat_max)).wkt


def get_random_emirates_stadium_point() -> str:
    #  Get point near Emirates stadium - all within geohash5 gcpvm
    lon_max = -0.107211
    lon_min = -0.109761
    lat_max = 51.556461
    lat_min = 51.554000

    return shapely.Point(random.uniform(lon_min, lon_max), random.uniform(lat_min, lat_max)).wkt


@pytest.fixture
def test_node(mocker: MockerFixture):
    """
    A parent node of observational_node_region1
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "incurring_object_id"
    node.acm = DEFAULT_ACM
    node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"
    node.name = "test node"

    return node


@pytest.fixture
def test_potential_loiter(mocker: MockerFixture):
    potential = mocker.Mock(spec=PotentialLoiter)
    potential.start_time = datetime.fromisoformat("2024-03-20T12:00:00-04:00")
    potential.latest_time = datetime.fromisoformat("2024-03-20T12:44:00-04:00")
    return potential


@pytest.fixture
def processed_points(test_node):
    p1 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-0.030890, 51.509420).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
        node_id=test_node.id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(
        acm=DEFAULT_ACM,
        location=p2_point,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"),
        node_id=test_node.id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(
        acm=DEFAULT_ACM,
        location=p3_point,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"),
        node_id=test_node.id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(
        acm=DEFAULT_ACM,
        location=p4_point,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"),
        node_id=test_node.id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(
        acm=DEFAULT_ACM,
        location=p5_point,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:16:00-04:00"),
        node_id=test_node.id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(
        acm=DEFAULT_ACM,
        location=p6_point,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"),
        node_id=test_node.id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )
    # West London way later
    p7 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-0.413890, 51.474942).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:44:00-04:00"),
        node_id=test_node.id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )
    return [p1, p2, p3, p4, p5, p6, p7]


@pytest.fixture
def test_track(mocker: MockerFixture, processed_points, test_node):
    # Create Track Object
    track = mocker.Mock(spec=Track)

    track.points = processed_points
    track.node_id = test_node.id
    track.algorithm = "test_track"
    track.track_uuid = uuid4
    track.acm = DEFAULT_ACM

    return track


def test_pot_loiter_init():
    start_time = datetime.now(timezone.utc)
    latest_time = datetime.now(timezone.utc) + timedelta(seconds=10)
    test_pot_loiter = PotentialLoiter(start_time, latest_time)
    assert test_pot_loiter.start_time == start_time
    assert test_pot_loiter.latest_time == latest_time


def test__str__pot_loiter():
    start_time = datetime.now(timezone.utc)
    latest_time = datetime.now(timezone.utc) + timedelta(seconds=10)
    test_pot_loiter = PotentialLoiter(start_time, latest_time)
    assert test_pot_loiter.__str__() == str(test_pot_loiter.__dict__)


def test__repr__pot_loiter():
    start_time = datetime.now(timezone.utc)
    latest_time = datetime.now(timezone.utc) + timedelta(seconds=10)
    test_pot_loiter = PotentialLoiter(start_time, latest_time)
    assert test_pot_loiter.__repr__() == test_pot_loiter.__str__()


@pytest.fixture
def loiter_sm(mock_crud_tool):
    return LoiterSensemaker(mock_crud_tool)


@pytest.fixture
def test_loiter(test_track, test_potential_loiter, mock_crud_tool):
    loiter_sm = LoiterSensemaker(mock_crud_tool)
    loiter_sm.config = {
        "loiter_activity_iri": SETTINGS.loiter_activity_iri,
        "loiter_activity_name": SETTINGS.loiter_activity_name,
        "loiter_activity_state": SETTINGS.loiter_activity_state,
        "valid_observed_threshold_seconds": 900,
        "loiter_geohash": 5,
        "cotravel_geohash": 5,
        "similar_tracks_geohash": 5,
        "loiter_min_time": 900,
        "min_cotravel_duration_seconds": 1200,
        "min_lag_lead_duration_seconds": 1200,
        "max_lag_lead_duration_seconds": 2700,
        "max_potential_duplicate_time_diff_seconds": 30,
        "within_meters": 3000.0,
    }
    loiter_points = loiter_sm._points_in_time_window(test_track, test_potential_loiter)
    geometry = shapely.LineString([point.coordinates for point in loiter_points])
    prospective_loiters = loiter_sm.find_prospective_loiters(test_track.points)
    for point_geohash, _ in prospective_loiters.items():
        first_geohash = point_geohash
        break
    test_loiter = Loiter(
        vehicle_id=uuid4(),
        geohash=first_geohash,
        start_time=loiter_points[0].detection_time,
        end_time=loiter_points[-1].detection_time,
        processed_points=loiter_points,
        geometry=geometry,
    )
    return test_loiter


def test_get_acm_loiter(test_loiter):
    with mock.patch("oms_sensemaking.clients.instances.aac_client.get_acm_rollup") as mock_get_acm:
        # Return a fake ACM rollup
        mock_get_acm.return_value = [DEFAULT_ACM] * 7

        acm_list = test_loiter.get_acm()
        assert len(acm_list) == 7


def test__str__loiter(test_loiter):
    assert test_loiter.__str__() == str(test_loiter.to_dict())


def test__repr__loiter(test_loiter):
    assert test_loiter.__str__() == test_loiter.__repr__()


def test_to_geojson_loiter(test_loiter):
    assert test_loiter.to_geojson() == {
        "type": "LineString",
        "coordinates": [point.coordinates for point in test_loiter.processed_points],
    }


def test_points_in_time_window(loiter_sm, test_track, test_potential_loiter):
    points_in_window = loiter_sm._points_in_time_window(test_track, test_potential_loiter)
    assert all(
        test_potential_loiter.start_time <= p.detection_time <= test_potential_loiter.latest_time
        for p in points_in_window
    )


def test_find_prospective_loiters(loiter_sm, processed_points):
    loiter_sm.config = {
        "loiter_activity_iri": SETTINGS.loiter_activity_iri,
        "loiter_activity_name": SETTINGS.loiter_activity_name,
        "loiter_activity_state": SETTINGS.loiter_activity_state,
        "valid_observed_threshold_seconds": 900,
        "loiter_geohash": 5,
        "cotravel_geohash": 5,
        "similar_tracks_geohash": 5,
        "loiter_min_time": 900,
        "min_cotravel_duration_seconds": 1200,
        "min_lag_lead_duration_seconds": 1200,
        "max_lag_lead_duration_seconds": 2700,
        "max_potential_duplicate_time_diff_seconds": 30,
        "within_meters": 3000.0,
    }
    prospective_loiters = loiter_sm.find_prospective_loiters(processed_points)
    assert isinstance(prospective_loiters, dict)
    # Ensure keys are strings (geohashes) and values are lists of PotentialLoiter
    for key, value in prospective_loiters.items():
        assert isinstance(key, str)
        assert all(isinstance(v, PotentialLoiter) for v in value)


def test_process_data_creates_loiters(loiter_sm, test_track, mock_crud_tool):
    config = {
        "loiter_activity_iri": SETTINGS.loiter_activity_iri,
        "loiter_activity_name": SETTINGS.loiter_activity_name,
        "loiter_activity_state": SETTINGS.loiter_activity_state,
        "valid_observed_threshold_seconds": 900,
        "loiter_geohash": 5,
        "cotravel_geohash": 5,
        "similar_tracks_geohash": 5,
        "loiter_min_time": 900,
        "min_cotravel_duration_seconds": 1200,
        "min_lag_lead_duration_seconds": 1200,
        "max_lag_lead_duration_seconds": 2700,
        "max_potential_duplicate_time_diff_seconds": 30,
        "within_meters": 3000.0,
    }
    with mock.patch("oms_sensemaking.clients.instances.aac_client.get_acm_rollup") as mock_get_acm:
        mock_get_acm.return_value = [DEFAULT_ACM] * 7
        mock_crud_tool.create_activity.return_value = type("Activity", (), {"id": uuid4()})()
        loiters = loiter_sm.process_data(test_track, config)
        assert isinstance(loiters, list)
        if loiters:
            # Verify that Loiter objects are returned
            for loiter in loiters:
                assert isinstance(loiter, Loiter)
                assert loiter.start_time <= loiter.end_time
                assert isinstance(loiter.geometry, shapely.LineString)


def test_publish_loiter_calls_oms_crud(loiter_sm, test_track, test_loiter, mock_crud_tool):
    with mock.patch("oms_sensemaking.clients.instances.aac_client.get_acm_rollup") as mock_get_acm:
        mock_get_acm.return_value = [DEFAULT_ACM] * 7
        fake_activity_id = uuid4()
        mock_crud_tool.create_activity.return_value = type("Activity", (), {"id": fake_activity_id})()
        loiter_sm.publish_loiter(test_track, test_loiter)
        assert mock_crud_tool.create_activity.called
        assert test_loiter.atoms_type == AtomsType.ACTIVITY
        assert test_loiter.atoms_id == fake_activity_id


def test_process_data_calls_publish_loiter(loiter_sm, test_track, mocker):
    # Patch publish_loiter to check it's called
    mock_publish = mocker.patch.object(loiter_sm, "publish_loiter", return_value=None)
    config = {
        "loiter_activity_iri": SETTINGS.loiter_activity_iri,
        "loiter_activity_name": SETTINGS.loiter_activity_name,
        "loiter_activity_state": SETTINGS.loiter_activity_state,
        "valid_observed_threshold_seconds": 900,
        "loiter_geohash": 5,
        "cotravel_geohash": 5,
        "similar_tracks_geohash": 5,
        "loiter_min_time": 900,
        "min_cotravel_duration_seconds": 1200,
        "min_lag_lead_duration_seconds": 1200,
        "max_lag_lead_duration_seconds": 2700,
        "max_potential_duplicate_time_diff_seconds": 30,
        "within_meters": 3000.0,
    }
    loiter_sm.process_data(test_track, config)
    assert mock_publish.called
