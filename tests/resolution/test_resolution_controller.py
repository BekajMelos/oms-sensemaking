"""Resolution Controller Unit Tests"""

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Action, AttributeAttribute, ObjectType

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.events import AuditLogEvent, SQSListener
from oms_sensemaking.resolution.controllers import (
    ResolutionQueueFilter,
    ResolutionSensemaker,
    ResolutionSensemakerController,
)


@pytest.fixture
def mock_res_controller():
    controller = ResolutionSensemakerController(
        SQSListener("ResolutionSQSListener", SETTINGS.sqs_res_queue_url, event_filter=ResolutionQueueFilter())
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
    mock_res_controller.register("resolution", ResolutionSensemaker(duplicate_object_iris,
                                                                    mock_res_controller.oms_crud_tool))

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
