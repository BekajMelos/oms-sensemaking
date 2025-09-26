"""Geo Controller Unit Tests"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Callable
from unittest import mock
from uuid import uuid4

import pytest
import shapely
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Confidence, NodeNode, SourceSource

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.ontology_client import OntologyClient
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.error_loggers import ErrorLogger, RethrowErrorLogger
from oms_sensemaking.core.events import RabbitMQListener
from oms_sensemaking.core.exceptions import TrackLengthError
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.controllers import GeoQueueFilter, GeospatialSensemakerController
from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker
from oms_sensemaking.geospatial.track_generator import TrackGenerator
from oms_sensemaking.models.geo import NaiveTrackWeaver, Point


@pytest.fixture
def mock_geo_controller(mock_oms_client):
    controller = GeospatialSensemakerController(
        RabbitMQListener("geo test queue listener", SETTINGS.rmq_geo_queue_name, event_filter=GeoQueueFilter()),
        RethrowErrorLogger(ErrorLogger()),
        OntologyClient(mock_oms_client),
    )
    controller.oms_crud_tool.oms_client = mock_oms_client

    # disable autoflush so that flush_buffer doesn't go on forever. Without this the tests never end
    controller.autoflush_enabled = False
    return controller


@pytest.fixture
def source1() -> SourceSource:
    source_id = uuid4()
    source1 = SourceSource.model_construct(id=source_id, providerId="00000000-0000-0000-0000-000000000000")
    return source1


@pytest.fixture
def source2() -> SourceSource:
    source_id_2 = uuid4()
    source2 = SourceSource.model_construct(id=source_id_2, providerId="11111111-1111-1111-1111-111111111111")
    return source2


@pytest.fixture
def oms_node(source1) -> NodeNode:
    return NodeNode.model_construct(
        id=uuid4(),
        name="test",
        sourceId=source1.id,
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft",
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def track_points(source1) -> list[Point]:
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
            source_id=source1.id,
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
            source_id=source1.id,
            observation_confidence=Confidence.HIGH,
        ),
    ]
    return points


@mock.patch("oms_sensemaking.models.geo.aac_client")
@mock.patch("oms_sensemaking.geospatial.controllers.as_completed")
@mock.patch("oms_sensemaking.geospatial.controllers.ThreadPoolExecutor")
def test_generate_track_too_short(
    mock_executor: ThreadPoolExecutor,
    mock_as_completed: Callable,
    mock_aac_client1: AacClient,
    mock_geo_controller: GeospatialSensemakerController,
    source1: SourceSource,
    oms_node: NodeNode,
    track_points: list[Point],
):
    track_generator = TrackGenerator(OntologyClient(OmsCrudTool()))
    # register the sensemaker without starting the listener
    mock_geo_controller.register("geo", CotravelSensemaker(OmsCrudTool()))

    mock_geo_controller.oms_crud_tool.get_node = mock.MagicMock(return_value=oms_node)
    mock_geo_controller.oms_crud_tool.get_source = mock.MagicMock(return_value=source1)

    # mock track creation
    track_uuid = uuid4()

    # only 1 point
    track_points = track_points[:1]

    # set up track buffer
    mock_geo_controller.track_node_buffer = {track_uuid: track_points}
    mock_geo_controller.track_times = {track_uuid: datetime.now(tz=timezone.utc) - timedelta(days=1)}
    track_generator.get_node_ancestors_iris = mock.MagicMock(return_value=set())

    # call flush buffer. Should raise exception
    with pytest.raises(TrackLengthError):
        track_generator.generate_track(
            track_uuid, NaiveTrackWeaver(), [], {track_uuid: track_points}, mock_geo_controller.oms_crud_tool
        )
