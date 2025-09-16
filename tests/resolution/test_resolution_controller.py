"""Resolution Controller Unit Tests"""

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Action, AttributeAttribute, ObjectType

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.error_loggers import ErrorLogger, RethrowErrorLogger
from oms_sensemaking.core.events import AuditLogEvent, RabbitMQListener
from oms_sensemaking.resolution.controllers import (
    ResolutionQueueFilter,
    ResolutionSensemaker,
    ResolutionSensemakerController,
)


@pytest.fixture
def mock_res_controller():
    controller = ResolutionSensemakerController(
        RabbitMQListener("ResolutionRMQListener", SETTINGS.rmq_res_queue_name, event_filter=ResolutionQueueFilter()),
        RethrowErrorLogger(ErrorLogger()),
    )
    return controller


@mock.patch("oms_sensemaking.core.controllers.as_completed")
@mock.patch("oms_sensemaking.core.controllers.ThreadPoolExecutor")
def test_res_controller(
    mock_executor: ThreadPoolExecutor, mock_as_completed: Callable, mock_res_controller: ResolutionSensemakerController
):
    # set duplicate object iris dictionary
    with open(SETTINGS.duplicate_object_iris_file_path) as fd:
        duplicate_object_iris = json.load(fd)
    # register the sensemaker without starting the listener
    mock_res_controller.register(
        "resolution", ResolutionSensemaker(duplicate_object_iris, mock_res_controller.oms_crud_tool)
    )

    # mock oms call
    oms_attribute = AttributeAttribute.model_construct(
        id=uuid4(), attributeIri="test", attributeValue="test", nodeId=uuid4(), sourceId=uuid4(), acm=DEFAULT_ACM
    )

    mock_res_controller.oms_crud_tool.get_attribute = mock.MagicMock()
    mock_res_controller.oms_crud_tool.get_attribute.return_value = oms_attribute

    # mock thread pool execution

    # Create a mock executor that returns a future with a known result
    instance = mock.MagicMock()
    mock_executor.return_value.__enter__.return_value = instance
    mock_as_completed.return_value = []

    audit_event = AuditLogEvent(
        userId="test",
        objectId=oms_attribute.id,
        objectType=ObjectType.ATTRIBUTE,
        action=Action.CREATE,
    )
    mock_res_controller.handle_event(audit_event)

    mock_res_controller.oms_crud_tool.get_attribute.assert_called_with(oms_attribute.id)
    instance.submit.assert_called_with(mock_res_controller._registry["resolution"].execute, oms_attribute)


def test_start_registers_resolution_sensemaker_when_enabled(mock_res_controller):
    fake_duplicate_data = {"obj1": ["dup1", "dup2"]}

    with (
        mock.patch("oms_sensemaking.config.SETTINGS") as settings_mock,
        mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(fake_duplicate_data))),
        mock.patch.object(mock_res_controller, "register") as register_mock,
        mock.patch("oms_sensemaking.resolution.controllers.ResolutionSensemaker") as sensemaker_mock,
        mock.patch.object(SensemakerController, "start", autospec=True) as super_start_mock,
    ):
        # configure settings
        settings_mock.enable_resolution_sensemaker = True
        settings_mock.duplicate_object_iris_file_path = "fake.json"

        mock_res_controller.start()

        # Verify ResolutionSensemaker was created with correct args
        sensemaker_mock.assert_called_once_with(fake_duplicate_data, mock_res_controller.oms_crud_tool)

        # Verify register called
        register_mock.assert_called_once_with("resolution", sensemaker_mock.return_value)

        # Verify super().start() called
        super_start_mock.assert_called_once_with(mock_res_controller)


def test_start_does_nothing_when_disabled(mock_res_controller):
    with (
        mock.patch("oms_sensemaking.config.SETTINGS") as settings_mock,
        mock.patch.object(mock_res_controller, "register") as register_mock,
        mock.patch.object(ResolutionSensemakerController, "start", autospec=True) as super_start_mock,
    ):
        settings_mock.enable_resolution_sensemaker = False

        mock_res_controller.start()

        register_mock.assert_not_called()
        super_start_mock.assert_called_once_with(mock_res_controller)


def test_passes_filter_returns_true_for_handled_event():
    filt = ResolutionQueueFilter()

    event = AuditLogEvent(
        userId="user1", objectId=uuid4(), objectType=ObjectType.ATTRIBUTE.value, action=Action.CREATE.value
    )

    assert filt.passes_filter(event) is True


@pytest.mark.parametrize(
    "obj_type,action",
    [
        ("not-handled", Action.CREATE.value),
        (ObjectType.ATTRIBUTE.value, "not-handled"),
        ("not-handled", "not-handled"),
    ],
)
def test_passes_filter_returns_false_for_unhandled(obj_type, action):
    filt = ResolutionQueueFilter()

    event = AuditLogEvent(userId="user1", objectId=uuid4(), objectType=obj_type, action=action)

    assert filt.passes_filter(event) is False
