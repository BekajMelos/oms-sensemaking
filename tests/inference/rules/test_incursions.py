from unittest.mock import MagicMock
import pytest
from oms_sdk import DEFAULT_ACM

from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeType,
    ActivityState,
    ObservationObservation,
    Confidence,
    AttributeQuery,
    CreateAttributeInput,
    StringQuery,
    CreateActivityInput,
    GeoQuery,
    ObservationQuery,
    TimeQuery,
    UpdateActivityInput,
    UpdateAttributeInput
)
from pytest_mock import MockerFixture, mocker
from oms_sdk.generated.generated_graphql_client.node import NodeNode

from oms_sensemaking.config import SETTINGS
import oms_sensemaking.inference
import oms_sensemaking.inference.rules
from oms_sensemaking.inference.rules.incursions import Incursion
import oms_sensemaking.inference.rules.incursions
from oms_sensemaking.inference.rules.rule_context import RuleContext
import json
import copy

# Refactor this- move to config
with open('./tests/inference/rules/test_data/areas_of_interest/geos_of_interest.json', 'r') as file:
            features = json.load(file)["features"]
            region1_geometry = features[0]["geometry"]
            region2_geometry = features[1]["geometry"]


# Mock nodes
@pytest.fixture
def attribute1(mocker: MockerFixture):
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
    attr.geometry = json.dumps(region1_geometry)
    attr.valueStart = "2024-01-01T00:00:00+00:00"
    attr.valueEnd = "2024-05-01T00:00:00+00:00"
    return attr

@pytest.fixture
def attribute2(mocker: MockerFixture):
    """
    An existing incursion attribute
    """
    attr = mocker.Mock(spec=AttributeAttribute)
    attr.id = "incAttr2"
    attr.acm = DEFAULT_ACM
    attr.attributeIri = SETTINGS.inference_incursion_attribute_iri
    attr.attributeName = SETTINGS.inference_incursion_attribute_iri.split("/")[-1]
    attr.attributeValue = "Incursion"
    attr.attributeType = AttributeType.GEOSPATIAL
    attr.confidence = Confidence.MODERATE
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd"
    attr.nodeId = "parent_node_id"
    attr.geometry = json.dumps(region1_geometry)
    attr.valueStart = "2022-01-01T00:00:00+00:00"
    attr.valueEnd = "2023-01-01T00:00:00+00:00"
    return attr

@pytest.fixture
def observational_node_region1(mocker: MockerFixture):
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
def observational_node_region2(mocker: MockerFixture):
  """
  Incoming observation
  """
  geometry = {
    	"coordinates": [
      	-152.16868319466693,
        23.556473770341952
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
def no_inc_observational_node(mocker: MockerFixture):
  """
  Incoming observation
  """
  geometry = {
    	"coordinates": [
      	-150.93829627954565,
        20.83888460523758
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
    A parent node of observational_node_region1
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "parent_node_id" # Base Node
    node.name = "Base Node"
    node.geoQuery = "some query"
    node.relationships = "another query"
    node.tier = "DERIVATIVE" #idk what this should be

    return node


# Tests
def test_evaluate_input(observational_node_region1):
    """Test to verify valid inputs are recognized as such"""
    rule = Incursion("incursion rule")

    # Rule should only be ran against observations
    assert not rule.evaluate(RuleContext()), "should only run for observations"

    # Input observations must include a nodeId and geometry
    assert rule.evaluate(RuleContext(observation=observational_node_region1)), "expected input to be a valid observation"
    observation_without_parent = copy.deepcopy(observational_node_region1)
    observation_without_parent.nodeId = None
    assert not rule.evaluate(RuleContext(observation=observation_without_parent)), "expected input to be an invalid observation"


def test_action_method(mocker: MockerFixture,
                       parent_node,
                       observational_node_region1,
                       attribute1,
                       attribute2,
                       no_inc_observational_node,
                       observational_node_region2):
    """Test to verify action method with various scenarios"""
    rule = Incursion("incursion rule")

    # Mocked methods

    #get_nodes
    mock_get_nodes = mocker.patch("oms_sensemaking.clients.oms_client.get_nodes")
    mock_nodes_response = MagicMock()
    mock_nodes_response.data = [parent_node] 
    mock_get_nodes.return_value = mock_nodes_response
    # get_attributes
    mock_get_attributes = mocker.patch("oms_sensemaking.clients.oms_client.get_attributes")
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = [] 
    mock_get_attributes.return_value = mock_attribute_response
    # create_attribute
    mock_create_attribute = mocker.patch("oms_sensemaking.clients.oms_client.create_attribute")
    # update_attribute 
    mock_update_attribute = mocker.patch("oms_sensemaking.clients.oms_client.update_attribute")
    # get_activities
    mock_get_activities = mocker.patch("oms_sensemaking.clients.oms_client.get_activities")
    mock_activity_response = MagicMock()
    mock_activity = MagicMock()
    mock_activity.id = "activity_id"
    mock_activity_response.data = [mock_activity] 
    mock_get_activities.return_value = mock_activity_response   
    # create_activity
    mock_create_activity = mocker.patch("oms_sensemaking.clients.oms_client.create_activity")
    # update_attribute 
    mock_update_activity = mocker.patch("oms_sensemaking.clients.oms_client.update_activity")
    # get_observations
    mock_get_observations = mocker.patch("oms_sensemaking.clients.oms_client.get_observations")
    mock_observation_response = MagicMock()
    mock_observation_response.data = [observational_node_region1] 
    mock_get_observations.return_value = mock_observation_response
    #_check_observations_between
    # mock_check_observations_between = mocker.patch("oms_sensemaking.inference.rules.incursions.Incursion._check_observations_between")
    # mock_check_observations_between.return_value = (False, ())


    # Scenario: Observation not in any area of interest, resulting in no creations or updates
    rule.action(RuleContext(observation=no_inc_observational_node))

    mock_create_activity.assert_not_called()
    mock_update_activity.assert_not_called()

    # Scenario: Observation input yields new incursion and activity in region1
    rule.action(RuleContext(observation=observational_node_region1))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=json.dumps(region1_geometry)),
            nodeIds=[parent_node.id],
            tags=SETTINGS.incursion_tags
        )
    )
    mock_create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_incursion_attribute_iri,
            attributeValue="Incursion",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=observational_node_region1.confidence,
            sourceId=observational_node_region1.sourceId, #change to config value
            nodeId=parent_node.id,
            acm=observational_node_region1.acm,
            tags=SETTINGS.incursion_tags,
            geometry=json.dumps(region1_geometry),
            valueStart=observational_node_region1.startTime,
            valueEnd=observational_node_region1.endTime
        )
    )
    mock_create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region1.acm,
            tags=SETTINGS.incursion_tags,
            name="Incursion",
            description=f"Incursion detected into {region1_geometry}",
            state=ActivityState.UNKNOWN,
            nodeId=observational_node_region1.nodeId,
            observationIds=[observational_node_region1.id],
            startTime=observational_node_region1.startTime,
            endTime=observational_node_region1.endTime
        )
    )
    
    # Scenario: Two existing incursion attributes with same geo of interest- one that is part of an incursion separate from the observation and one that is part of an incursion including the observation, resulting in an attribute/activity update
    mock_attribute_response.data = [attribute2, attribute1]
    mock_get_attributes.return_value = mock_attribute_response

    rule.action(RuleContext(observation=observational_node_region1))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=json.dumps(region1_geometry)),
            nodeIds=[parent_node.id],
            tags=SETTINGS.incursion_tags
        )
    )

    mock_get_observations.assert_called_with(
        ObservationQuery(
            nodeId=[parent_node.id],
            startTime=TimeQuery(gte = attribute2.valueEnd),
            endTime=TimeQuery(lte = observational_node_region1.startTime)
        )
    )
    mock_update_attribute.assert_called_with(
        UpdateAttributeInput(
            id=attribute1.id,
            startTime=observational_node_region1.startTime,
            endTime=observational_node_region1.endTime,
        )
    )
    mock_update_activity.assert_called_with(
        UpdateActivityInput(
            id = "activity_id",
            addObservationIds=[observational_node_region1.id],
            startTime=observational_node_region1.startTime,
            endTime=observational_node_region1.endTime
        )
    )

    # Scenario: Observation input yields new incursion and activity in region2
    rule.action(RuleContext(observation=observational_node_region2))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=json.dumps(region2_geometry)),
            nodeIds=[parent_node.id],
            tags=SETTINGS.incursion_tags
        )
    )

    # Scenario: One existing incursion attribute exists matching observation's geo of interest with nonoverlapping time, resulting in attribute/activity updates
    mock_observation_response.data = [] 
    mock_get_observations.return_value = mock_observation_response

    rule.action(RuleContext(observation=observational_node_region1))
    mock_get_observations.assert_called_with(
        ObservationQuery(
            nodeId=[parent_node.id],
            startTime=TimeQuery(gte = attribute2.valueEnd),
            endTime=TimeQuery(lte = observational_node_region1.startTime)
        )
    )
    mock_update_attribute.assert_called_with(
        UpdateAttributeInput(
            id=attribute2.id,
            startTime=attribute2.valueStart,
            endTime=observational_node_region1.endTime,
        )
    )
    mock_update_activity.assert_called_with(
        UpdateActivityInput(
            id = "activity_id",
            addObservationIds=[observational_node_region1.id],
            startTime=attribute2.valueStart,
            endTime=observational_node_region1.endTime
        )
    )