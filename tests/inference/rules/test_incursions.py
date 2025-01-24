from unittest.mock import MagicMock
import pytest
from oms_sdk import DEFAULT_ACM

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeType,
    ActivityState,
    ObservationObservation,
    NodesNodesData,
    AttributesAttributesData,
    Confidence,
    AttributeQuery,
    CreateAttributeInput,
    StringQuery,
    CreateActivityInput,
    GeoQuery,
    ObservationQuery,
    TimeQuery
)
from pytest_mock import MockerFixture, mocker
from oms_sdk.generated.generated_graphql_client.node import NodeNode

import oms_sensemaking
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.incursions import Incursion
from oms_sensemaking.inference.rules.rule_context import RuleContext
import json
import copy

# Refactor this- move to config
with open('./tests/inference/rules/test_data/areas_of_interest/geos_of_interest.json', 'r') as file:
            features = json.load(file)["features"]
            region1_geometry = features[0]["geometry"]
            region2_geometry = features[1]["geometry"]

class MockAttributeResponse:
    def __init__(self):
        self.data = []

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
def observational_node(mocker: MockerFixture):
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
  obs.startTime = "2024-01-01T00:00:00+00:00"
  obs.endTime = "2025-01-01T00:00:00+00:00"

  return obs

@pytest.fixture
def parent_node(mocker: MockerFixture):
    """
    A parent node of observational_node
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "parent_node_id" # Base Node
    node.name = "Base Node"
    node.geoQuery = "some query"
    node.relationships = "another query"
    node.tier = "DERIVATIVE" #idk what this should be

    return node


def test_evaluate_input(observational_node):
    """Test to verify valid inputs are recognized as such"""
    rule = Incursion("incursion rule")

    # Rule should only be ran against observations
    assert not rule.evaluate(RuleContext()), "should only run for observations"

    # Input observations must include a nodeId and geometry
    assert rule.evaluate(RuleContext(observation=observational_node)), "expected input to be a valid observation"
    observation_without_parent = copy.deepcopy(observational_node)
    observation_without_parent.nodeId = None
    assert not rule.evaluate(RuleContext(observation=observation_without_parent)), "expected input to be an invalid observation"


def test_action_method(mocker: MockerFixture,
                       parent_node,
                       observational_node,
                       incursion_attr):
    """Test to verify action method with various scenarios"""
    rule = Incursion("incursion rule")

    # Mocked methods
    mock_get_nodes = mocker.patch("oms_sensemaking.clients.oms_client.get_nodes")
    mock_nodes = {
        "parent_node_id": parent_node,
    }
    def get_nodes_side_effect(query):
        node_id = query.ids[0]
        return mock_nodes.get(node_id)
    mock_nodes_response = MagicMock()
    mock_nodes_response.data = [parent_node] 
    mock_get_nodes.return_value = mock_nodes_response
    
    mock_get_attributes = mocker.patch("oms_sensemaking.clients.oms_client.get_attributes")
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = [] 
    mock_get_attributes.return_value = mock_attribute_response

    mock_create_attribute = mocker.patch("oms_sensemaking.clients.oms_client.create_attribute")

    mock_create_activity = mocker.patch("oms_sensemaking.clients.oms_client.create_activity")

    # Scenario: No existing incursion attributes, observation input yields new incursion and activity
    rule.action(RuleContext(observation=observational_node))
    mock_get_attributes.assert_called_once_with(
        AttributeQuery(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=region1_geometry),
            nodeIds=[parent_node.id],
            tags=SETTINGS.incursion_tags
        )
    )
    mock_create_attribute.assert_called_once_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_incursion_attribute_iri,
            attributeValue="Incursion",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=observational_node.confidence,
            sourceId=observational_node.sourceId, #change to config value
            nodeId=parent_node.id,
            acm=observational_node.acm,
            tags=SETTINGS.incursion_tags,
            geometry=region1_geometry,
            valueStart=observational_node.startTime,
            valueEnd=observational_node.endTime
        )
    )
    mock_create_activity.assert_called_once_with(
        CreateActivityInput(
            acm=observational_node.acm,
            tags=SETTINGS.incursion_tags,
            name="Incursion",
            description=f"Incursion detected into {region1_geometry}",
            state=ActivityState.UNKNOWN,
            nodeId=observational_node.nodeId,
            observationIds=[observational_node.id],
            startTime=observational_node.startTime,
            endTime=observational_node.endTime
        )
    )
    