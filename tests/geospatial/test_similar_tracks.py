from datetime import datetime
from queue import PriorityQueue
from uuid import uuid4

import pytest
import shapely
from oms_sdk.generated.generated_graphql_client import Confidence, NodeNode
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.geospatial.sensemakers.similar_tracks import ComparisonResult, SimilarTracksSensemaker, TopSimilar
from oms_sensemaking.models.geo import Point

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
def processed_points(test_node):
    p1 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(
            41.467810,
            2.289575,
        ).wkt,
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
    p2_point = shapely.Point(41.399953, 2.217167).wkt
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
    p3_point = shapely.Point(41.356069, 2.183748).wkt
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
    return [p1, p2, p3]


@pytest.fixture
def similar_points(test_node):
    p4_point = shapely.Point(41.467811, 2.289576).wkt
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
    p5_point = shapely.Point(41.399954, 2.217168).wkt
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
    p6_point = shapely.Point(41.356070, 2.183749).wkt
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
    return [p4, p5, p6]


@pytest.fixture
def geo_config():
    config = {
        "loiter_event_node_iri": SETTINGS.loiter_event_node_iri,
        "loiter_relationship_iri": SETTINGS.loiter_relationship_iri,
        "loiter_event_node_attribute_iri": SETTINGS.loiter_event_node_attribute_iri,
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

    return config


@pytest.fixture
def sim_track_sm(geo_config):
    sm = SimilarTracksSensemaker()
    sm.config = geo_config
    return sm


def test_comparison_result_init():
    track_id = uuid4()
    cpr = ComparisonResult(track_id, 0.0)
    assert cpr.track_uuid == track_id
    assert cpr.similarity_score == 0.0


def test_comparison_result_str():
    track_id = uuid4()
    cpr = ComparisonResult(track_id, 0.0)
    assert cpr.__str__() == str(cpr.__dict__)


def test_comparison_result_repr():
    track_id = uuid4()
    cpr = ComparisonResult(track_id, 0.0)
    assert cpr.__repr__() == cpr.__str__()


def test_top_similar_init():
    ts = TopSimilar()
    assert isinstance(ts.top_similarities, PriorityQueue)


def test_top_similar_str():
    ts = TopSimilar()
    assert ts.__str__() == str((ts.top_similarities.maxsize, list(ts.top_similarities.queue)))


def test_top_similar_repr():
    ts = TopSimilar()
    assert ts.__repr__() == ts.__str__()


def test_top_similar_add_comp_result():
    cpr = ComparisonResult(uuid4(), 0.0)
    ts = TopSimilar()
    ts.add_comparison_result(cpr)
    assert (cpr.similarity_score, cpr.track_uuid) in list(ts.top_similarities.queue)


def test_get_buff_geohash_set(sim_track_sm, processed_points):
    st_sm = sim_track_sm
    result = st_sm.get_buffered_geohash_set(processed_points)
    assert len(result) == 12


def test_determine_jaccard_similarity(sim_track_sm, processed_points, similar_points):
    st_sm = sim_track_sm
    track_id = uuid4()
    ref = st_sm.get_buffered_geohash_set(processed_points)
    eval = st_sm.get_buffered_geohash_set(similar_points)
    result = st_sm.determine_jaccard_similarity(ref, eval, track_id)
    assert isinstance(result, ComparisonResult)
    assert result.track_uuid == track_id
    assert result.similarity_score == 1.0
