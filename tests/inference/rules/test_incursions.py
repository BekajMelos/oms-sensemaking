import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.observation import ObservationObservation
from oms_sdk.generated.generated_graphql_client.enums import AttributeType, Confidence
from oms_sdk.generated.generated_graphql_client.input_types import (
    AttributeQuery,
    CreateAttributeInput,
    StringQuery,
)
from pytest_mock import MockerFixture, mocker
from oms_sdk.generated.generated_graphql_client.node import NodeNode

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.incursions import Incursion
from oms_sensemaking.inference.rules.rule_context import RuleContext
import json


with open('./tests/inference/rules/test_data/areas_of_interest/geos_of_interest.json', 'r') as file:
            features = json.load(file)["features"]
            region1_geometry = features[0]["geometry"]
            region2_geometry = features[1]["geometry"]

@pytest.fixture
def incursion_attr(mocker: MockerFixture):
    """
    An existing incursion attribute
    """
    attr = mocker.Mock(spec=AttributeAttribute)
    attr.id = "incAttr1"
    attr.acm = DEFAULT_ACM
    attr.attributeIri = SETTINGS.inference_incursion_attribute_iri
    attr.attributeName = SETTINGS.inference_incursion_attribute_iri.split("/")[-1]
    attr.attributeValue = "Incursion"
    attr.attributeType = AttributeType.GEOSPATIAL
    attr.confidence = Confidence.MODERATE
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd"
    attr.nodeId = "parent_node_id"
    attr.geometry = region1_geometry
    attr.valueStart = "2024-01-01T00:00:00+00:00"
    attr.valueEnd = "2025-01-01T00:00:00+00:00"
    return attr

@pytest.fixture
def incursion_obs(mocker: MockerFixture):
  """
  Incoming observation
  """
  geometry = {
    "coordinates": [
      -157.20314345121238,
      20.32200240882949
    ],
    "type": "Point"
  }

  obs = mocker.Mock(spec=ObservationObservation)
  obs.id = "obs_id"
  obs.version = "version"
  obs.acm = "acm"
  obs.classIri = "classIri"
  obs.className = "className"
  obs.confidence = Confidence.MODERATE
  obs.sourceId = "obs_sourceId"
  obs.nodeId = "parent_node_id"
  obs.geometry = geometry

  return obs

@pytest.fixture
def parent_node(mocker: MockerFixture):
    """
    A parent node of incursion_obs
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "parent_node_id" # Base Node
    node.name = "Base Node"
    node.geoQuery = "some query"
    node.relationships = "another query"
    node.tier = "DERIVATIVE" #idk what this should be

    return node

def test_evaluate_none_input():
    """Test to verify we only run the rule against observations"""
    rule = Incursion("incursion rule")
    assert not rule.evaluate(RuleContext()), "should only run for observations"


def test_evaluate_observation_input(incursion_obs, mocker: MockerFixture):
    """Test to verify valid inputs are recognized as such"""
    rule = Incursion("incursion rule")

    mock_get_nodes = mocker.patch("oms_sensemaking.clients.oms_client.get_nodes")
    mock_nodes = {
      "parent_node_id": parent_node
    }

    def get_nodes_side_effect(query):
        node_id = query.ids[0]
        return mock_nodes.get(node_id)

    mock_get_nodes.side_effect = get_nodes_side_effect
    assert rule.evaluate(RuleContext(observation=incursion_obs)), "expected input to be a valid observation"


# def test_evaluate_attribute_empty_value(name_attr):
#     """Test to verify emtpy names would not cause a HasName attribute to be created"""
#     rule = Incursion("some name")

#     attr = name_attr
#     attr.attributeValue = ""
#     assert not rule.evaluate(RuleContext(attribute=attr)), "expected empty string to not count as a name"


# def test_has_action_already_ran(mocker: MockerFixture, name_attr):
#     mock = mocker.patch("oms_sensemaking.clients.oms_client.get_attributes")
#     rule = Incursion("some name")
#     rule.has_action_already_ran(RuleContext(attribute=name_attr))
#     mock.assert_called_once_with(
#         AttributeQuery(
#             attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
#             attributeValue=StringQuery(equals="true"),
#             attributeType={
#                 "is": AttributeType.BOOLEAN,
#             },
#             confidence={"is": (name_attr.confidence)},
#             sourceId=name_attr.sourceId,
#             nodeIds=[name_attr.nodeId],
#             tags=SETTINGS.inference_tags,
#         )
#     )


# def test_action_creates_attribute(mocker: MockerFixture, name_attr):
#     mock = mocker.patch("oms_sensemaking.clients.oms_client.create_attribute")
#     rule = Incursion("some name")
#     rule.action(RuleContext(attribute=name_attr))
#     mock.assert_called_once_with(
#         CreateAttributeInput(
#             attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
#             attributeValue="true",
#             attributeType=AttributeType.BOOLEAN,
#             confidence=name_attr.confidence,
#             sourceId=name_attr.sourceId,
#             nodeId=name_attr.nodeId,
#             acm=name_attr.acm,
#             tags=SETTINGS.inference_tags,
#         )
#     )
