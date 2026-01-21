"""Geo Controller Unit Tests"""

import logging
import threading
from datetime import datetime, timedelta, timezone
from unittest import mock
from uuid import uuid4

import pytest
import shapely
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Confidence, NodeNode, ObservationObservation, SourceSource
from pytest_mock import MockerFixture

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.ontology_client import OntologyClient
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.error_loggers import ErrorLogger, RethrowErrorLogger
from oms_sensemaking.core.events import RabbitMQListener
from oms_sensemaking.core.exceptions import TrackLengthError
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.controllers import GeoQueueFilter, GeospatialSensemakerController
from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker
from oms_sensemaking.models.geo import Point, Track


@pytest.fixture
def mock_geo_controller(mock_oms_client):
    controller = GeospatialSensemakerController(
        RabbitMQListener(
            "geo test queue listener",
            SETTINGS.rmq_geo_queue_name,
            SETTINGS.queue_worker_threads,
            event_filter=GeoQueueFilter(),
        ),
        RethrowErrorLogger(ErrorLogger()),
        OntologyClient(mock_oms_client),
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
def oms_node() -> NodeNode:
    return NodeNode.model_construct(
        id=uuid4(),
        name="test",
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft",
        acm=DEFAULT_ACM,
    )


@pytest.fixture
def track_points(source1, oms_node) -> list[Point]:
    # unimportant point
    points = [
        Point(
            acm=DEFAULT_ACM,
            location=shapely.Point(-0.030890, 51.509420).wkt,
            altitude=None,
            detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
            node_id=oms_node.id,
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
            node_id=oms_node.id,
            node_version=1,
            observation_id=uuid4(),
            observation_version=1,
            source_id=source1.id,
            observation_confidence=Confidence.HIGH,
        ),
    ]
    return points


@mock.patch("oms_sensemaking.geospatial.controllers.as_completed")
@mock.patch("oms_sensemaking.geospatial.controllers.ThreadPoolExecutor")
def test_geo_controller_with_default_provider_config(
    mock_executor: mock.MagicMock,
    mock_as_completed: mock.MagicMock,
    mock_geo_controller: GeospatialSensemakerController,
    default_aircraft_config: dict,
    default_watercraft_config: dict,
    source1: SourceSource,
    oms_node: NodeNode,
    track_points: list[Point],
):
    # register the sensemaker without starting the listener
    mock_geo_controller.register("geo", CotravelSensemaker(OmsCrudTool()))

    mock_geo_controller.oms_crud_tool.get_node = mock.MagicMock(return_value=oms_node)

    source_irrelevant_provider = source1
    mock_geo_controller.oms_crud_tool.get_source = mock.MagicMock(return_value=source_irrelevant_provider)

    # mock track creation
    track_uuid = uuid4()
    track = Track(
        acm=DEFAULT_ACM,
        points=track_points,
        node_id=oms_node.id,
        algorithm="",
        observation_ids=[],
        track_uuid=track_uuid,
        provider_id=source1.providerId,
    )

    # set up track buffer
    mock_geo_controller.track_node_buffer = {track_uuid: track_points}
    mock_geo_controller.track_times = {track_uuid: datetime.now(tz=timezone.utc) - timedelta(days=1)}
    t = Track(
        acm=DEFAULT_ACM,
        points=track_points,
        node_id=oms_node.id,
        algorithm="",
        observation_ids=[],
        track_uuid=track.track_uuid,
        provider_id=source1.providerId,
    )
    mock_geo_controller._track_generator.generate_track = mock.MagicMock(return_value=[t])

    # mock thread pool execution
    # Create a mock executor that returns a future with a known result
    instance = mock.MagicMock()
    mock_executor.return_value.__enter__.return_value = instance
    mock_as_completed.return_value = []

    # mock execute function
    mock_geo_controller._registry["geo"].execute = mock.MagicMock()
    #### End of Common Setup Code ####

    #### Start First Code Under Test ####
    # Test Watercraft without relevant provider
    # call flush buffer
    mock_geo_controller.flush_buffer()

    # Ensure that the default watercraft config is used
    instance.submit.assert_called_with(mock_geo_controller._registry["geo"].execute, track, default_watercraft_config)
    #### End First Code Under Test ####

    #### start of test 2 ####
    # Test Aircraft without relevant provider
    # mock atoms call. Set classIri to aircraft
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"
    mock_geo_controller.oms_crud_tool.get_node = mock.MagicMock(return_value=oms_node)
    # set up track buffer
    mock_geo_controller.track_node_buffer = {track_uuid: track_points}
    mock_geo_controller.track_times = {track_uuid: datetime.now(tz=timezone.utc) - timedelta(days=1)}

    instance.reset_mock()

    # call flush buffer
    mock_geo_controller.flush_buffer()

    # Ensure that the default aircraft config is used
    instance.submit.assert_called_with(mock_geo_controller._registry["geo"].execute, track, default_aircraft_config)
    mock_geo_controller.oms_crud_tool.get_source.assert_called_with(source_id=str(source_irrelevant_provider.id))


@mock.patch("oms_sensemaking.geospatial.controllers.as_completed")
@mock.patch("oms_sensemaking.geospatial.controllers.ThreadPoolExecutor")
def test_geo_controller_with_provider_config(
    mock_executor: mock.MagicMock,
    mock_as_completed: mock.MagicMock,
    mock_geo_controller: GeospatialSensemakerController,
    provider_1_aircraft_config: dict,
    source1: SourceSource,
    source2: SourceSource,
    oms_node: NodeNode,
    track_points: list[Point],
):
    # register the sensemaker without starting the listener
    mock_geo_controller.register("geo", CotravelSensemaker(OmsCrudTool()))

    source_irrelevant_provider = source1
    source_relevant_provider = source2

    # mock track creation
    track_uuid = uuid4()
    track = Track(
        acm=DEFAULT_ACM,
        points=track_points,
        node_id=oms_node.id,
        algorithm="",
        observation_ids=[],
        track_uuid=track_uuid,
        provider_id=source2.providerId,
    )

    # set up track buffer
    mock_geo_controller.track_node_buffer = {track_uuid: track_points}
    mock_geo_controller.track_times = {track_uuid: datetime.now(tz=timezone.utc) - timedelta(days=1)}

    # mock thread pool execution
    # Create a mock executor that returns a future with a known result
    instance = mock.MagicMock()
    mock_executor.return_value.__enter__.return_value = instance
    mock_as_completed.return_value = []

    # mock execute function
    mock_geo_controller._registry["geo"].execute = mock.MagicMock()

    # Test Aircraft with relevant provider
    oms_node.classIri = "http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft"
    mock_geo_controller.oms_crud_tool.get_source = mock.MagicMock(return_value=source_relevant_provider)
    mock_geo_controller.oms_crud_tool.get_node = mock.MagicMock(return_value=oms_node)

    t = Track(
        acm=DEFAULT_ACM,
        points=track_points,
        node_id=oms_node.id,
        algorithm="",
        observation_ids=[],
        track_uuid=track.track_uuid,
        provider_id=source2.providerId,
    )
    mock_geo_controller._track_generator.generate_track = mock.MagicMock(return_value=[t])

    # call flush buffer
    mock_geo_controller.flush_buffer()

    # Ensure that the provider_1 aircraft config is used
    instance.submit.assert_called_with(mock_geo_controller._registry["geo"].execute, track, provider_1_aircraft_config)

    # Ensure provider id is fetched from most recent observation
    mock_geo_controller.oms_crud_tool.get_source.assert_called_with(source_id=str(source_irrelevant_provider.id))


@mock.patch("oms_sensemaking.models.geo.aac_client")
def test_track_too_short1(
    mock_aac_client1: AacClient,
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
    mock_geo_controller._track_generator.get_node_ancestors_iris = mock.MagicMock(return_value=set())

    # mock execute function
    mock_geo_controller._registry["geo"].execute = mock.MagicMock()

    # call flush buffer
    mock_geo_controller.flush_buffer()
    assert caplog.records[-1].message == (f"Track {track_uuid} doesn't have enough points; removing from buffer.")


def test_observations_can_make_tracks(mocker: MockerFixture, mock_geo_controller: GeospatialSensemakerController):
    mock_obs = mocker.MagicMock(spec=ObservationObservation)
    mock_obs.geometry = {"type": "point", "coordinates": [2.3522, 48.8566]}
    mock_geo_controller.oms_crud_tool.get_observation = mocker.Mock(spec=ObservationObservation, return_value=mock_obs)
    obs = mock_geo_controller.get_oms_observation("some-id")
    assert obs == mock_obs


def test_handle_event_skips_generated_tracks(mocker, mock_geo_controller):
    event = mocker.Mock()
    event.objectId = uuid4()

    obs = mocker.Mock()
    obs.nodeId = uuid4()
    obs.labels = [SETTINGS.sm_connected_track]
    mocker.patch.object(mock_geo_controller, "get_oms_observation", return_value=obs)

    handled = mock_geo_controller.handle_event(event)
    assert handled is True


def test_handle_event_no_observation_returns_true(mocker, mock_geo_controller):
    event = mocker.Mock()
    event.objectId = uuid4()
    mocker.patch.object(mock_geo_controller, "get_oms_observation", return_value=None)

    result = mock_geo_controller.handle_event(event)
    assert result is True


def test_handle_event_missing_geometry(mocker, mock_geo_controller, caplog):
    event = mocker.Mock()
    event.objectId = uuid4()

    obs = mocker.Mock()
    obs.nodeId = uuid4()
    obs.labels = []
    mocker.patch.object(mock_geo_controller, "get_oms_observation", return_value=obs)
    mocker.patch("oms_sensemaking.geospatial.controllers.decompose_observation_geometry", return_value=None)

    handled = mock_geo_controller.handle_event(event)
    assert handled is False
    assert "No geometry found for observation" in caplog.text


def test_handle_event_adds_point_successfully(mocker, mock_geo_controller):
    event = mocker.Mock()
    event.objectId = uuid4()

    obs = mocker.Mock()
    obs.nodeId = uuid4()
    obs.id = uuid4()
    obs.sourceId = uuid4()
    obs.version = 1
    obs.confidence = "HIGH"
    obs.acm = DEFAULT_ACM
    obs.labels = []
    mocker.patch.object(mock_geo_controller, "get_oms_observation", return_value=obs)

    mocker.patch(
        "oms_sensemaking.geospatial.controllers.decompose_observation_geometry",
        return_value=[{"coordinates": [0, 0], "detection_time": datetime.now(timezone.utc)}],
    )

    node = mocker.Mock(version=1)
    mock_geo_controller.oms_crud_tool.get_node = mocker.Mock(return_value=node)
    mocker.patch(
        "oms_sensemaking.models.geo.Point.get_or_create", return_value=(mock.Mock(observation_id=uuid4()), True)
    )

    success = mock_geo_controller.handle_event(event)
    assert success
    assert mock_geo_controller.track_node_buffer


def test_concurrent_flush_buffer_thread_safety(mock_geo_controller):
    # prepare buffer with several tracks
    for _ in range(10):
        track_uuid = uuid4()
        mock_geo_controller.track_times[track_uuid] = datetime.now(tz=timezone.utc) - timedelta(seconds=999)
        mock_geo_controller.track_node_buffer[track_uuid] = []

    threads = [threading.Thread(target=mock_geo_controller.flush_buffer) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All expired tracks should be processed & cleaned
    assert all(v is None for v in mock_geo_controller.track_times.values())


def test_lock_is_used_during_flush_buffer(mocker, mock_geo_controller):
    class SpyLock:
        def __init__(self, real_lock):
            self.real_lock = real_lock
            self.enter_called = False

        def __enter__(self):
            self.enter_called = True
            return self.real_lock.__enter__()

        def __exit__(self, *args):
            return self.real_lock.__exit__(*args)

    spy_lock = SpyLock(threading.Lock())
    mock_geo_controller.lock = spy_lock

    mock_geo_controller.flush_buffer()

    assert spy_lock.enter_called, "Expected flush_buffer() to use the lock"


def test_process_track_too_short_triggers_cleanup(mocker, mock_geo_controller):
    track_uuid = uuid4()
    mock_geo_controller._track_generator.generate_track = mocker.Mock(side_effect=TrackLengthError)

    # populate shared dicts
    mock_geo_controller.track_times[track_uuid] = datetime.now(tz=timezone.utc)
    mock_geo_controller.track_node_buffer[track_uuid] = []
    mock_geo_controller.node_track_mapping[uuid4()] = track_uuid

    result = mock_geo_controller._process_track(track_uuid)

    assert result is False
    assert track_uuid in mock_geo_controller.track_times
    assert mock_geo_controller.track_times[track_uuid] is None


def test_process_track_handles_unexpected_exception(mocker, mock_geo_controller):
    track_uuid = uuid4()
    mock_geo_controller._track_generator.generate_track = mocker.Mock(side_effect=RuntimeError("fail"))

    mock_geo_controller.track_times[track_uuid] = datetime.now(tz=timezone.utc)
    mock_geo_controller.track_node_buffer[track_uuid] = []
    mock_geo_controller.node_track_mapping[uuid4()] = track_uuid

    mock_geo_controller._process_track(track_uuid)
    assert track_uuid in mock_geo_controller.track_times
    assert mock_geo_controller.track_times[track_uuid] is None
