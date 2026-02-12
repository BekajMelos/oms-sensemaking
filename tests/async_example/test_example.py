from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeType,
    AuthorityValue,
    Confidence,
    CreateAttributeInput,
)

from oms_sensemaking.async_example.sensemakers.example import ExampleAsyncSensemaker


@pytest.fixture
def input_attribute() -> AttributeAttribute:
    attr = Mock(spec=AttributeAttribute)
    attr.id = MagicMock()
    attr.version = MagicMock()
    attr.attributeName = "Name"
    attr.attributeIri = "Name"
    attr.authoritySetBy = "test_user"
    attr.authoritySetAtTime = MagicMock()
    attr.authorityValue = AuthorityValue.DIAP
    attr.attributeValue = "John"
    attr.attributeType = AttributeType.STRING
    attr.confidence = Confidence.HIGH
    attr.sourceId = "source_123"
    attr.nodeId = "node_984"
    attr.acm = MagicMock()
    attr.tags = []
    return attr


@pytest.mark.asyncio
@patch("oms_sensemaking.async_example.sensemakers.example.AsyncAtomsCrudTool")
async def test_example(mock_async_crud_tool, input_attribute):
    mock_instance = mock_async_crud_tool.return_value
    mock_instance.create_attribute = AsyncMock(return_value=MagicMock(name="MockResponse"))
    sensemaker = ExampleAsyncSensemaker()
    await sensemaker.process_data(input_attribute, None)
    mock_instance.create_attribute.assert_called_once()
    created_attribute: CreateAttributeInput = mock_instance.create_attribute.call_args[0][0]

    assert created_attribute.attributeIri == "HasName"
    assert created_attribute.attributeType == AttributeType.BOOLEAN
    assert created_attribute.attributeValue == "true"

    assert created_attribute.confidence == input_attribute.confidence
    assert created_attribute.nodeId == input_attribute.nodeId
