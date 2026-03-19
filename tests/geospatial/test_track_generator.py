"""Geo Controller Unit Tests"""

from datetime import datetime, timedelta
from unittest import mock
from uuid import uuid4

import pytest
import shapely
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Confidence, NodeNode, SourceSource

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.ontology_client import OntologyClient
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.exceptions import TrackLengthError
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.track_generator import GeoCSFTrackPointHelpers, TrackGenerator
from oms_sensemaking.models.geo import CommonSenseFilter, Point, Track
from oms_sensemaking.models.track_weavers import NaiveTrackWeaver


@pytest.fixture
def source() -> SourceSource:
    source_id = uuid4()
    source = SourceSource.model_construct(id=source_id, providerId="00000000-0000-0000-0000-000000000000")
    return source


@pytest.fixture
def oms_node() -> NodeNode:
    return NodeNode.model_construct(
        id=uuid4(),
        name="test",
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft",
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def track_points(source) -> list[Point]:
    node_uuid = uuid4()

    # unimportant point
    points = [
        Point(
            acm=DEFAULT_ACM,
            location=shapely.Point(-0.030890, 51.509420).wkt,
            altitude=None,
            detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
            node_id=node_uuid,
            node_version=1,
            observation_id=uuid4(),
            observation_version=1,
            source_id=source.id,
            observation_confidence=Confidence.HIGH,
        ),
        Point(
            acm=DEFAULT_ACM,
            location=shapely.Point(-0.040890, 51.509420).wkt,
            altitude=None,
            detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"),
            node_id=node_uuid,
            node_version=1,
            observation_id=uuid4(),
            observation_version=1,
            source_id=source.id,
            observation_confidence=Confidence.HIGH,
        ),
    ]
    return points


@mock.patch("oms_sensemaking.models.track_weavers.aac_client")
def test_generate_track_too_short(mock_aac_client: AacClient, mock_oms_crud_tool, track_points: list[Point]):
    track_generator = TrackGenerator(OntologyClient(OmsCrudTool()))

    # mock track creation
    track_uuid = uuid4()

    # only 1 point
    track_points = track_points[:1]

    track_generator.get_node_ancestors_iris = mock.MagicMock(return_value=set())

    # call flush buffer. Should raise exception
    with pytest.raises(TrackLengthError):
        track_generator.generate_track(
            track_uuid, NaiveTrackWeaver(), [], {track_uuid: track_points}, mock_oms_crud_tool
        )


def test_bin_points_for_track_groups_by_time_interval(oms_node):
    gen = TrackGenerator(OntologyClient(OmsCrudTool()))
    now = datetime.now()

    points = [
        Point(
            acm=DEFAULT_ACM,
            location=shapely.Point(0, 0).wkt,
            altitude=None,
            detection_time=now,
            node_id=uuid4(),
            node_version=1,
            observation_id=uuid4(),
            observation_version=1,
            source_id=uuid4(),
            observation_confidence=Confidence.HIGH,
        ),
        Point(
            acm=DEFAULT_ACM,
            location=shapely.Point(1, 1).wkt,
            altitude=None,
            detection_time=now + timedelta(seconds=SETTINGS.max_track_time_length_seconds + 1),
            node_id=uuid4(),
            node_version=1,
            observation_id=uuid4(),
            observation_version=1,
            source_id=uuid4(),
            observation_confidence=Confidence.HIGH,
        ),
    ]

    bins = gen.bin_points_for_track(points)

    # Expect 2 bins
    assert len(bins) == 2
    assert sum(len(v) for v in bins.values()) == 2


def test_generate_track_empty_buffer_raises(mock_oms_crud_tool):
    gen = TrackGenerator(OntologyClient(OmsCrudTool()))
    gen.get_node_ancestors_iris = mock.MagicMock(return_value=set())
    track_uuid = uuid4()

    with pytest.raises(TrackLengthError):
        gen.generate_track(track_uuid, NaiveTrackWeaver(), [], {track_uuid: []}, mock_oms_crud_tool)


class DummyFilter(CommonSenseFilter):
    def filter_points(self, pts):
        return pts[1:]  # drop first


def test_csf_single_track_points_applies_filter(track_points):
    f = DummyFilter(name="test", iri="iri://match")
    helpers = GeoCSFTrackPointHelpers([f])
    ancestor_iris = {"iri://match"}
    result = helpers.csf_single_track_points(ancestor_iris, track_points, uuid4())

    assert len(result) == len(track_points) - 1


def test_csf_single_track_points_ignores_non_matching_filter(track_points):
    f = DummyFilter(name="test", iri="iri://nope")
    helpers = GeoCSFTrackPointHelpers([f])
    ancestor_iris = {"iri://different"}
    result = helpers.csf_single_track_points(ancestor_iris, track_points, uuid4())

    assert result == track_points


class DummyFilterDelta(CommonSenseFilter):
    def filter_point_deltas(self, pts):
        return pts[:-1]  # drop last


def test_csf_track_point_deltas_applies_filter(track_points):
    track = Track(
        points=track_points,
        node_id=uuid4(),
        algorithm="algo",
        observation_ids=[p.observation_id for p in track_points],
        acm=DEFAULT_ACM,
    )

    f = DummyFilterDelta(name="delta", iri="iri://match")
    helpers = GeoCSFTrackPointHelpers([f])
    ancestor_iris = {"iri://match"}
    out = helpers.csf_track_point_deltas(ancestor_iris, uuid4(), track)

    assert len(out.points) == len(track_points) - 1
