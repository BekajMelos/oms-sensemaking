from unittest import mock
from uuid import uuid4

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.core.events import AuditLogEvent
from oms_sensemaking.iw.controllers import ObservableSensemakerController


@mock.patch("oms_sensemaking.iw.controllers.process_observables")
def test_observable_sensemaker_controller_handle_event(mock_process_observables: mock.MagicMock):
    """Test that handle_event calls process_observables"""
    # Mock the event consumer required by the parent class
    mock_event_consumer = mock.MagicMock()
    mock_event_consumer.handle_event = None  # This will be set by the controller

    controller = ObservableSensemakerController(mock_event_consumer)

    # Create a test event
    event = AuditLogEvent(userId="test-user", objectId=uuid4(), objectType=ObjectType.ATTRIBUTE, action=Action.CREATE)

    # Call handle_event
    result = controller.handle_event(event)

    # Verify process_observables was called
    mock_process_observables.assert_called_once()

    # Verify the method returns True
    assert result is True
