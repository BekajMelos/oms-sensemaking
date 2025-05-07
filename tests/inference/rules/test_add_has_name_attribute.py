from uuid import uuid4

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
from oms_sensemaking.inference.rules.add_has_name_attribute import AddHasNameAttribute, AddHasNameFinding
from oms_sensemaking.inference.rules.rule_context import RuleContext


@pytest.fixture
def name_attr(mocker: MockerFixture):
    """
    A Name attribute to be evaluated
    """
    attr = mocker.Mock(spec=AttributeAttribute)
    attr.id = "junk won't match"
    attr.acm = DEFAULT_ACM
    attr.labels = [SETTINGS.sm_inferenced_label, SETTINGS.inference_sm_label,
                   SETTINGS.add_has_name_sm_label, AddHasNameAttribute.version_string]
    attr.attributeIri = SETTINGS.inference_add_has_name_attribute_iri
    attr.attributeName = SETTINGS.inference_add_has_name_attribute_iri.split("/")[-1]
    attr.attributeValue = "some attr name"
    attr.attributeType = AttributeType.BOOLEAN
    attr.confidence = Confidence.MODERATE
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd"
    attr.nodeId = "0cc17447-b1f8-48e8-ae30-f9031f250b5d"

    return attr

@pytest.fixture
def invalid_attr(mocker: MockerFixture):
    """
    Attribute not pointing to a node
    """
    attr = mocker.Mock(spec=AttributeAttribute)
    attr.id = "junk won't match"
    attr.acm = DEFAULT_ACM
    attr.labels = [SETTINGS.sm_inferenced_label, SETTINGS.inference_sm_label,
                   SETTINGS.add_has_name_sm_label, AddHasNameAttribute.version_string]
    attr.attributeIri = SETTINGS.inference_add_has_name_attribute_iri
    attr.attributeName = SETTINGS.inference_add_has_name_attribute_iri.split("/")[-1]
    attr.attributeValue = "some attr name"
    attr.attributeType = AttributeType.BOOLEAN
    attr.confidence = Confidence.MODERATE
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd"
    attr.nodeId = None

    return attr


def test_evaluate_none_input():
    """Test to verify we only run the rule against attributes"""
    rule = AddHasNameAttribute("some name")
    assert not rule.evaluate(RuleContext()), "should only run for attributes"

def test_evaluate_attribute_no_node(invalid_attr):
    """Test to verify we only run the rule against attributes pointing to nodes"""
    rule = AddHasNameAttribute("some name")
    assert not rule.evaluate(RuleContext()), "should only run for attributes pointing to nodes"

def test_evaluate_attribute_input(name_attr):
    """Test to verify valid inputs are recognized as such"""
    rule = AddHasNameAttribute("some name")

    assert rule.evaluate(RuleContext(attribute=name_attr)), "expected input to be a valid Name attribute"


def test_evaluate_attribute_empty_value(name_attr):
    """Test to verify emtpy names would not cause a HasName attribute to be created"""
    rule = AddHasNameAttribute("some name")

    attr = name_attr
    attr.attributeValue = ""
    assert not rule.evaluate(RuleContext(attribute=attr)), "expected empty string to not count as a name"


def test_has_action_already_ran(mocker: MockerFixture, name_attr):
    mock = mocker.patch("oms_sensemaking.clients.instances.oms_client.get_attributes")
    rule = AddHasNameAttribute("some name")
    rule.has_action_already_ran(RuleContext(attribute=name_attr))
    mock.assert_called_once_with(
        AttributeQuery(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue=StringQuery(equals="true"),
            attributeType={
                "is": AttributeType.BOOLEAN,
            },
            confidence={"is": (name_attr.confidence)},
            sourceId=name_attr.sourceId,
            nodeIds=[name_attr.nodeId],
            tags=SETTINGS.inference_tags,
            labels=[SETTINGS.sm_inferenced_label, SETTINGS.inference_sm_label,
                    SETTINGS.add_has_name_sm_label, rule.version_string],
        )
    )


def test_action_creates_attribute(mocker: MockerFixture, name_attr):
    oms_mock = mocker.patch("oms_sensemaking.clients.instances.oms_client.create_attribute")
    create_attr_response = mocker.MagicMock(spec=AttributeAttribute)
    create_attr_response.id = uuid4()
    oms_mock.return_value = create_attr_response

    rule = AddHasNameAttribute("some name")
    finding_writer_mock = mocker.patch.object(rule._finding_writer, "save_findings")

    # ensure we do pre-action steps too
    rule._action(RuleContext(attribute=name_attr))

    oms_mock.assert_called_once_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue="true",
            attributeType=AttributeType.BOOLEAN,
            confidence=name_attr.confidence,
            sourceId=name_attr.sourceId,
            nodeId=name_attr.nodeId,
            acm=name_attr.acm,
            tags=SETTINGS.inference_tags,
            labels=[SETTINGS.sm_inferenced_label, SETTINGS.inference_sm_label,
                    SETTINGS.add_has_name_sm_label, rule.version_string]
        )
    )
    expected_findings = [AddHasNameFinding(name_attr.acm, create_attr_response.id)]
    finding_writer_mock.assert_called_once_with(expected_findings, rule)
