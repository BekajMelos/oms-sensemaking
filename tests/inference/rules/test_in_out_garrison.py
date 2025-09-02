import copy
from unittest.mock import MagicMock

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivitiesData,
    AttributeAttribute,
    AttributeType,
    Confidence,
    CreateActivityInput,
    GeoQuery,
    GeoQueryType,
    NodeNode,
    ObservationObservation,
    ObservationQuery,
    RelationshipRelationship,
    TimeQuery,
    UpdateActivityInput,
    UpdateUuidList,
    UuidQueryByList,
)
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.geo_helpers import generate_circle_points_geographical
from oms_sensemaking.inference.rules.in_out_garrison import InOrOutOfGarrison
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
    attr.valueStart = "2020-01-01T00:00:00+00:00"
    attr.valueEnd = "2026-01-01T00:00:00+00:00"
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
    obs.nodeId = "initial_object_id"
    obs.geometry = geometry
    obs.startTime = "2025-01-01T00:00:00+00:00"
    obs.endTime = "2025-01-01T00:00:00+00:00"

    return obs


@pytest.fixture
def observational_node2(mocker: MockerFixture):
    """
    Incoming observation
    """
    geometry = {"coordinates": [-77.10218105866703, 38.88589179856498], "type": "Point"}

    obs = mocker.Mock(spec=ObservationObservation)
    obs.id = "obs2_id"
    obs.version = "version"
    obs.acm = "acm"
    obs.classIri = "classIri"
    obs.className = "className"
    obs.confidence = Confidence.MODERATE
    obs.sourceId = "obs_sourceId"
    obs.nodeId = "initial_object_id"
    obs.geometry = geometry
    obs.startTime = "2024-01-01T00:00:00+00:00"
    obs.endTime = "2024-01-01T00:00:00+00:00"

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


@pytest.fixture
def in_garrison_activity1(mocker: MockerFixture):
    """
    Mock in garrison activity
    """
    activity = mocker.Mock(spec=ActivitiesActivitiesData)
    activity.id = "in_garrison_activity1_id"
    activity.version = "version"
    activity.acm = "acm"
    activity.classIri = SETTINGS.inference_garrison_class_iri
    activity.name = SETTINGS.inference_in_garrison_activity_name
    activity.className = "class name"
    activity.state = SETTINGS.inference_in_garrison_activity_state
    activity.nodeId = "initial_object_id"
    activity.observationIds = ["some_obs_id"]
    activity.startTime = "2022-01-01T00:00:00+00:00"
    activity.endTime = "2023-01-01T00:00:00+00:00"

    return activity


@pytest.fixture
def in_garrison_activity2(mocker: MockerFixture):
    """
    Mock in garrison activity
    """
    activity = mocker.Mock(spec=ActivitiesActivitiesData)
    activity.id = "in_garrison_activity2_id"
    activity.version = "1"
    activity.acm = "acm"
    activity.classIri = SETTINGS.inference_garrison_class_iri
    activity.name = SETTINGS.inference_in_garrison_activity_name
    activity.className = "class name"
    activity.state = SETTINGS.inference_in_garrison_activity_state
    activity.nodeId = "initial_object_id"
    activity.observationIds = ["some_obs_id"]
    activity.startTime = "2025-01-01T00:00:00+00:00"
    activity.endTime = "2026-05-01T00:00:00+00:00"

    return activity


@pytest.fixture
def out_garrison_activity1(mocker: MockerFixture):
    """
    Mock out of garrison activity
    """
    activity = mocker.Mock(spec=ActivitiesActivitiesData)
    activity.id = "out_garrison_activity1_id"
    activity.version = "version"
    activity.acm = "acm"
    activity.classIri = SETTINGS.inference_garrison_class_iri
    activity.name = SETTINGS.inference_out_of_garrison_activity_name
    activity.className = "class name"
    activity.state = SETTINGS.inference_out_of_garrison_activity_state
    activity.nodeId = "initial_object_id"
    activity.observationIds = ["some_obs_id"]
    activity.startTime = "2025-01-01T00:00:00+00:00"
    activity.endTime = "2027-01-01T00:00:00+00:00"

    return activity


@pytest.fixture
def out_garrison_activity2(mocker: MockerFixture):
    """
    Mock out of garrison activity
    """
    activity = mocker.Mock(spec=ActivitiesActivitiesData)
    activity.id = "out_garrison_activity2_id"
    activity.version = "1"
    activity.acm = "acm"
    activity.classIri = SETTINGS.inference_garrison_class_iri
    activity.name = SETTINGS.inference_out_of_garrison_activity_name
    activity.className = "class name"
    activity.state = SETTINGS.inference_out_of_garrison_activity_state
    activity.nodeId = "initial_object_id"
    activity.observationIds = ["some_obs_id"]
    activity.startTime = "2025-01-01T00:00:00+00:00"
    activity.endTime = "2026-05-01T00:00:00+00:00"

    return activity


# Mock methods
@pytest.fixture
def mock_get_node(mocker: MockerFixture, initial_object):
    mock_get_node = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.get_node")
    mock_get_node.return_value = initial_object
    return mock_get_node


@pytest.fixture
def mock_get_attributes(mocker: MockerFixture):
    mock_get_attributes = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.get_attributes")
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = []
    mock_get_attributes.return_value = mock_attribute_response
    return mock_get_attributes


@pytest.fixture
def mock_get_activities(mocker: MockerFixture):
    mock_get_activities = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.get_activities")
    mock_activity_response = MagicMock()
    mock_activity_response.data = []
    mock_get_activities.return_value = mock_activity_response
    return mock_get_activities


@pytest.fixture
def mock_get_relationships(mocker: MockerFixture, garrison_relationship):
    mock_get_relationships = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.get_relationships")
    mock_relationship_response = MagicMock()
    mock_relationship_response.data = [garrison_relationship]
    mock_get_relationships.return_value = mock_relationship_response
    return mock_get_relationships


@pytest.fixture
def mock_create_activity(mocker: MockerFixture):
    mock_create_activity = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.create_activity")
    return mock_create_activity


@pytest.fixture
def mock_update_activity(mocker: MockerFixture):
    mock_update_activity = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.update_activity")
    return mock_update_activity


@pytest.fixture
def mock_get_observations(mocker: MockerFixture, observational_node2):
    mock_get_observations = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.get_observations")
    mock_observation_response = MagicMock()
    mock_observation_response.data = [observational_node2]
    mock_get_observations.return_value = mock_observation_response
    return mock_get_observations


@pytest.fixture
def mock_gql_query(mocker, garrison_object, geo_attribute1):
    """
    Mocks the single custom operation used by _fetch_garrison_coords.
    Returns a structure matching the generated client:
      result.node.relationships.data[0].end_node.attributes.data[0].geometry.coordinates
    """
    payload = {
        "node": {
            "relationships": {
                "data": [
                    {
                        "end_node": {
                            "id": garrison_object.id,
                            "attributes": {
                                "data": [
                                    {
                                        "id": "attr-geo-1",
                                        "geometry": {
                                            "coordinates": geo_attribute1.geometry["coordinates"]
                                        },  # [lon, lat]
                                    }
                                ]
                            },
                        }
                    }
                ]
            }
        }
    }

    return mocker.patch(
        "oms_sensemaking.clients.instances.oms_crud_tool.oms_client.query",
        new=MagicMock(return_value=payload),
    )


# Tests
def test_evaluate_input(observational_node):
    """Test to verify valid inputs are recognized as such"""
    rule = InOrOutOfGarrison("garrison rule")

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
    mock_get_activities,
    mock_create_activity,
    geo_attribute1,
    mock_gql_query,
):
    # Scenario: Observation input yields new in garrison activity
    rule = InOrOutOfGarrison("garrison rule")
    rule.action(RuleContext(observation=observational_node))

    mock_gql_query.assert_called_once()
    _, kwargs = mock_gql_query.call_args
    assert kwargs.get("operation_name") == "InOutGarrison_HomeBaseWithGeo"

    mock_create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node.acm,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.garrison_sm_label,
                rule.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name=SETTINGS.inference_in_garrison_activity_name,
            state=SETTINGS.inference_in_garrison_activity_state,
            nodeId=observational_node.nodeId,
            observationIds=[observational_node.id],
            startTime=observational_node.startTime,
            endTime=observational_node.endTime,
        )
    )


def test_new_out_garrison(
    observational_node2,
    garrison_object,
    mock_get_node,
    mock_get_activities,
    mock_create_activity,
    geo_attribute1,
    mock_gql_query,
):
    # Scenario: Observation input yields new out of garrison activity
    rule = InOrOutOfGarrison("garrison rule")
    rule.action(RuleContext(observation=observational_node2))

    mock_gql_query.assert_called_once()
    _, kwargs = mock_gql_query.call_args
    assert kwargs.get("operation_name") == "InOutGarrison_HomeBaseWithGeo"

    mock_create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node2.acm,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.garrison_sm_label,
                rule.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name=SETTINGS.inference_out_of_garrison_activity_name,
            state=SETTINGS.inference_out_of_garrison_activity_state,
            nodeId=observational_node2.nodeId,
            observationIds=["obs2_id"],
            startTime=observational_node2.startTime,
            endTime=observational_node2.endTime,
        )
    )


def test_update_in_garrison(
    observational_node,
    garrison_object,
    mock_get_node,
    mock_get_activities,
    mock_get_observations,
    mock_update_activity,
    geo_attribute1,
    in_garrison_activity1,
    in_garrison_activity2,
    mock_gql_query,
):
    # Scenario: Observation input yields updating an in garrison activity
    mock_activity_response = MagicMock()
    mock_activity_response.data = [in_garrison_activity1, in_garrison_activity2]
    mock_get_activities.return_value = mock_activity_response

    rule = InOrOutOfGarrison("garrison rule")

    rule.action(RuleContext(observation=observational_node))

    # single call now
    mock_gql_query.assert_called_once()

    garrison_buffer_points = generate_circle_points_geographical(
        geo_attribute1.geometry["coordinates"][1],
        geo_attribute1.geometry["coordinates"][0],
        SETTINGS.garrison_distance_kilometers,
    )
    garrison_buffer_geojson = {"type": "Polygon", "coordinates": [garrison_buffer_points]}
    mock_get_observations.assert_called_with(
        ObservationQuery(
            nodeIds=UuidQueryByList(in_=["initial_object_id"]),
            startTime=TimeQuery(gt="2023-01-01T00:00:00+00:00"),
            endTime=TimeQuery(lte="2025-01-01T00:00:00+00:00"),
            geometry=GeoQuery(queryGeoJson=garrison_buffer_geojson, queryType=GeoQueryType.DISJOINT),
        )
    )
    mock_update_activity.assert_called_with(
        UpdateActivityInput(
            id=in_garrison_activity2.id,
            startTime=in_garrison_activity2.startTime,
            endTime=in_garrison_activity2.endTime,
            observationIds=UpdateUuidList(add=[observational_node.id]),
            nodeId=observational_node.nodeId,
        )
    )


def test_update_out_garrison(
    observational_node2,
    garrison_object,
    mock_get_node,
    mock_get_activities,
    mock_get_observations,
    mock_update_activity,
    geo_attribute1,
    out_garrison_activity1,
    mock_gql_query,
):
    # Scenario: Observation input yields updating an out of garrison activity
    # that has non overlapping time with observation
    mock_activity_response = MagicMock()
    mock_activity_response.data = [out_garrison_activity1]
    mock_get_activities.return_value = mock_activity_response

    mock_observation_response = MagicMock()
    mock_observation_response.data = []
    mock_get_observations.return_value = mock_observation_response

    rule = InOrOutOfGarrison("garrison rule")

    rule.action(RuleContext(observation=observational_node2))

    mock_gql_query.assert_called_once()

    garrison_buffer_points = generate_circle_points_geographical(
        geo_attribute1.geometry["coordinates"][1],
        geo_attribute1.geometry["coordinates"][0],
        SETTINGS.garrison_distance_kilometers,
    )
    garrison_buffer_geojson = {"type": "Polygon", "coordinates": [garrison_buffer_points]}

    mock_get_observations.assert_called_with(
        ObservationQuery(
            nodeIds=UuidQueryByList(in_=["initial_object_id"]),
            startTime=TimeQuery(gte="2024-01-01T00:00:00+00:00"),
            endTime=TimeQuery(lt="2025-01-01T00:00:00+00:00"),
            geometry=GeoQuery(queryGeoJson=garrison_buffer_geojson, queryType=GeoQueryType.INTERSECTS),
        )
    )
    mock_update_activity.assert_called_with(
        UpdateActivityInput(
            id=out_garrison_activity1.id,
            startTime=observational_node2.startTime,
            endTime=out_garrison_activity1.endTime,
            observationIds=UpdateUuidList(add=[observational_node2.id]),
            nodeId=observational_node2.nodeId,
        )
    )
