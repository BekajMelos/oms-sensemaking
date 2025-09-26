"""Geo Controller Unit Tests"""

from datetime import datetime
from unittest import mock
from uuid import uuid4

import pytest
import shapely
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Confidence, NodeNode, SourceSource

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.ontology_client import OntologyClient
from oms_sensemaking.core.exceptions import TrackLengthError
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.track_generator import TrackGenerator
from oms_sensemaking.models.geo import NaiveTrackWeaver, Point


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


@mock.patch("oms_sensemaking.models.geo.aac_client")
def test_generate_track_too_short(mock_aac_client: AacClient, mock_oms_client, track_points: list[Point], oms_node):
    track_generator = TrackGenerator(OntologyClient(OmsCrudTool()))

    mock_oms_client.get_node = mock.MagicMock(return_value=oms_node)

    # mock track creation
    track_uuid = uuid4()

    # only 1 point
    track_points = track_points[:1]

    track_generator.get_node_ancestors_iris = mock.MagicMock(return_value=set())

    # call flush buffer. Should raise exception
    with pytest.raises(TrackLengthError):
        track_generator.generate_track(track_uuid, NaiveTrackWeaver(), [], {track_uuid: track_points}, mock_oms_client)
