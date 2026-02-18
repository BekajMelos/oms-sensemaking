import copy
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    ActivityActivity,
    ActivityQuery,
    Confidence,
    CreateActivityInput,
    GeoQuery,
    GeoQueryType,
    IncursionDataActivities,
    IncursionDataActivitiesData,
    NodeNode,
    ObservationObservation,
    ObservationQuery,
    PageParams,
    StringQuery,
    TimeQuery,
    UpdateActivityInput,
    UpdateUuidList,
    UuidQueryByList,
)
from oms_sdk.generated.generated_graphql_client.client import Client
from pytest_mock import MockerFixture
from shapely.geometry import shape

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.inference.rules.incursions import Incursion, IncursionSensemaker
from tests.domain.area_of_interest.test_aoi_extractor import FakeAOIExtractor


@pytest.fixture
def areas_of_interest(observational_node_region1, observational_node_region2, observational_node_region3):
    # Done this way since there is no way to tell which AOI will be what index
    # We just grab the folder as a whole
    extractor = FakeAOIExtractor()
    aois = extractor.get_areas_of_interest()
    test_aois = [None] * len(aois)
    for aoi in aois:
        if aoi.has_overlap(shape(observational_node_region1.geometry)):
            test_aois[0] = aoi
        elif aoi.has_overlap(shape(observational_node_region2.geometry)):
            test_aois[1] = aoi
        elif aoi.has_overlap(shape(observational_node_region3.geometry)):
            test_aois[2] = aoi
        else:
            test_aois[3] = aoi
    return test_aois


@pytest.fixture
def observational_node_region1(mocker: MockerFixture):
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
    obs.nodeId = "incurring_object_id"
    obs.geometry = geometry
    obs.startTime = "2024-01-01T00:00:00+00:00"
    obs.endTime = "2025-01-01T00:00:00+00:00"

    return obs


@pytest.fixture
def observational_node_region2(mocker: MockerFixture):
    """
    Incoming observation
    """
    geometry = {"coordinates": [-152.16868319466693, 23.556473770341952], "type": "Point"}

    obs = mocker.Mock(spec=ObservationObservation)
    obs.id = "obs_id"
    obs.version = "version"
    obs.acm = "acm"
    obs.classIri = "classIri"
    obs.className = "className"
    obs.confidence = Confidence.MODERATE
    obs.sourceId = "obs_sourceId"
    obs.nodeId = "incurring_object_id"
    obs.geometry = geometry
    obs.startTime = "2024-01-01T00:00:00+00:00"
    obs.endTime = "2025-01-01T00:00:00+00:00"

    return obs


@pytest.fixture
def observational_node_region3(mocker: MockerFixture):
    """
    Incoming observation
    """
    geometry = {"coordinates": [-122.083, 37.421], "type": "Point"}

    obs = mocker.Mock(spec=ObservationObservation)
    obs.id = "obs_id"
    obs.version = "version"
    obs.acm = "acm"
    obs.classIri = "classIri"
    obs.className = "className"
    obs.confidence = Confidence.MODERATE
    obs.sourceId = "obs_sourceId"
    obs.nodeId = "incurring_object_id"
    obs.geometry = geometry
    obs.startTime = "2024-01-01T00:00:00+00:00"
    obs.endTime = "2025-01-01T00:00:00+00:00"

    return obs


@pytest.fixture
def observational_node_region4(mocker: MockerFixture):
    """
    Incoming observation
    """
    geometry = {"coordinates": [-77.0587192, 38.8696377], "type": "Point"}

    obs = mocker.Mock(spec=ObservationObservation)
    obs.id = "obs_id"
    obs.version = "version"
    obs.acm = "acm"
    obs.classIri = "classIri"
    obs.className = "className"
    obs.confidence = Confidence.MODERATE
    obs.sourceId = "obs_sourceId"
    obs.nodeId = "incurring_object_id"
    obs.geometry = geometry
    obs.startTime = "2024-01-01T00:00:00+00:00"
    obs.endTime = "2025-01-01T00:00:00+00:00"

    return obs


@pytest.fixture
def no_inc_observational_node(mocker: MockerFixture):
    """
    Incoming observation
    """
    geometry = {"coordinates": [-150.93829627954565, 20.83888460523758], "type": "Point"}

    obs = mocker.Mock(spec=ObservationObservation)
    obs.id = "obs_id"
    obs.version = "version"
    obs.acm = "acm"
    obs.classIri = "classIri"
    obs.className = "className"
    obs.confidence = Confidence.MODERATE
    obs.sourceId = "obs_sourceId"
    obs.nodeId = "incurring_object_id"
    obs.geometry = geometry
    obs.startTime = "2024-01-01T00:00:00+00:00"
    obs.endTime = "2025-01-01T00:00:00+00:00"

    return obs


@pytest.fixture
def incurring_object(mocker: MockerFixture):
    """
    A parent node of observational_node_region1
    """
    node = mocker.Mock(spec=NodeNode)
    node.id = "incurring_object_id"
    node.name = "Base Node"
    node.geoQuery = "some query"
    node.relationships = "another query"
    node.tier = "DERIVATIVE"

    return node


@pytest.fixture
def activity1(mocker: MockerFixture):
    acti = mocker.Mock(spec=ActivityActivity)
    acti.id = "incActi1"
    acti.acm = DEFAULT_ACM
    acti.classIri = SETTINGS.inference_incursion_class_iri
    acti.name = "Incursion"
    acti.state = SETTINGS.inference_incursion_activity_state
    acti.nodeId = "incurring_object_id"
    acti.observationIds = ["obs_id"]
    acti.startTime = "2022-01-01T00:00:00+00:00"
    acti.endTime = "2023-01-01T00:00:00+00:00"
    acti.labels = None

    return acti


@pytest.fixture
def mock_get_observations(mocker: MockerFixture, observational_node_region1):
    mock_get_observations = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.get_observations")
    mock_observation_response = MagicMock()
    mock_observation_response.data = [observational_node_region1]
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


@pytest.fixture
def test_observation():
    observation = ObservationObservation(
        id=uuid4(),
        version="version",
        acm="acm",
        tags=["tag"],
        labels=["label"],
        classIri="iri",
        className="name",
        displayValue="value",
        confidence=Confidence.HIGH,
        sourceId=uuid4(),
        nodeId=uuid4(),
        geometry={
            "type": "Point",
            "coordinates": [-2.765882, 54.887295, 0.0],
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        },
        startTime="2024-01-01T00:00:00+00:00",
        endTime="2024-01-01T00:00:00+00:00",
    )
    return observation


@pytest.fixture
def test_incursion(test_observation, areas_of_interest):
    test_incursion = Incursion(
        incurring_obj_id=test_observation.nodeId,
        incursion_observation=test_observation,
        start_time=test_observation.startTime,
        end_time=test_observation.endTime,
        area_of_interest_dict=areas_of_interest[0].geometry_dict,
        acm=test_observation.acm,
    )
    return test_incursion


# Tests
def test_incursion_methods(test_incursion, areas_of_interest):
    assert test_incursion.get_acm() == test_incursion.acm

    assert test_incursion.__str__() == str(test_incursion.to_dict())

    assert test_incursion.__repr__() == test_incursion.__str__()

    assert test_incursion.to_geojson() == {
        "type": "Point",
        "coordinates": test_incursion.incursion_observation.geometry["coordinates"],
    }


def test_evaluate_input(observational_node_region1, observation_with_missing_start_time, mock_crud_tool):
    """Test to verify valid inputs are recognized as such"""
    incur_sm = IncursionSensemaker(FakeAOIExtractor(), mock_crud_tool)

    # Rule should only be ran against observations
    assert not incur_sm.evaluate(observation_with_missing_start_time), "should only run for observations"

    # Input observations must include a nodeId and geometry
    assert incur_sm.evaluate(obs=observational_node_region1), "expected input to be valid"
    observation_without_parent = copy.deepcopy(observational_node_region1)
    observation_without_parent.nodeId = None
    assert not incur_sm.evaluate(obs=observation_without_parent), "expected input to be invalid"


def test_no_incursion(no_inc_observational_node, mock_crud_tool):
    # Scenario: Observation not in any area of interest, resulting in no creations or updates
    incur_sm = IncursionSensemaker(FakeAOIExtractor(), mock_crud_tool)

    incur_sm.process_data(obs=no_inc_observational_node)
    mock_crud_tool.create_activity.assert_not_called()
    mock_crud_tool.update_activity.assert_not_called()


def test_get_incursion_data(observational_node_region1, mock_crud_tool, areas_of_interest):
    incur_sm = IncursionSensemaker(FakeAOIExtractor(), mock_crud_tool)
    # Fake activity objects (could be MagicMock or real dataclasses)
    activity1 = MagicMock(spec=IncursionDataActivitiesData)
    activity2 = MagicMock(spec=IncursionDataActivitiesData)
    activity3 = MagicMock(spec=IncursionDataActivitiesData)

    # Page 1 returns full page, page 2 returns partial and then stop
    responses = [
        IncursionDataActivities(data=[activity1, activity2]),  # page 1
        IncursionDataActivities(data=[activity3]),  # page 2
    ]
    mock_incursion_data = MagicMock(side_effect=responses)
    mock_crud_tool.oms_client.incursion_data = mock_incursion_data
    result = incur_sm.get_all_incursion_data(incurring_object_id=observational_node_region1.nodeId, pagesize=2)

    assert result == [activity1, activity2, activity3]
    assert mock_crud_tool.oms_client.incursion_data.call_count == 2


def test_new_incursion_region1(
    activity1, observational_node_region1, incurring_object, areas_of_interest, mock_crud_tool
):
    # Scenario: Observation input yields new incursion and activity in region1
    incur_sm = IncursionSensemaker(FakeAOIExtractor(), mock_crud_tool)

    # mock response for triggering other calls
    mock_crud_tool.create_activity.return_value = activity1

    result = incur_sm.process_data(obs=observational_node_region1)

    mock_crud_tool.create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region1.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                incur_sm.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name="Incursion",
            description=f"Incursion Activity by object: {observational_node_region1.nodeId}",
            state=SETTINGS.inference_incursion_activity_state,
            sourceId=observational_node_region1.sourceId,
            nodeId=observational_node_region1.nodeId,
            observationIds=[observational_node_region1.id],
            startTime=observational_node_region1.startTime,
            endTime=observational_node_region1.endTime,
        )
    )
    assert isinstance(result[0], Incursion)
    assert result[0].incursion_observation == observational_node_region1


def test_new_incursion_region2(
    activity1, observational_node_region2, incurring_object, areas_of_interest, mock_crud_tool
):
    # Scenario: Observation input yields new incursion and activity in region2
    incur_sm = IncursionSensemaker(FakeAOIExtractor(), mock_crud_tool)

    # mock responses for triggering correct behavior
    mock_crud_tool.create_activity.return_value = activity1

    result = incur_sm.process_data(obs=observational_node_region2)
    mock_crud_tool.create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region2.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                incur_sm.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name="Incursion",
            description=f"Incursion Activity by object: {observational_node_region2.nodeId}",
            state=SETTINGS.inference_incursion_activity_state,
            sourceId=observational_node_region2.sourceId,
            nodeId=observational_node_region2.nodeId,
            observationIds=[observational_node_region2.id],
            startTime=observational_node_region2.startTime,
            endTime=observational_node_region2.endTime,
        )
    )
    assert isinstance(result[0], Incursion)
    assert result[0].incursion_observation == observational_node_region2


@patch("oms_sensemaking.inference.rules.incursions.aac_client")
def test_existing_incursion_nonoverlapping_time(
    mock_aac_client,
    observational_node_region1,
    incurring_object,
    mock_get_observations,
    areas_of_interest,
    activity1,
    mock_crud_tool,
):
    # Scenario: One existing incursion attribute exists matching observation's geo of interest
    # with nonoverlapping time, resulting in attribute/activity updates
    incur_sm = IncursionSensemaker(FakeAOIExtractor(), mock_crud_tool)

    response = SimpleNamespace(
        data=[
            SimpleNamespace(
                id=activity1.id,
                labels=activity1.labels,
                startTime=activity1.startTime,
                endTime=activity1.endTime,
                observations=SimpleNamespace(
                    data=[
                        SimpleNamespace(
                            id=observational_node_region1.id,
                            acm=observational_node_region1.acm,
                            geometry=observational_node_region1.geometry,
                        )
                    ]
                ),
            ),
        ]
    )
    mock_crud_tool.oms_client.incursion_data.return_value = response
    mock_aac_client.get_acm_rollup.return_value = observational_node_region1.acm

    mock_observation_response = MagicMock()
    mock_observation_response.data = []
    mock_get_observations.return_value = mock_observation_response

    result = incur_sm.process_data(obs=observational_node_region1)
    mock_crud_tool.oms_client.incursion_data.assert_called_with(
        ActivityQuery(
            classIris=[SETTINGS.inference_incursion_class_iri],
            name=StringQuery(equals="Incursion"),
            states=[SETTINGS.inference_incursion_activity_state],
            nodeIds=UuidQueryByList(in_=[incurring_object.id]),
            pageParams=PageParams(page=1, pageSize=200),
        )
    )
    mock_get_observations.assert_called_with(
        ObservationQuery(
            nodeIds=UuidQueryByList(in_=[incurring_object.id]),
            startTime=TimeQuery(gt=activity1.endTime),
            endTime=TimeQuery(lte=observational_node_region1.startTime),
            geometry=GeoQuery(queryGeoJson=areas_of_interest[0].geometry_dict, queryType=GeoQueryType.DISJOINT),
        )
    )
    mock_aac_client.get_acm_rollup.assert_has_calls(
        [call([{"ACM": observational_node_region1.acm}, {"ACM": observational_node_region1.acm}])]
    )

    mock_crud_tool.update_activity.assert_called_with(
        UpdateActivityInput(
            id="incActi1",
            acm=observational_node_region1.acm,
            observationIds=UpdateUuidList(add=[observational_node_region1.id]),
            startTime=activity1.startTime,
            endTime=observational_node_region1.endTime,
            labels=[SETTINGS.sm_enriched_label],
        )
    )
    assert isinstance(result[0], Incursion)
    assert result[0].acm == observational_node_region1.acm
    assert result[0].incursion_observation == observational_node_region1


def test_new_incursion_region3(
    activity1, observational_node_region3, incurring_object, areas_of_interest, mock_crud_tool
):
    # Scenario: Observation input yields new incursion and activity in region2
    incur_sm = IncursionSensemaker(FakeAOIExtractor(), mock_crud_tool)

    mock_crud_tool.create_activity.return_value = activity1

    result = incur_sm.process_data(obs=observational_node_region3)

    mock_crud_tool.create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region3.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                incur_sm.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name="Incursion",
            description=f"Incursion Activity by object: {observational_node_region3.nodeId}",
            state=SETTINGS.inference_incursion_activity_state,
            sourceId=observational_node_region3.sourceId,
            nodeId=observational_node_region3.nodeId,
            observationIds=[observational_node_region3.id],
            startTime=observational_node_region3.startTime,
            endTime=observational_node_region3.endTime,
        )
    )
    assert isinstance(result[0], Incursion)
    assert result[0].incursion_observation == observational_node_region3


def test_new_incursion_region4(
    activity1, observational_node_region4, incurring_object, areas_of_interest, mock_crud_tool
):
    # Scenario: Observation input yields new incursion and activity in region2
    incur_sm = IncursionSensemaker(FakeAOIExtractor(), mock_crud_tool)

    mock_crud_tool.create_activity.return_value = activity1

    result = incur_sm.process_data(obs=observational_node_region4)

    mock_crud_tool.create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region4.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                incur_sm.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name="Incursion",
            description=f"Incursion Activity by object: {observational_node_region4.nodeId}",
            state=SETTINGS.inference_incursion_activity_state,
            sourceId=observational_node_region4.sourceId,
            nodeId=observational_node_region4.nodeId,
            observationIds=[observational_node_region4.id],
            startTime=observational_node_region4.startTime,
            endTime=observational_node_region4.endTime,
        )
    )
    assert isinstance(result[0], Incursion)
    assert result[0].incursion_observation == observational_node_region4


def test_process_data_returns_empty_when_evaluate_fails(
    observation_with_missing_start_time,
    mock_crud_tool,
):
    incur_sm = IncursionSensemaker(FakeAOIExtractor(), mock_crud_tool)

    result = incur_sm.process_data(obs=observation_with_missing_start_time)

    assert result == []
    mock_crud_tool.create_activity.assert_not_called()
    # ensures we didn't attempt the expensive query
    mock_crud_tool.oms_client.incursion_data.assert_not_called()
