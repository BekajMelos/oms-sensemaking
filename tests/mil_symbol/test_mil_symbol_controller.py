"""MilSymbol Controller Unit Tests"""

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Action, NodeNode, ObjectType

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.events import AuditLogEvent, SQSListener
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.mil_symbol.controllers import (
    MilSymbolQueueFilter,
    MilSymbolSensemaker,
    MilSymbolSensemakerController,
)


@pytest.fixture
def mock_mil_sym_controller():
    controller = MilSymbolSensemakerController(
        SQSListener("MilSymbolSQSListener", SETTINGS.sqs_res_queue_url, event_filter=MilSymbolQueueFilter())
    )
    return controller


@mock.patch("oms_sensemaking.core.controllers.as_completed")
@mock.patch("oms_sensemaking.core.controllers.ThreadPoolExecutor")
def test_mil_sym_controller(
    mock_executor: ThreadPoolExecutor,
    mock_as_completed: Callable,
    mock_mil_sym_controller: MilSymbolSensemakerController,
    mil_symbol_rules: Dict,
):
    # register the sensemaker without starting the listener
    mock_mil_sym_controller.register("mil_symbol", MilSymbolSensemaker(OmsCrudTool(), mil_symbol_rules))

    # mock oms call
    oms_node = NodeNode.model_construct(id=uuid4(), name="test", sourceId=uuid4(), acm=DEFAULT_ACM)
    mock_mil_sym_controller.oms_crud_tool.get_node = mock.MagicMock()
    mock_mil_sym_controller.oms_crud_tool.get_node.return_value = oms_node

    # mock thread pool execution

    # Create a mock executor that returns a future with a known result
    instance = mock.MagicMock()
    mock_executor.return_value.__enter__.return_value = instance
    mock_as_completed.return_value = []

    audit_event = AuditLogEvent(
        userId="test",
        objectId=oms_node.id,
        objectType=ObjectType.NODE,
        action=Action.CREATE,
    )
    mock_mil_sym_controller.handle_event(audit_event)

    mock_mil_sym_controller.oms_crud_tool.get_node.assert_called_with(oms_node.id)
    instance.submit.assert_called_with(mock_mil_sym_controller._registry["mil_symbol"].execute, oms_node)
