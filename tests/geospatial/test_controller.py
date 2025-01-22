"""Geo Controller Unit Tests"""

import logging
from unittest import mock
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.events import SQSListener
from oms_sensemaking.geospatial.controllers import GeoQueueFilter, GeospatialSensemakerController


@pytest.fixture
def mock_geo_controller(mock_oms_client):
    controller = GeospatialSensemakerController(
        SQSListener("geo test queue listener", SETTINGS.sqs_geo_queue_url, event_filter=GeoQueueFilter())
    )
    controller.oms_crud_tool.oms_client = mock_oms_client
    return controller


def test_node_version_attribute_error(mocker: MockerFixture, mock_geo_controller, caplog):
    # This is what we want returned from get_oms_observation. We only need the nodeId
    mock_observation = mock.Mock()
    mock_observation.nodeId = uuid4()

    # We will pass this into the handle_event function. We only care about objectId
    mock_object_event = mock.Mock()
    mock_object_event.objectId = uuid4()

    # This method is hit during handle_event and it's nodeId is needed
    mocker.patch.object(mock_geo_controller, "get_oms_observation").return_value = mock_observation

    # This method is hit during handle_event to get the associated node from the db
    # In this case, we want to return None to check that an AttributeError is raised
    mocker.patch.object(mock_geo_controller.oms_crud_tool.oms_client, "node").return_value = None

    # Set the logger level to WARNING. This is the level we are sending our AttributeError message
    caplog.set_level(logging.WARNING)

    # Run handle_event with our mock_object_event from above. Should render False
    handled = mock_geo_controller.handle_event(mock_object_event)

    # Assertions
    assert "No node found. Unable to process observation." in caplog.text
    assert not handled
