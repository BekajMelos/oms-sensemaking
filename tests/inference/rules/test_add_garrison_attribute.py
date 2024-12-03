import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.node import NodeNode
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
    A Garrison attribute to be evaluated
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
    attr.geo = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "coordinates": [
                    -2.86242139203938,
                    18.68484166661493
            ],
            "type": "Point"
        }}]
    }

    return attr

@pytest.fixture
def garrison_node(mocker: MockerFixture):
    """
    A Garrison attribute to be evaluated
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "0cc17447-b1f8-48e8-ae30-f9031f250b5d"
    node.name = "TEST"
    node.geoQuery = "some query"
    node.relationships = "another query"
    node.tier = "OBSERVATIONAL"

    return node


def test_evaluate_none_input():
    """Test to verify we only run the rule against attributes"""
    print("********************START TEST********************")
    rule = AddGarrisonAttribute("some name")
    assert not rule.evaluate(RuleContext()), "should only run for attributes"

def test_action_creates_attribute(mocker: MockerFixture, garrison_attr, garrison_node):
    print("*********************START ACTION TEST************************")
    mock = mocker.patch("oms_sensemaking.clients.oms_client.create_attribute")
    mock2 = mocker.patch("oms_sensemaking.clients.oms_client.create_node")
    mock3 = mocker.patch("oms_sensemaking.clients.oms_client.get_nodes")
    mock2.return_value = garrison_node
    mock3.return_value = garrison_node
    print("test 1")
    rule = AddGarrisonAttribute("some name")
    print("test 2")
    rule.action(RuleContext(attribute=garrison_attr))
    print("test 3")
    mock.assert_called_once_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue="true",
            attributeType=AttributeType.BOOLEAN,
            confidence=garrison_attr.confidence,
            sourceId=garrison_attr.sourceId,
            nodeId=garrison_attr.nodeId,
            acm=garrison_attr.acm,
            tags=SETTINGS.inference_tags,
        )
    )
