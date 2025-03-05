from uuid import UUID

from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from pytest_mock import MockerFixture

from oms_sensemaking.core.events import AuditLogEvent, DummyAuditLogEventConsumer
from oms_sensemaking.inference.controllers import InferenceSensemakerController


def test_handle_event(mocker: MockerFixture):
    consumer = DummyAuditLogEventConsumer()
    controller = InferenceSensemakerController(consumer)

    mock_attribute = mocker.Mock(spec=AttributeAttribute)
    mock_attribute.id = "0bfc5dfe-f502-4d05-9ddf-94a6860a11e7"
    mock = mocker.patch("oms_sensemaking.core.oms_crud.OmsCrudTool.get_attribute")
    mock.return_value = mock_attribute

    attribute = AuditLogEvent("dn", UUID(mock_attribute.id), ObjectType.ATTRIBUTE, Action.CREATE)
    processed_successfully = controller.handle_event(attribute)

    assert processed_successfully, "Inference Controller should handle attributes"
    mock.assert_called_once()
