from unittest.mock import AsyncMock, MagicMock, patch

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
    attr = AttributeAttribute(
        id=MagicMock(),
        version=MagicMock(),
        attributeName="Name",
        attributeIri="Name",
        authoritySetBy="test_user",
        authoritySetAtTime=MagicMock(),
        authorityValue=AuthorityValue.DIAP,
        attributeValue="John",
        attributeType=AttributeType.STRING,
        confidence=Confidence.HIGH,
        sourceId="source_123",
        nodeId="node_984",
        acm=MagicMock(),
        tags=[],
        labels=[],
        isMutable=True,
        isReviewed=False,
        isAuthoritative=False,
        isUserEntered=True,
        attributeDisplayValue=None,
        attributeNormalizedValue=None,
        geometry=None,
        sourceType=None,
        observationId=None,
        activityId=None,
        valueStart=None,
        valueEnd=None,
        reviewedBy=None,
        reviewedAt=None,
    )
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
