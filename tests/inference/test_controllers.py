from unittest import mock
from uuid import UUID, uuid4

import pytest
from oms_sdk.generated.generated_graphql_client import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.error_loggers import ErrorLogger, RethrowErrorLogger
from oms_sensemaking.core.events import AuditLogEvent, DummyAuditLogEventConsumer, RabbitMQListener
from oms_sensemaking.inference.controllers import (
    InferenceQueueFilter,
    InferenceSensemakerController,
)


@pytest.fixture
def mock_inference_controller():
    controller = InferenceSensemakerController(
        RabbitMQListener(
            "InferenceRMQListener",
            SETTINGS.rmq_res_queue_name,
            SETTINGS.queue_worker_threads,
            event_filter=InferenceQueueFilter(),
        ),
        RethrowErrorLogger(ErrorLogger()),
    )
    return controller


def test_handle_event(mocker: MockerFixture):
    consumer = DummyAuditLogEventConsumer()
    controller = InferenceSensemakerController(consumer, RethrowErrorLogger(ErrorLogger()))

    mock_attribute = mocker.Mock(spec=AttributeAttribute)
    mock_attribute.id = "0bfc5dfe-f502-4d05-9ddf-94a6860a11e7"
    mock = mocker.patch("oms_sensemaking.core.oms_crud.OmsCrudTool.get_attribute")
    mock.return_value = mock_attribute

    attribute = AuditLogEvent("dn", UUID(mock_attribute.id), ObjectType.ATTRIBUTE, Action.CREATE)
    processed_successfully = controller.handle_event(attribute)

    assert processed_successfully, "Inference Controller should handle attributes"
    mock.assert_called_once()


def test_start_registers_resolution_sensemaker_when_enabled(mock_inference_controller):
    with (
        mock.patch("oms_sensemaking.config.SETTINGS") as settings_mock,
        mock.patch.object(mock_inference_controller, "register") as register_mock,
        mock.patch("oms_sensemaking.inference.controllers.InOrOutOfGarrison") as sensemaker_mock,
        mock.patch.object(SensemakerController, "start", autospec=True) as super_start_mock,
    ):
        # configure settings
        settings_mock.generate_inferences = True

        mock_inference_controller.start()

        # Verify ResolutionSensemaker was created with correct args
        sensemaker_mock.assert_called_once()

        # Verify register called
        register_mock.assert_called_with("garrison", sensemaker_mock.return_value)

        # Verify super().start() called
        super_start_mock.assert_called_once_with(mock_inference_controller)


def test_start_does_nothing_when_disabled(mock_inference_controller):
    with (
        mock.patch("oms_sensemaking.config.SETTINGS") as settings_mock,
        mock.patch.object(mock_inference_controller, "register") as register_mock,
        mock.patch.object(InferenceSensemakerController, "start", autospec=True) as super_start_mock,
    ):
        settings_mock.generate_inferences = False

        mock_inference_controller.start()

        register_mock.assert_not_called()
        super_start_mock.assert_called_once_with(mock_inference_controller)


def test_passes_filter_returns_true_for_handled_event():
    filt = InferenceQueueFilter()

    event1 = AuditLogEvent(
        userId="user1", objectId=uuid4(), objectType=ObjectType.OBSERVATION.value, action=Action.CREATE.value
    )
    event2 = AuditLogEvent(
        userId="user1", objectId=uuid4(), objectType=ObjectType.OBSERVATION.value, action=Action.RESTORE.value
    )

    assert filt.passes_filter(event1) is True
    assert filt.passes_filter(event2) is True


@pytest.mark.parametrize(
    "obj_type,action",
    [
        ("not-handled", Action.CREATE.value),
        (ObjectType.OBSERVATION.value, "not-handled"),
        ("not-handled", "not-handled"),
    ],
)
def test_passes_filter_returns_false_for_unhandled(obj_type, action):
    filt = InferenceQueueFilter()

    event = AuditLogEvent(userId="user1", objectId=uuid4(), objectType=obj_type, action=action)

    assert filt.passes_filter(event) is False
