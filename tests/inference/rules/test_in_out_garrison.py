import copy
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivitiesData,
    AttributeAttribute,
    AttributeType,
    Confidence,
    CreateActivityInput,
    NodeNode,
    ObservationObservation,
    RelationshipRelationship,
    UpdateActivityInput,
    UpdateUuidList,
)
from oms_sdk.generated.generated_graphql_client.client import Client
from pytest_mock import MockerFixture

from oms_sensemaking.config import SETTINGS
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
    crud_tool = MagicMock(spec=OmsCrudTool)
    crud_tool.oms_client = mock_oms_client
    return crud_tool


@pytest.fixture
def observation_with_missing_start_time(mocker: MockerFixture):
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
def test_evaluate_input_obs_no_start_time(mock_crud_tool, observation_with_missing_start_time):
    """Test to verify valid inputs are recognized as such"""
    garr_sm = InOrOutOfGarrison(mock_crud_tool)

    # Rule should only be ran against observations
    assert not garr_sm.evaluate(observation_with_missing_start_time), "should only run for observations"


def test_evaluate_input_obs_no_node_id(observational_node, mock_crud_tool):
    garr_sm = InOrOutOfGarrison(mock_crud_tool)
    # Input observations must include a nodeId and geometry
    assert garr_sm.evaluate(obs=observational_node), "expected input to be valid"
    observation_without_parent = copy.deepcopy(observational_node)
    observation_without_parent.nodeId = None
    assert not garr_sm.evaluate(obs=observation_without_parent), "expected input to be invalid"


def test_no_relationship_no_op(mocker, observational_node, mock_crud_tool):
    payload = MagicMock()
    payload.relationships.data = []
    mocker.patch(
        "oms_sensemaking.clients.instances.oms_crud_tool.oms_client.in_out_garrison_with_geo",
        new=MagicMock(return_value=payload),
    )
    garr_sm = InOrOutOfGarrison(mock_crud_tool)

    garr_sm.process_data(obs=observational_node)
    mock_crud_tool.create_activity.assert_not_called()


def test_no_geo_attr_no_op(mocker, observational_node, garrison_object, mock_crud_tool):
    payload = MagicMock()
    payload.node.relationships.data.endNode = {"id": garrison_object.id}
    mocker.patch(
        "oms_sensemaking.clients.instances.oms_crud_tool.oms_client.in_out_garrison_with_geo",
        new=MagicMock(return_value=payload),
    )
    garr_sm = InOrOutOfGarrison(mock_crud_tool)

    garr_sm.process_data(obs=observational_node)
    mock_crud_tool.create_activity.assert_not_called()


@patch("oms_sensemaking.inference.rules.in_out_garrison.GetGarrisonDataAllAtOnce.get_all_garrison_data")
def test_new_in_garrison(
    mock_get_garrison_data,
    mock_crud_tool,
    observational_node,
    geo_attribute1,
):
    mock_get_garrison_data.return_value = SimpleNamespace(
        object_lat_lon=[
            observational_node.geometry["coordinates"][1],
            observational_node.geometry["coordinates"][0],
        ],
        garrison_lat_lon=[
            geo_attribute1.geometry["coordinates"][1],
            geo_attribute1.geometry["coordinates"][0],
        ],
        activities=[],
    )

    garr_sm = InOrOutOfGarrison(mock_crud_tool)
    garr_sm.process_data(obs=observational_node)

    mock_crud_tool.create_activity.assert_called_once()


@patch("oms_sensemaking.inference.rules.in_out_garrison.GetGarrisonDataAllAtOnce.get_all_garrison_data")
def test_new_out_garrison(
    mock_get_garrison_data,
    mock_crud_tool,
    observational_node2,
    geo_attribute1,
):
    mock_get_garrison_data.return_value = SimpleNamespace(
        object_lat_lon=[
            observational_node2.geometry["coordinates"][1],
            observational_node2.geometry["coordinates"][0],
        ],
        garrison_lat_lon=[
            geo_attribute1.geometry["coordinates"][1],
            geo_attribute1.geometry["coordinates"][0],
        ],
        activities=[],
    )

    garr_sm = InOrOutOfGarrison(mock_crud_tool)
    garr_sm.process_data(obs=observational_node2)

    # Assert: New Out of Garrison activity created
    mock_crud_tool.create_activity.assert_called_once_with(
        CreateActivityInput(
            acm=observational_node2.acm,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.garrison_sm_label,
                garr_sm.version_string,
            ],
            classIri=SETTINGS.inference_garrison_class_iri,
            name=SETTINGS.inference_out_of_garrison_activity_name,
            state=SETTINGS.inference_out_of_garrison_activity_state,
            nodeId=observational_node2.nodeId,
            observationIds=[observational_node2.id],
            startTime=observational_node2.startTime,
            endTime=observational_node2.endTime,
        )
    )


@patch(
    "oms_sensemaking.inference.rules.rule_helper_classes.GeoTimeframe.object_observed_between_generic_node_and_observation_times",
    return_value=False,
)
@patch("oms_sensemaking.inference.rules.in_out_garrison.GetGarrisonDataAllAtOnce.get_all_garrison_data")
def test_update_in_garrison(
    mock_get_garrison_data,
    mock_object_between,
    mock_crud_tool,
    observational_node,
    geo_attribute1,
    in_garrison_activity1,
    in_garrison_activity2,
):
    mock_get_garrison_data.return_value = SimpleNamespace(
        object_lat_lon=[
            observational_node.geometry["coordinates"][1],
            observational_node.geometry["coordinates"][0],
        ],
        garrison_lat_lon=[
            geo_attribute1.geometry["coordinates"][1],
            geo_attribute1.geometry["coordinates"][0],
        ],
        activities=[in_garrison_activity1, in_garrison_activity2],
    )

    garr_sm = InOrOutOfGarrison(mock_crud_tool)
    garr_sm.process_data(obs=observational_node)

    mock_crud_tool.update_activity.assert_called_once()


@patch(
    "oms_sensemaking.inference.rules.rule_helper_classes.GeoTimeframe.object_observed_between_generic_node_and_observation_times",
    return_value=True,
)
@patch("oms_sensemaking.inference.rules.in_out_garrison.GetGarrisonDataAllAtOnce.get_all_garrison_data")
def test_update_out_garrison(
    mock_get_garrison_data,
    mock_object_between,
    mock_crud_tool,
    observational_node2,
    geo_attribute1,
    out_garrison_activity1,
):
    # Observation input yields updating an out of garrison activity that has non overlapping time with observation
    mock_get_garrison_data.return_value = SimpleNamespace(
        object_lat_lon=[
            observational_node2.geometry["coordinates"][1],
            observational_node2.geometry["coordinates"][0],
        ],
        garrison_lat_lon=[
            geo_attribute1.geometry["coordinates"][1],
            geo_attribute1.geometry["coordinates"][0],
        ],
        activities=[out_garrison_activity1],
    )

    garr_sm = InOrOutOfGarrison(mock_crud_tool)
    garr_sm.process_data(obs=observational_node2)

    # Assert: existing activity updated, not recreated
    mock_crud_tool.update_activity.assert_called_once_with(
        UpdateActivityInput(
            id=out_garrison_activity1.id,
            startTime=observational_node2.startTime,
            endTime=out_garrison_activity1.endTime,
            observationIds=UpdateUuidList(add=[observational_node2.id]),
            nodeId=observational_node2.nodeId,
        )
    )

    mock_crud_tool.create_activity.assert_not_called()


@patch("oms_sensemaking.inference.rules.in_out_garrison.GetGarrisonDataAllAtOnce.get_all_garrison_data")
def test_has_action_already_ran_short_circuits(
    mock_get_garrison_data,
    mock_crud_tool,
    observational_node,
    in_garrison_activity1,
):
    """Test to verify has_action_already_ran"""
    in_garrison_activity1.observationIds = [observational_node.id]

    mock_get_garrison_data.return_value = SimpleNamespace(
        object_lat_lon=[0, 0],
        garrison_lat_lon=[0, 0],
        activities=[in_garrison_activity1],
    )

    garrison_rule = InOrOutOfGarrison(mock_crud_tool)
    garrison_rule.process_data(obs=observational_node)

    mock_crud_tool.create_activity.assert_not_called()
    mock_crud_tool.update_activity.assert_not_called()
