import copy
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
    RelationshipRelationship,
    StringQuery,
    TimeQuery,
    UpdateActivityInput,
    UpdateAttributeInput,
)
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.data.areas_of_interest.areas_of_interest import features_list_from_geojson
from oms_sensemaking.inference.rules.add_garrison_attribute import AddOutOfGarrisonAttribute
from oms_sensemaking.inference.rules.rule_context import RuleContext


# Mocked nodes
@pytest.fixture
def geo_attribute1(mocker: MockerFixture):
    """
    Geo attribute for garrison_node
    """
    geometry = {"coordinates": [-155.62126383336064, 19.70066375574565], "type": "Point"}

    attr = mocker.Mock(spec=AttributeAttribute)
    attr.id = "garAttr1"
    attr.acm = DEFAULT_ACM
    attr.attributeIri = SETTINGS.inference_geo_attribute_iri
    attr.attributeName = SETTINGS.inference_geo_attribute_iri.split("/")[-1]
    attr.attributeValue = "Geospatial Location"
    attr.attributeType = AttributeType.GEOSPATIAL
    attr.confidence = Confidence.MODERATE
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd"
    attr.nodeId = "garrison_object_id"
    attr.geometry = geometry
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
    attr.attributeIri = SETTINGS.inference_geo_attribute_iri
    attr.attributeName = SETTINGS.inference_geo_attribute_iri.split("/")[-1]
    attr.attributeValue = "Incursion"
    attr.attributeType = AttributeType.GEOSPATIAL
    attr.confidence = Confidence.MODERATE
    attr.sourceId = "559cf331-ac45-4a78-816a-b4b3835d3dbd"
    attr.nodeId = "incurring_object_id"
    attr.geometry = areas_of_interest[0]
    attr.valueStart = "2022-01-01T00:00:00+00:00"
    attr.valueEnd = "2023-01-01T00:00:00+00:00"
    return attr


@pytest.fixture
def observational_node(mocker: MockerFixture):
    """
    Incoming observation
    """
    geometry = {"coordinates": [-155.6235, 19.7023], "type": "Point"}

    obs = mocker.Mock(spec=ObservationObservation)
    obs.id = "obs_id"
    obs.version = "version"
    obs.acm = "acm"
    obs.classIri = "classIri"
    obs.className = "className"
    obs.confidence = Confidence.MODERATE
    obs.sourceId = "obs_sourceId"
    obs.nodeId = "garrison_object_id"
    obs.geometry = geometry
    obs.startTime = "2024-01-01T00:00:00+00:00"
    obs.endTime = "2025-01-01T00:00:00+00:00"

    return obs


@pytest.fixture
def garrison_object(mocker: MockerFixture):
    """
    Garrison node of observational_node/initial_object
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "garrison_object_id"
    node.name = "Garrison Node"
    node.geoQuery = "some query"
    node.relationships = "another query"
    node.tier = "DERIVATIVE"

    return node

@pytest.fixture
def initial_object(mocker: MockerFixture):
    """
    Node observational_node points to
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "initial_object_id"
    node.name = "Base Node"
    node.geoQuery = "some query"
    node.relationships = "another query"
    node.tier = "DERIVATIVE"

    return node

@pytest.fixture
def garrison_relationship(mocker: MockerFixture):
    """
    Mock relationship between node that observation points to and garrison node
    """
    geometry = {"coordinates": [-155.6235, 19.7023], "type": "Point"}

    relationship = mocker.Mock(spec=RelationshipRelationship)
    relationship.id = "relationship_id"
    relationship.version = "version"
    relationship.acm = "acm"
    relationship.name = "name"
    relationship.confidence = Confidence.MODERATE
    relationship.sourceId = "obs_sourceId"
    relationship.startNodeId = "initial_object_id"
    relationship.endNodeId = "garrison_object_id"
    relationship.geometry = geometry

    return relationship


# Mock methods
@pytest.fixture
def mock_get_node(mocker: MockerFixture, initial_object):
    mock_get_node = mocker.patch("oms_sensemaking.clients.instances.oms_client.get_node")
    mock_get_node.return_value = initial_object
    return mock_get_node


@pytest.fixture
def mock_get_attributes(mocker: MockerFixture):
    mock_get_attributes = mocker.patch("oms_sensemaking.clients.instances.oms_client.get_attributes")
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = []
    mock_get_attributes.return_value = mock_attribute_response
    return mock_get_attributes


@pytest.fixture
def mock_get_activities(mocker: MockerFixture):
    mock_get_activities = mocker.patch("oms_sensemaking.clients.instances.oms_client.get_activities")
    mock_activity_response = MagicMock()
    mock_activity_response.data = []
    mock_get_activities.return_value = mock_activity_response
    return mock_get_activities

@pytest.fixture
def mock_get_relationships(mocker: MockerFixture):
    mock_get_relationships = mocker.patch("oms_sensemaking.clients.instances.oms_client.get_relationships")
    mock_relationship_response = MagicMock()
    mock_relationship = MagicMock()
    mock_relationship_response.data = [mock_relationship]
    mock_get_relationships.return_value = mock_relationship_response
    return mock_get_relationships


@pytest.fixture
def mock_create_activity(mocker: MockerFixture):
    mock_create_activity = mocker.patch("oms_sensemaking.clients.instances.oms_client.create_activity")
    return mock_create_activity


@pytest.fixture
def mock_update_activity(mocker: MockerFixture):
    mock_update_activity = mocker.patch("oms_sensemaking.clients.instances.oms_client.update_activity")
    return mock_update_activity


@pytest.fixture
def mock_get_observations(mocker: MockerFixture, observational_node):
    mock_get_observations = mocker.patch("oms_sensemaking.clients.instances.oms_client.get_observations")
    mock_observation_response = MagicMock()
    mock_observation_response.data = [observational_node]
    mock_get_observations.return_value = mock_observation_response
    return mock_get_observations


# Tests
def test_evaluate_input(observational_node):
    """Test to verify valid inputs are recognized as such"""
    rule = AddOutOfGarrisonAttribute("garrison rule")

    # Rule should only be ran against observations
    assert not rule.evaluate(RuleContext()), "should only run for observations"

    # Input observations must include a nodeId and geometry
    assert rule.evaluate(RuleContext(observation=observational_node)), "expected input to be valid"
    observation_without_parent = copy.deepcopy(observational_node)
    observation_without_parent.nodeId = None
    assert not rule.evaluate(RuleContext(observation=observation_without_parent)), "expected input to be invalid"


def test_new_in_garrison(
    observational_node,
    garrison_object,
    mock_get_node,
    mock_get_attributes,
    mock_get_relationships,
    mock_get_activities,
    mock_create_activity,
    geo_attribute1
):
    # Scenario: Observation input yields new in garrison activity
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = [geo_attribute1]
    mock_get_attributes.return_value = mock_attribute_response
    rule = AddOutOfGarrisonAttribute("garrison rule")

    rule.action(RuleContext(observation=observational_node))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIris=[SETTINGS.inference_geo_attribute_iri],
            nodeIds=[garrison_object.id],
        )
    )

    mock_create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node.acm,
            classIri=SETTINGS.inference_incursion_class_iri,
            name="In garrison",
            state=ActivityState.IN_GARRISON,
            nodeId=observational_node.nodeId,
            observationIds=[observational_node.id],
            startTime=observational_node.startTime,
            endTime=observational_node.endTime,
        )
    )


# def test_new_incursion_region2(
#     observational_node_region2,
#     incurring_object,
#     mock_get_node,
#     mock_get_attributes,
#     mock_create_activity,
#     mock_create_attribute,
#     areas_of_interest,
# ):
#     # Scenario: Observation input yields new incursion and activity in region2
#     rule = AddOutOfGarrisonAttribute("garrison rule")

#     rule.action(RuleContext(observation=observational_node_region2))
#     mock_get_attributes.assert_called_with(
#         AttributeQuery(
#             attributeIris=[SETTINGS.inference_geo_attribute_iri],
#             attributeValue=StringQuery(equals="Incursion"),
#             attributeType={"is": AttributeType.GEOSPATIAL},
#             geometry=GeoQuery(queryGeoJson=areas_of_interest[1]),
#             nodeIds=[incurring_object.id],
#             tags=SETTINGS.incursion_tags,
#         )
#     )
#     mock_create_attribute.assert_called_with(
#         CreateAttributeInput(
#             attributeIri=SETTINGS.inference_incursion_attribute_iri,
#             attributeValue="Incursion",
#             attributeType=AttributeType.GEOSPATIAL,
#             confidence=observational_node_region2.confidence,
#             sourceId=observational_node_region2.sourceId,
#             nodeId=incurring_object.id,
#             acm=observational_node_region2.acm,
#             tags=SETTINGS.incursion_tags,
#             geometry=areas_of_interest[1],
#             valueStart=observational_node_region2.startTime,
#             valueEnd=observational_node_region2.endTime,
#         )
#     )
#     mock_create_activity.assert_called_with(
#         CreateActivityInput(
#             acm=observational_node_region2.acm,
#             tags=SETTINGS.incursion_tags,
#             classIri=SETTINGS.inference_incursion_class_iri,
#             name="Incursion",
#             description=f"Incursion detected into {areas_of_interest[1]}",
#             state=ActivityState.UNKNOWN,
#             nodeId=observational_node_region2.nodeId,
#             observationIds=[observational_node_region2.id],
#             startTime=observational_node_region2.startTime,
#             endTime=observational_node_region2.endTime,
#         )
#     )


# def test_two_existing_incursions(
#     observational_node,
#     incurring_object,
#     geo_attribute1,
#     attribute2,
#     mock_get_node,
#     mock_get_attributes,
#     mock_get_activities,
#     mock_get_observations,
#     mock_update_attribute,
#     mock_update_activity,
#     areas_of_interest,
# ):
#     # Scenario: Two existing incursion attributes with same geo of interest- one that
#     # is part of an incursion separate from the observation and one that is part of an
#     # incursion including the observation, resulting in an attribute/activity update
#     rule = AddOutOfGarrisonAttribute("garrison rule")
#     mock_attribute_response = MagicMock()
#     mock_attribute_response.data = [attribute2, geo_attribute1]
#     mock_get_attributes.return_value = mock_attribute_response

#     rule.action(RuleContext(observation=observational_node))
#     mock_get_attributes.assert_called_with(
#         AttributeQuery(
#             attributeIris=[SETTINGS.inference_incursion_attribute_iri],
#             attributeValue=StringQuery(equals="Incursion"),
#             attributeType={"is": AttributeType.GEOSPATIAL},
#             geometry=GeoQuery(queryGeoJson=areas_of_interest[0]),
#             nodeIds=[incurring_object.id],
#             tags=SETTINGS.incursion_tags,
#         )
#     )

#     mock_get_observations.assert_called_with(
#         ObservationQuery(
#             nodeId=[incurring_object.id],
#             startTime=TimeQuery(gt=attribute2.valueEnd),
#             endTime=TimeQuery(lt=observational_node.startTime),
#         )
#     )
#     mock_update_attribute.assert_called_with(
#         UpdateAttributeInput(
#             id=geo_attribute1.id,
#             valueStart=observational_node.startTime,
#             valueEnd=observational_node.endTime,
#         )
#     )
#     mock_update_activity.assert_called_with(
#         UpdateActivityInput(
#             id="activity_id",
#             addObservationIds=[observational_node.id],
#             startTime=observational_node.startTime,
#             endTime=observational_node.endTime,
#         )
#     )


# def test_existing_incursion_nonoverlapping_time(
#     observational_node,
#     incurring_object,
#     attribute2,
#     mock_get_node,
#     mock_get_attributes,
#     mock_get_activities,
#     mock_get_observations,
#     mock_update_attribute,
#     mock_update_activity,
# ):
#     # Scenario: One existing incursion attribute exists matching observation's geo of interest
#     # with nonoverlapping time, resulting in attribute/activity updates
#     rule = AddOutOfGarrisonAttribute("garrison rule")

#     mock_observation_response = MagicMock()
#     mock_observation_response.data = []
#     mock_get_observations.return_value = mock_observation_response
#     mock_attribute_response = MagicMock()
#     mock_attribute_response.data = [attribute2]
#     mock_get_attributes.return_value = mock_attribute_response

#     rule.action(RuleContext(observation=observational_node))
#     mock_get_observations.assert_called_with(
#         ObservationQuery(
#             nodeId=[incurring_object.id],
#             startTime=TimeQuery(gt=attribute2.valueEnd),
#             endTime=TimeQuery(lt=observational_node.startTime),
#         )
#     )
#     mock_update_attribute.assert_called_with(
#         UpdateAttributeInput(
#             id=attribute2.id,
#             valueStart=attribute2.valueStart,
#             valueEnd=observational_node.endTime,
#         )
#     )
#     mock_update_activity.assert_called_with(
#         UpdateActivityInput(
#             id="activity_id",
#             addObservationIds=[observational_node.id],
#             startTime=attribute2.valueStart,
#             endTime=observational_node.endTime,
#         )
#     )
