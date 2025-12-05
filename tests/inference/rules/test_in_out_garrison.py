import copy
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivitiesData,
    AttributeAttribute,
    AttributeType,
    Confidence,
    CreateActivityInput,
    GeoQueryType,
    NodeNode,
    ObservationObservation,
    RelationshipRelationship,
    UpdateActivityInput,
    UpdateUuidList,
)
from oms_sdk.generated.generated_graphql_client.client import Client
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.geo_helpers import generate_circle_points_geographical
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.inference.rules.in_out_garrison import InOrOutOfGarrison


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
def mock_oms_client():
    return MagicMock(spec=Client)


@pytest.fixture
def mock_crud_tool(mock_oms_client):
    oms_crud_tool = OmsCrudTool()
    oms_crud_tool.oms_client = mock_oms_client

    return oms_crud_tool


@pytest.fixture
def broken_observation(mocker: MockerFixture):
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
    obs.startTime = None
    obs.endTime = "2025-01-01T00:00:00+00:00"

    return obs


def make_in_out_garrison_response(coords):
    # attr.geometry must be a dict with "coordinates"
    geo_attr = SimpleNamespace(geometry={"type": "Point", "coordinates": coords})
    end_node = SimpleNamespace(attributes=SimpleNamespace(data=[geo_attr]))
    rel = SimpleNamespace(endNode=end_node)
    relationships = SimpleNamespace(data=[rel])
    return SimpleNamespace(relationships=relationships)


# Tests
def test_evaluate_input(observational_node, mock_crud_tool, broken_observation):
    """Test to verify valid inputs are recognized as such"""
    garr_sm = InOrOutOfGarrison(mock_crud_tool)

    # Rule should only be ran against observations
    assert not garr_sm.evaluate(broken_observation), "should only run for observations"

    # Input observations must include a nodeId and geometry
    assert garr_sm.evaluate(obs=observational_node), "expected input to be valid"
    observation_without_parent = copy.deepcopy(observational_node)
    observation_without_parent.nodeId = None
    assert not garr_sm.evaluate(obs=observation_without_parent), "expected input to be invalid"


def test_no_relationship_no_op(mocker, mock_crud_tool, observational_node, mock_get_node, mock_create_activity):
    payload = {"node": {"relationships": {"data": []}}}
    mocker.patch(
        "oms_sensemaking.clients.instances.oms_crud_tool.oms_client.in_out_garrison_with_geo",
        new=MagicMock(return_value=payload),
    )
    garr_sm = InOrOutOfGarrison(mock_crud_tool)

    garr_sm.process_data(obs=observational_node)
    mock_create_activity.assert_not_called()


def test_no_geo_attr_no_op(
    mocker, mock_crud_tool, observational_node, garrison_object, mock_get_node, mock_create_activity
):
    payload = {
        "node": {"relationships": {"data": [{"endNode": {"id": garrison_object.id, "attributes": {"data": []}}}]}}
    }
    mocker.patch(
        "oms_sensemaking.clients.instances.oms_crud_tool.oms_client.in_out_garrison_with_geo",
        new=MagicMock(return_value=payload),
    )
    garr_sm = InOrOutOfGarrison(mock_crud_tool)

    garr_sm.process_data(obs=observational_node)
    mock_create_activity.assert_not_called()


def test_new_in_garrison(
    mock_crud_tool,
    observational_node,
    garrison_object,
    mock_get_node,
    mock_get_activities,
    mock_create_activity,
    geo_attribute1,
):
    # Make the mocked GQL call return a shape compatible with the helper
    mock_crud_tool.oms_client.in_out_garrison_with_geo.return_value = make_in_out_garrison_response(
        geo_attribute1.geometry["coordinates"]
    )

    # Scenario: Observation input yields new in garrison activity
    garr_sm = InOrOutOfGarrison(mock_crud_tool)
    garr_sm.process_data(obs=observational_node)

    mock_crud_tool.oms_client.in_out_garrison_with_geo.assert_called_once_with(
        id=observational_node.nodeId,
        garrisonIris=[SETTINGS.inference_garrisoned_in_iri],
        geoIris=[SETTINGS.inference_geo_attribute_iri],
    )

    mock_crud_tool.oms_client.create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node.acm,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.garrison_sm_label,
                garr_sm.version_string,
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
    mock_crud_tool,
    observational_node2,
    garrison_object,
    mock_get_node,
    mock_get_activities,
    mock_create_activity,
    geo_attribute1,
):
    # Make the mocked GQL call return a shape compatible with the helper
    mock_crud_tool.oms_client.in_out_garrison_with_geo.return_value = make_in_out_garrison_response(
        geo_attribute1.geometry["coordinates"]
    )
    # Scenario: Observation input yields new out of garrison activity
    garr_sm = InOrOutOfGarrison(mock_crud_tool)
    garr_sm.process_data(obs=observational_node2)

    mock_crud_tool.oms_client.in_out_garrison_with_geo.assert_called_once_with(
        id=observational_node2.nodeId,
        garrisonIris=[SETTINGS.inference_garrisoned_in_iri],
        geoIris=[SETTINGS.inference_geo_attribute_iri],
    )

    mock_crud_tool.oms_client.create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node2.acm,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.garrison_sm_label,
                garr_sm.version_string,
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
    mock_crud_tool,
    observational_node,
    garrison_object,
    mock_get_node,
    mock_get_activities,
    mock_get_observations,
    mock_update_activity,
    geo_attribute1,
    in_garrison_activity1,
    in_garrison_activity2,
):
    # Scenario: Observation input yields updating an in garrison activity
    mock_activity_response = MagicMock()
    mock_activity_response.data = [in_garrison_activity1, in_garrison_activity2]
    mock_crud_tool.oms_client.activities.return_value = mock_activity_response

    garr_sm = InOrOutOfGarrison(mock_crud_tool)
    mock_crud_tool.oms_client.in_out_garrison_with_geo.return_value = make_in_out_garrison_response(
        coords=geo_attribute1.geometry["coordinates"]
    )
    garr_sm.process_data(obs=observational_node)

    # single call now
    mock_crud_tool.oms_client.in_out_garrison_with_geo.assert_called_once_with(
        id=observational_node.nodeId,
        garrisonIris=[SETTINGS.inference_garrisoned_in_iri],
        geoIris=[SETTINGS.inference_geo_attribute_iri],
    )

    garrison_buffer_points = generate_circle_points_geographical(
        geo_attribute1.geometry["coordinates"][1],
        geo_attribute1.geometry["coordinates"][0],
        SETTINGS.garrison_distance_kilometers,
    )
    garrison_buffer_geojson = {"type": "Polygon", "coordinates": [garrison_buffer_points]}

    args, kwargs = mock_get_observations.call_args
    obs_query_arg = args[0]
    assert isinstance(obs_query_arg.nodeIds.in_[0], MagicMock)
    assert obs_query_arg.startTime.gt == "2023-01-01T00:00:00+00:00"
    assert obs_query_arg.endTime.lte == "2025-01-01T00:00:00+00:00"
    assert obs_query_arg.geometry.queryGeoJson == garrison_buffer_geojson
    assert obs_query_arg.geometry.queryType == GeoQueryType.DISJOINT

    mock_crud_tool.oms_client.update_activity.assert_called_with(
        UpdateActivityInput(
            id=in_garrison_activity2.id,
            startTime=in_garrison_activity2.startTime,
            endTime=in_garrison_activity2.endTime,
            observationIds=UpdateUuidList(add=[observational_node.id]),
            nodeId=observational_node.nodeId,
        )
    )


def test_update_out_garrison(
    mock_crud_tool,
    observational_node2,
    garrison_object,
    mock_get_node,
    mock_get_activities,
    mock_get_observations,
    mock_update_activity,
    geo_attribute1,
    out_garrison_activity1,
):
    # Scenario: Observation input yields updating an out of garrison activity
    # that has non overlapping time with observation
    mock_activity_response = MagicMock()
    mock_activity_response.data = [out_garrison_activity1]
    mock_crud_tool.oms_client.activities.return_value = mock_activity_response

    mock_observation_response = MagicMock()
    mock_observation_response.data = []
    mock_get_observations.return_value = mock_observation_response

    garr_sm = InOrOutOfGarrison(mock_crud_tool)
    mock_crud_tool.oms_client.in_out_garrison_with_geo.return_value = make_in_out_garrison_response(
        coords=geo_attribute1.geometry["coordinates"]
    )
    garr_sm.process_data(obs=observational_node2)

    mock_crud_tool.oms_client.in_out_garrison_with_geo.assert_called_once_with(
        id=observational_node2.nodeId,
        garrisonIris=[SETTINGS.inference_garrisoned_in_iri],
        geoIris=[SETTINGS.inference_geo_attribute_iri],
    )

    garrison_buffer_points = generate_circle_points_geographical(
        geo_attribute1.geometry["coordinates"][1],
        geo_attribute1.geometry["coordinates"][0],
        SETTINGS.garrison_distance_kilometers,
    )
    garrison_buffer_geojson = {"type": "Polygon", "coordinates": [garrison_buffer_points]}

    args, kwargs = mock_get_observations.call_args
    obs_query_arg = args[0]
    assert isinstance(obs_query_arg.nodeIds.in_[0], MagicMock)
    assert obs_query_arg.startTime.gte == "2024-01-01T00:00:00+00:00"
    assert obs_query_arg.endTime.lt == "2025-01-01T00:00:00+00:00"
    assert obs_query_arg.geometry.queryGeoJson == garrison_buffer_geojson
    assert obs_query_arg.geometry.queryType == GeoQueryType.INTERSECTS

    mock_crud_tool.oms_client.update_activity.assert_called_with(
        UpdateActivityInput(
            id=out_garrison_activity1.id,
            startTime=observational_node2.startTime,
            endTime=out_garrison_activity1.endTime,
            observationIds=UpdateUuidList(add=[observational_node2.id]),
            nodeId=observational_node2.nodeId,
        )
    )
