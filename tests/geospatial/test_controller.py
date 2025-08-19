"""Geo Controller Unit Tests"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Callable
from unittest import mock
from uuid import uuid4

import pytest
import shapely
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Confidence, NodeNode, SourceSource
from pytest_mock import MockerFixture

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.error_loggers import ErrorLogger, RethrowErrorLogger
from oms_sensemaking.core.events import RabbitMQListener
from oms_sensemaking.core.exceptions import TrackLengthError
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.dao.track import APITrack
from oms_sensemaking.geospatial.controllers import GeoQueueFilter, GeospatialSensemakerController
from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker
from oms_sensemaking.models.geo import Point, Track


@pytest.fixture
def mock_geo_controller(mock_oms_client):
    controller = GeospatialSensemakerController(
        RabbitMQListener("geo test queue listener", SETTINGS.rmq_geo_queue_name, event_filter=GeoQueueFilter()),
        RethrowErrorLogger(ErrorLogger()),
    )
    controller.oms_crud_tool.oms_client = mock_oms_client

    # disable autoflush so that flush_buffer doesn't go on forever. Without this the tests never end
    controller.autoflush_enabled = False
    return controller


def test_node_version_attribute_error(mocker: MockerFixture, mock_geo_controller, caplog):
    # This is what we want returned from get_oms_observation. We only need the nodeId
    mock_observation = mock.Mock()
    mock_observation.nodeId = uuid4()
    mock_observation.labels = []

    # We will pass this into the handle_event function. We only care about objectId
    mock_audit_log_event = mock.Mock()
    mock_audit_log_event.objectId = uuid4()

    # This method is hit during handle_event and it's nodeId is needed
    mocker.patch.object(mock_geo_controller, "get_oms_observation").return_value = mock_observation

    # This method is hit during handle_event to get the associated node from the db
    # In this case, we want to return None to check that an AttributeError is raised
    mocker.patch.object(mock_geo_controller.oms_crud_tool.oms_client, "node").return_value = None

    # Set the logger level to WARNING. This is the level we are sending our AttributeError message
    caplog.set_level(logging.WARNING)

    # Run handle_event with our mock_audit_log_event from above. Should render False
    handled = mock_geo_controller.handle_event(mock_audit_log_event)

    # Assertions
    assert "No node found. Unable to process observation." in caplog.text
    assert not handled


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


@mock.patch("oms_sensemaking.geospatial.controllers.Track.get_or_create")
@mock.patch("oms_sensemaking.geospatial.controllers.APITrack")
@mock.patch("oms_sensemaking.geospatial.controllers.aac_client")
@mock.patch("oms_sensemaking.models.geo.aac_client")
@mock.patch("oms_sensemaking.geospatial.controllers.as_completed")
@mock.patch("oms_sensemaking.geospatial.controllers.ThreadPoolExecutor")
def test_geo_controller_config(
    mock_executor: ThreadPoolExecutor,
    mock_as_completed: Callable,
    mock_aac_client1: AacClient,
    mock_aac_client2: AacClient,
    mock_api_track_client: APITrack,
    mock_track_get_or_create: Callable,
    mock_geo_controller: GeospatialSensemakerController,
    default_aircraft_config: dict,
    default_watercraft_config: dict,
    provider_1_aircraft_config: dict,
    source1: SourceSource,
    source2: SourceSource,
    oms_node: NodeNode,
    track_points: list[Point],
):
    # register the sensemaker without starting the listener
    mock_geo_controller.register("geo", CotravelSensemaker(OmsCrudTool()))

    mock_geo_controller.oms_crud_tool.get_node = mock.MagicMock(return_value=oms_node)

    source_irrelevant_provider = source1
    source_relevant_provider = source2
    mock_geo_controller.oms_crud_tool.get_source = mock.MagicMock(return_value=source_irrelevant_provider)

    # mock track creation
    track_uuid = uuid4()
    track = Track(DEFAULT_ACM, track_points, uuid4(), "", [], track_uuid)

    mock_track_get_or_create.return_value = (track, None)

    # set up track buffer
    mock_geo_controller.track_node_buffer = {track_uuid: track_points}
    mock_geo_controller.track_times = {track_uuid: datetime.now(tz=timezone.utc) - timedelta(days=1)}
    mock_geo_controller.get_node_ancestors_iris = mock.MagicMock(return_value=set())
    mock_api_track_client.create_oms_track = mock.MagicMock()

    # mock thread pool execution
    # Create a mock executor that returns a future with a known result
    instance = mock.MagicMock()
    mock_executor.return_value.__enter__.return_value = instance
    mock_as_completed.return_value = []

    # mock execute function
    mock_geo_controller._registry["geo"].execute = mock.MagicMock()

    # Test Watercraft without relevant provider
    # call flush buffer
    mock_geo_controller.flush_buffer()

    # Ensure that the default watercraft config is used
    instance.submit.assert_called_with(mock_geo_controller._registry["geo"].execute, track, default_watercraft_config)

    # Test Aircraft without relevant provider
    # mock oms call. Set classIri to aircraft
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"
    mock_geo_controller.oms_crud_tool.get_node = mock.MagicMock(return_value=oms_node)
    # set up track buffer
    mock_geo_controller.track_node_buffer = {track_uuid: track_points}
    mock_geo_controller.track_times = {track_uuid: datetime.now(tz=timezone.utc) - timedelta(days=1)}
    mock_geo_controller.get_node_ancestors_iris = mock.MagicMock(return_value=set())
    mock_api_track_client.create_oms_track = mock.MagicMock()

    instance.reset_mock()

    # call flush buffer
    mock_geo_controller.flush_buffer()

    # Ensure that the default aircraft config is used
    instance.submit.assert_called_with(mock_geo_controller._registry["geo"].execute, track, default_aircraft_config)
    mock_geo_controller.oms_crud_tool.get_source.assert_called_with(source_id=str(source_irrelevant_provider.id))

    # Test Aircraft with relevant provider
    mock_geo_controller.oms_crud_tool.get_source = mock.MagicMock(return_value=source_relevant_provider)
    mock_geo_controller.oms_crud_tool.get_node = mock.MagicMock(return_value=oms_node)
    # set up track buffer
    mock_geo_controller.track_node_buffer = {track_uuid: track_points}
    mock_geo_controller.track_times = {track_uuid: datetime.now(tz=timezone.utc) - timedelta(days=1)}
    mock_geo_controller.get_node_ancestors_iris = mock.MagicMock(return_value=set())
    mock_api_track_client.create_oms_track = mock.MagicMock()

    instance.reset_mock()

    # call flush buffer
    mock_geo_controller.flush_buffer()

    # Ensure that the provider_1 aircraft config is used
    instance.submit.assert_called_with(mock_geo_controller._registry["geo"].execute, track, provider_1_aircraft_config)

    # Ensure provider id is fetched from most recent observation
    mock_geo_controller.oms_crud_tool.get_source.assert_called_with(source_id=str(source_irrelevant_provider.id))


@mock.patch("oms_sensemaking.geospatial.controllers.aac_client")
@mock.patch("oms_sensemaking.models.geo.aac_client")
@mock.patch("oms_sensemaking.geospatial.controllers.as_completed")
@mock.patch("oms_sensemaking.geospatial.controllers.ThreadPoolExecutor")
def test_track_too_short1(
    mock_executor: ThreadPoolExecutor,
    mock_as_completed: Callable,
    mock_aac_client1: AacClient,
    mock_aac_client2: AacClient,
    mock_geo_controller: GeospatialSensemakerController,
    source1: SourceSource,
    oms_node: NodeNode,
    track_points: list[Point],
    caplog,
):
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
    mock_geo_controller.get_node_ancestors_iris = mock.MagicMock(return_value=set())

    # mock execute function
    mock_geo_controller._registry["geo"].execute = mock.MagicMock()

    # call flush buffer
    mock_geo_controller.flush_buffer()
    assert caplog.records[-1].message == (
        "Track doesn't have enough points. Ignore and remove from buffer until it gets more points"
    )


@mock.patch("oms_sensemaking.geospatial.controllers.aac_client")
@mock.patch("oms_sensemaking.models.geo.aac_client")
@mock.patch("oms_sensemaking.geospatial.controllers.as_completed")
@mock.patch("oms_sensemaking.geospatial.controllers.ThreadPoolExecutor")
def test_generate_track_too_short(
    mock_executor: ThreadPoolExecutor,
    mock_as_completed: Callable,
    mock_aac_client1: AacClient,
    mock_aac_client2: AacClient,
    mock_geo_controller: GeospatialSensemakerController,
    source1: SourceSource,
    oms_node: NodeNode,
    track_points: list[Point],
):
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
    mock_geo_controller.get_node_ancestors_iris = mock.MagicMock(return_value=set())

    # call flush buffer. Should raise exception
    with pytest.raises(TrackLengthError):
        mock_geo_controller._generate_track(track_uuid=track_uuid)
