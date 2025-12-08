"""MilSymbol Controller Unit Tests"""

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict
from unittest import mock
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Action, AttributeAttribute, NodeNode, ObjectType

from oms_sensemaking.clients.ontology_client import OntologyClient
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.error_loggers import ErrorLogger, RethrowErrorLogger
from oms_sensemaking.core.event_model import AuditLogHeaders
from oms_sensemaking.core.events import AuditLogEvent, RabbitMQListener
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.mil_symbol.controllers import (
    MilSymbolQueueFilter,
    MilSymbolSensemaker,
    MilSymbolSensemakerController,
)
from oms_sensemaking.mil_symbol.get_attributes import GetMilSymbolAttributeFactory


@pytest.fixture
def mock_mil_sym_controller():
    controller = MilSymbolSensemakerController(
        RabbitMQListener(
            "MilSymbolRMQListener",
            SETTINGS.rmq_res_queue_name,
            SETTINGS.queue_worker_threads,
            event_filter=MilSymbolQueueFilter(),
        ),
        RethrowErrorLogger(ErrorLogger()),
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
    oms_client = OmsCrudTool()
    # register the sensemaker without starting the listener
    mock_mil_sym_controller.register(
        "mil_symbol",
        MilSymbolSensemaker(
            oms_client,
            mil_symbol_rules,
            OntologyClient(oms_client),
            GetMilSymbolAttributeFactory(oms_client).get_attribute_retriever(
                SETTINGS.mil_symbol_settings.mil_sym_attr_retriever
            ),
        ),
    )

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

    # test attribute
    oms_attribute = AttributeAttribute.model_construct(
        id=uuid4(), nodeId=oms_node.id, sourceId=uuid4(), acm=DEFAULT_ACM
    )
    mock_mil_sym_controller.oms_crud_tool.get_attribute = mock.MagicMock()
    mock_mil_sym_controller.oms_crud_tool.get_attribute.return_value = oms_attribute

    instance = mock.MagicMock()
    mock_executor.return_value.__enter__.return_value = instance
    mock_as_completed.return_value = []

    audit_event_attribute = AuditLogEvent(
        userId="test",
        objectId=oms_attribute.id,
        objectType=ObjectType.ATTRIBUTE,
        action=Action.UPDATE,
    )
    mock_mil_sym_controller.handle_event(audit_event_attribute)

    mock_mil_sym_controller.oms_crud_tool.get_attribute.assert_called_with(oms_attribute.id)
    instance.submit.assert_called_with(mock_mil_sym_controller._registry["mil_symbol"].execute, oms_attribute)


def test_start_registers_resolution_sensemaker_when_enabled(mock_mil_sym_controller):
    fake_mil_rules = {"mil": {"stuff": {"other stuff": "boom"}}}

    with (
        mock.patch("oms_sensemaking.config.SETTINGS.mil_symbol_settings") as settings_mock,
        mock.patch("builtins.open", mock.mock_open(read_data=json.dumps(fake_mil_rules))),
        mock.patch.object(mock_mil_sym_controller, "register") as register_mock,
        mock.patch("oms_sensemaking.mil_symbol.controllers.MilSymbolSensemaker") as sensemaker_mock,
        mock.patch.object(SensemakerController, "start", autospec=True) as super_start_mock,
    ):
        # configure settings
        settings_mock.enable_mil_symbol_sensemaker = True
        settings_mock.rules_file_path = "fake_mil_rules.json"
        settings_mock.mil_sym_attr_retriever = "AllAtOnce"

        mock_mil_sym_controller.start()

        # Verify register called
        register_mock.assert_called_once_with("mil_symbol", sensemaker_mock.return_value)

        # Verify super().start() called
        super_start_mock.assert_called_once_with(mock_mil_sym_controller)


def test_start_does_nothing_when_disabled(mock_mil_sym_controller):
    with (
        mock.patch("oms_sensemaking.config.SETTINGS.mil_symbol_settings") as settings_mock,
        mock.patch.object(mock_mil_sym_controller, "register") as register_mock,
        mock.patch.object(MilSymbolSensemakerController, "start", autospec=True) as super_start_mock,
    ):
        settings_mock.enable_mil_symbol_sensmaker = False

        mock_mil_sym_controller.start()

        register_mock.assert_not_called()
        super_start_mock.assert_called_once_with(mock_mil_sym_controller)


def test_passes_filter_returns_true_for_handled_event():
    filt = MilSymbolQueueFilter()

    event1 = AuditLogEvent(
        userId="user1", objectId=uuid4(), objectType=ObjectType.ATTRIBUTE.value, action=Action.CREATE.value
    )
    event1.headers = AuditLogHeaders(SETTINGS.mil_symbol_settings.status_iris[0])
    event2 = AuditLogEvent(
        userId="user1", objectId=uuid4(), objectType=ObjectType.NODE.value, action=Action.CREATE.value
    )

    assert filt.passes_filter(event1) is True
    assert filt.passes_filter(event2) is True


@pytest.mark.parametrize(
    "obj_type,action",
    [
        ("not-handled", Action.CREATE.value),
        (ObjectType.ATTRIBUTE.value, "not-handled"),
        ("not-handled", "not-handled"),
    ],
)
def test_passes_filter_returns_false_for_unhandled(obj_type, action):
    filt = MilSymbolQueueFilter()

    event = AuditLogEvent(userId="user1", objectId=uuid4(), objectType=obj_type, action=action)

    assert filt.passes_filter(event) is False
