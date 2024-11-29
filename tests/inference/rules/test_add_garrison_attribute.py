import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.enums import AttributeType, Confidence
from oms_sdk.generated.generated_graphql_client.input_types import (
    AttributeQuery,
    CreateAttributeInput,
    StringQuery,
)
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.add_has_name_attribute import AddHasNameAttribute
from oms_sensemaking.inference.rules.add_garrison_attribute import AddGarrisonAttribute
from oms_sensemaking.inference.rules.rule_context import RuleContext


@pytest.fixture
def garrison_attr(mocker: MockerFixture):
    """
    A Name attribute to be evaluated
    """
    attr = mocker.Mock(spec=AttributeAttribute)
    attr.id = "junk won't match"
    attr.acm = DEFAULT_ACM
    attr.attributeIri = SETTINGS.inference_add_garrison_attribute_iri
    attr.attributeName = SETTINGS.inference_add_garrison_attribute_iri.split("/")[-1]
    attr.attributeValue = "some attr name"
    attr.attributeType = AttributeType.BOOLEAN
    attr.confidence = Confidence.MODERATE
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd"
    attr.nodeId = "0cc17447-b1f8-48e8-ae30-f9031f250b5d"

    return attr

def test_evaluate_none_input():
    """Test to verify we only run the rule against attributes"""
    print("********************START TEST********************")
    rule = AddGarrisonAttribute("some name")
    assert not rule.evaluate(RuleContext()), "should only run for attributes"
