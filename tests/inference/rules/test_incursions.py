import copy
import json
from unittest.mock import MagicMock

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    ActivityState,
    AttributeAttribute,
    AttributeQuery,
    AttributeType,
    Confidence,
    CreateActivityInput,
    CreateAttributeInput,
    GeoQuery,
    NodeNode,
    ObservationObservation,
    ObservationQuery,
    StringQuery,
    TimeQuery,
    UpdateActivityInput,
    UpdateAttributeInput,
)
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.data.areas_of_interest import features_list_from_geojson
from oms_sensemaking.inference.rules.incursions import Incursion
from oms_sensemaking.inference.rules.rule_context import RuleContext


@pytest.fixture
def areas_of_interest():
    features = features_list_from_geojson(SETTINGS.incursion_areas_of_interest_path)
    return [feature["geometry"] for feature in features]

# Mocked nodes
@pytest.fixture
def attribute1(mocker: MockerFixture, areas_of_interest):
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
    attr.geometry = json.dumps(areas_of_interest[0])
    attr.valueStart = "2024-01-01T00:00:00+00:00"
    attr.valueEnd = "2024-05-01T00:00:00+00:00"
    return attr

@pytest.fixture
def attribute2(mocker: MockerFixture, areas_of_interest):
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
    attr.geometry = json.dumps(areas_of_interest[0])
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

# Mock methods
@pytest.fixture
def mock_get_node(mocker: MockerFixture, parent_node):
    mock_get_node = mocker.patch("oms_sensemaking.clients.oms_client.get_node")
    mock_get_node.return_value = parent_node
    return mock_get_node

@pytest.fixture
def mock_get_attributes(mocker: MockerFixture):
    mock_get_attributes = mocker.patch("oms_sensemaking.clients.oms_client.get_attributes")
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = []
    mock_get_attributes.return_value = mock_attribute_response
    return mock_get_attributes

@pytest.fixture
def mock_create_attribute(mocker: MockerFixture):
    mock_create_attribute = mocker.patch("oms_sensemaking.clients.oms_client.create_attribute")
    return mock_create_attribute

@pytest.fixture
def mock_update_attribute(mocker: MockerFixture):
    mock_update_attribute = mocker.patch("oms_sensemaking.clients.oms_client.update_attribute")
    return mock_update_attribute

@pytest.fixture
def mock_get_activities(mocker: MockerFixture):
    mock_get_activities = mocker.patch("oms_sensemaking.clients.oms_client.get_activities")
    mock_activity_response = MagicMock()
    mock_activity = MagicMock()
    mock_activity.id = "activity_id"
    mock_activity_response.data = [mock_activity]
    mock_get_activities.return_value = mock_activity_response
    return mock_get_activities

@pytest.fixture
def mock_create_activity(mocker: MockerFixture):
    mock_create_activity = mocker.patch("oms_sensemaking.clients.oms_client.create_activity")
    return mock_create_activity

@pytest.fixture
def mock_update_activity(mocker: MockerFixture):
    mock_update_activity = mocker.patch("oms_sensemaking.clients.oms_client.update_activity")
    return mock_update_activity

@pytest.fixture
def mock_get_observations(mocker: MockerFixture, observational_node_region1):
    mock_get_observations = mocker.patch("oms_sensemaking.clients.oms_client.get_observations")
    mock_observation_response = MagicMock()
    mock_observation_response.data = [observational_node_region1]
    mock_get_observations.return_value = mock_observation_response
    return mock_get_observations

# Tests
def test_evaluate_input(observational_node_region1):
    """Test to verify valid inputs are recognized as such"""
    rule = Incursion("incursion rule")

    # Rule should only be ran against observations
    assert not rule.evaluate(RuleContext()), "should only run for observations"

    # Input observations must include a nodeId and geometry
    assert rule.evaluate(RuleContext(observation=observational_node_region1)), "expected input to be valid"
    observation_without_parent = copy.deepcopy(observational_node_region1)
    observation_without_parent.nodeId = None
    assert not rule.evaluate(RuleContext(observation=observation_without_parent)), "expected input to be invalid"

def test_no_incursion(no_inc_observational_node,
                      mock_get_node,
                      mock_create_activity,
                      mock_update_activity):
    # Scenario: Observation not in any area of interest, resulting in no creations or updates
    rule = Incursion("incursion rule")

    rule.action(RuleContext(observation=no_inc_observational_node))
    mock_create_activity.assert_not_called()
    mock_update_activity.assert_not_called()

def test_new_incursion_region1(observational_node_region1,
                               parent_node,
                               mock_get_node,
                               mock_get_attributes,
                               mock_create_activity,
                               mock_create_attribute,
                               areas_of_interest):
    # Scenario: Observation input yields new incursion and activity in region1
    rule = Incursion("incursion rule")

    rule.action(RuleContext(observation=observational_node_region1))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=json.dumps(areas_of_interest[0])),
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
            geometry=json.dumps(areas_of_interest[0]),
            valueStart=observational_node_region1.startTime,
            valueEnd=observational_node_region1.endTime
        )
    )
    mock_create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region1.acm,
            tags=SETTINGS.incursion_tags,
            name="Incursion",
            description=f"Incursion detected into {areas_of_interest[0]}",
            state=ActivityState.UNKNOWN,
            nodeId=observational_node_region1.nodeId,
            observationIds=[observational_node_region1.id],
            startTime=observational_node_region1.startTime,
            endTime=observational_node_region1.endTime
        )
    )

def test_new_incursion_region2(observational_node_region2,
                               parent_node,
                               mock_get_node,
                               mock_get_attributes,
                               mock_create_activity,
                               mock_create_attribute,
                               areas_of_interest):
    # Scenario: Observation input yields new incursion and activity in region2
    rule = Incursion("incursion rule")

    rule.action(RuleContext(observation=observational_node_region2))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=json.dumps(areas_of_interest[1])),
            nodeIds=[parent_node.id],
            tags=SETTINGS.incursion_tags
        )
    )
    mock_create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_incursion_attribute_iri,
            attributeValue="Incursion",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=observational_node_region2.confidence,
            sourceId=observational_node_region2.sourceId,
            nodeId=parent_node.id,
            acm=observational_node_region2.acm,
            tags=SETTINGS.incursion_tags,
            geometry=json.dumps(areas_of_interest[1]),
            valueStart=observational_node_region2.startTime,
            valueEnd=observational_node_region2.endTime
        )
    )
    mock_create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region2.acm,
            tags=SETTINGS.incursion_tags,
            name="Incursion",
            description=f"Incursion detected into {areas_of_interest[1]}",
            state=ActivityState.UNKNOWN,
            nodeId=observational_node_region2.nodeId,
            observationIds=[observational_node_region2.id],
            startTime=observational_node_region2.startTime,
            endTime=observational_node_region2.endTime
        )
    )

def test_two_existing_incursions(observational_node_region1,
                                 parent_node,
                                 attribute1,
                                 attribute2,
                                 mock_get_node,
                                 mock_get_attributes,
                                 mock_get_activities,
                                 mock_get_observations,
                                 mock_update_attribute,
                                 mock_update_activity,
                                 areas_of_interest):
    # Scenario: Two existing incursion attributes with same geo of interest- one that
    # is part of an incursion separate from the observation and one that is part of an
    # incursion including the observation, resulting in an attribute/activity update
    rule = Incursion("incursion rule")
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = [attribute2, attribute1]
    mock_get_attributes.return_value = mock_attribute_response

    rule.action(RuleContext(observation=observational_node_region1))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=json.dumps(areas_of_interest[0])),
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

def test_existing_incursion_nonoverlapping_time(observational_node_region1,
                                                parent_node,
                                                attribute2,
                                                mock_get_node,
                                                mock_get_attributes,
                                                mock_get_activities,
                                                mock_get_observations,
                                                mock_update_attribute,
                                                mock_update_activity):
    # Scenario: One existing incursion attribute exists matching observation's geo of interest
    # with nonoverlapping time, resulting in attribute/activity updates
    rule = Incursion("incursion rule")

    mock_observation_response = MagicMock()
    mock_observation_response.data = []
    mock_get_observations.return_value = mock_observation_response
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = [attribute2]
    mock_get_attributes.return_value = mock_attribute_response

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
