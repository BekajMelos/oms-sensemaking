import copy
from unittest.mock import MagicMock

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    ActivityActivity,
    AttributeAttribute,
    AttributeQuery,
    AttributeType,
    Confidence,
    CreateActivityInput,
    CreateAttributeInput,
    GeoQuery,
    GeoQueryType,
    NodeNode,
    ObservationObservation,
    ObservationQuery,
    StringQuery,
    TimeQuery,
    UpdateActivityInput,
    UpdateAttributeInput,
    UpdateUuidList,
)
from pytest_mock import MockerFixture
from shapely.geometry import shape

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.incursions import Incursion
from oms_sensemaking.inference.rules.rule_context import RuleContext
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
    attr.activityId = "incActi1"
    attr.geometry = areas_of_interest[0].geometry_dict
    attr.valueStart = "2024-01-01T00:00:00+00:00"
    attr.valueEnd = "2024-05-01T00:00:00+00:00"
    attr.labels = []
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
    attr.activityId = "incActi2"
    attr.geometry = areas_of_interest[0].geometry_dict
    attr.valueStart = "2022-01-01T00:00:00+00:00"
    attr.valueEnd = "2023-01-01T00:00:00+00:00"
    attr.labels = []
    return attr


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
    acti.startTime = "2024-01-01T00:00:00+00:00"
    acti.endTime = "2025-01-01T00:00:00+00:00"

    return acti


# Mock methods
@pytest.fixture
def mock_get_node(mocker: MockerFixture, incurring_object):
    mock_get_node = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.get_node")
    mock_get_node.return_value = incurring_object
    return mock_get_node


@pytest.fixture
def mock_get_attributes(mocker: MockerFixture):
    mock_get_attributes = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.get_attributes")
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = []
    mock_get_attributes.return_value = mock_attribute_response
    return mock_get_attributes


@pytest.fixture
def mock_create_attribute(mocker: MockerFixture):
    mock_create_attribute = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.create_attribute")
    return mock_create_attribute


@pytest.fixture
def mock_update_attribute(mocker: MockerFixture):
    mock_update_attribute = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.update_attribute")
    return mock_update_attribute


@pytest.fixture
def mock_get_activities(mocker: MockerFixture):
    mock_get_activities = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.get_activities")
    mock_activity_response = MagicMock()
    mock_activity = MagicMock()
    mock_activity.id = "incActi1"
    mock_activity.labels = []
    mock_activity_response.data = [mock_activity]
    mock_get_activities.return_value = mock_activity_response
    return mock_get_activities


@pytest.fixture
def mock_create_activity(mocker: MockerFixture, activity1):
    mock_create_activity = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.create_activity")
    mock_create_activity.return_value = activity1
    return mock_create_activity


@pytest.fixture
def mock_update_activity(mocker: MockerFixture):
    mock_update_activity = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.update_activity")
    return mock_update_activity


@pytest.fixture
def mock_get_observations(mocker: MockerFixture, observational_node_region1):
    mock_get_observations = mocker.patch("oms_sensemaking.clients.instances.oms_crud_tool.get_observations")
    mock_observation_response = MagicMock()
    mock_observation_response.data = [observational_node_region1]
    mock_get_observations.return_value = mock_observation_response
    return mock_get_observations


# Tests
def test_evaluate_input(observational_node_region1):
    """Test to verify valid inputs are recognized as such"""
    rule = Incursion("incursion rule", FakeAOIExtractor())

    # Rule should only be ran against observations
    assert not rule.evaluate(RuleContext()), "should only run for observations"

    # Input observations must include a nodeId and geometry
    assert rule.evaluate(RuleContext(observation=observational_node_region1)), "expected input to be valid"
    observation_without_parent = copy.deepcopy(observational_node_region1)
    observation_without_parent.nodeId = None
    assert not rule.evaluate(RuleContext(observation=observation_without_parent)), "expected input to be invalid"


def test_no_incursion(no_inc_observational_node, mock_get_node, mock_create_activity, mock_update_activity):
    # Scenario: Observation not in any area of interest, resulting in no creations or updates
    rule = Incursion("incursion rule", FakeAOIExtractor())

    rule.action(RuleContext(observation=no_inc_observational_node))
    mock_create_activity.assert_not_called()
    mock_update_activity.assert_not_called()


def test_new_incursion_region1(
    activity1,
    observational_node_region1,
    incurring_object,
    mock_get_node,
    mock_get_activities,
    mock_get_attributes,
    mock_create_activity,
    mock_create_attribute,
    areas_of_interest,
):
    # Scenario: Observation input yields new incursion and activity in region1
    rule = Incursion("incursion rule", FakeAOIExtractor())

    rule.action(RuleContext(observation=observational_node_region1))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIris=[SETTINGS.inference_incursion_attribute_iri],
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=areas_of_interest[0].geometry_dict),
            activityIds=[activity1.id],
            tags=SETTINGS.incursion_tags,
        )
    )
    mock_create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_incursion_attribute_iri,
            attributeValue="Incursion",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=observational_node_region1.confidence,
            sourceId=observational_node_region1.sourceId,  # change to config value
            activityId=activity1.id,
            acm=observational_node_region1.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                rule.version_string,
            ],
            geometry=areas_of_interest[0].geometry_dict,
            valueStart=observational_node_region1.startTime,
            valueEnd=observational_node_region1.endTime,
        )
    )
    mock_create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region1.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                rule.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name="Incursion",
            description="test feature name",
            state=SETTINGS.inference_incursion_activity_state,
            nodeId=observational_node_region1.nodeId,
            observationIds=[observational_node_region1.id],
            startTime=observational_node_region1.startTime,
            endTime=observational_node_region1.endTime,
        )
    )


def test_new_incursion_region2(
    activity1,
    observational_node_region2,
    incurring_object,
    mock_get_node,
    mock_get_activities,
    mock_get_attributes,
    mock_create_activity,
    mock_create_attribute,
    areas_of_interest,
):
    # Scenario: Observation input yields new incursion and activity in region2
    rule = Incursion("incursion rule", FakeAOIExtractor())

    rule.action(RuleContext(observation=observational_node_region2))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIris=[SETTINGS.inference_incursion_attribute_iri],
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=areas_of_interest[1].geometry_dict),
            activityIds=[activity1.id],
            tags=SETTINGS.incursion_tags,
        )
    )
    mock_create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_incursion_attribute_iri,
            attributeValue="Incursion",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=observational_node_region2.confidence,
            sourceId=observational_node_region2.sourceId,
            activityId=activity1.id,
            acm=observational_node_region2.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                rule.version_string,
            ],
            geometry=areas_of_interest[1].geometry_dict,
            valueStart=observational_node_region2.startTime,
            valueEnd=observational_node_region2.endTime,
        )
    )
    mock_create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region2.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                rule.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name="Incursion",
            description=f"Incursion Activity by {incurring_object.name}",
            state=SETTINGS.inference_incursion_activity_state,
            nodeId=observational_node_region2.nodeId,
            observationIds=[observational_node_region2.id],
            startTime=observational_node_region2.startTime,
            endTime=observational_node_region2.endTime,
        )
    )


def test_two_existing_incursions(
    activity1,
    observational_node_region1,
    incurring_object,
    attribute1,
    attribute2,
    mock_get_node,
    mock_get_attributes,
    mock_get_activities,
    mock_get_observations,
    mock_update_attribute,
    mock_update_activity,
    areas_of_interest,
):
    # Scenario: Two existing incursion attributes with same geo of interest- one that
    # is part of an incursion separate from the observation and one that is part of an
    # incursion including the observation, resulting in an attribute/activity update
    rule = Incursion("incursion rule", FakeAOIExtractor())
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = [attribute2, attribute1]
    mock_get_attributes.return_value = mock_attribute_response

    rule.action(RuleContext(observation=observational_node_region1))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIris=[SETTINGS.inference_incursion_attribute_iri],
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=areas_of_interest[0].geometry_dict),
            activityIds=[activity1.id],
            tags=SETTINGS.incursion_tags,
        )
    )

    mock_get_observations.assert_called_with(
        ObservationQuery(
            nodeId=[incurring_object.id],
            startTime=TimeQuery(gt=attribute2.valueEnd),
            endTime=TimeQuery(lte=observational_node_region1.startTime),
            geometry=GeoQuery(queryGeoJson=areas_of_interest[0].geometry_dict, queryType=GeoQueryType.DISJOINT),
        )
    )
    mock_update_attribute.assert_called_with(
        UpdateAttributeInput(
            id=attribute1.id,
            valueStart=observational_node_region1.startTime,
            valueEnd=observational_node_region1.endTime,
            labels=[SETTINGS.sm_enriched_label],
        )
    )
    mock_update_activity.assert_called_with(
        UpdateActivityInput(
            id="incActi1",
            observationIds=UpdateUuidList(add=[observational_node_region1.id]),
            startTime=observational_node_region1.startTime,
            endTime=observational_node_region1.endTime,
            labels=[SETTINGS.sm_enriched_label],
        )
    )


def test_existing_incursion_nonoverlapping_time(
    observational_node_region1,
    incurring_object,
    attribute2,
    mock_get_node,
    mock_get_attributes,
    mock_get_activities,
    mock_get_observations,
    mock_update_attribute,
    mock_update_activity,
    areas_of_interest,
):
    # Scenario: One existing incursion attribute exists matching observation's geo of interest
    # with nonoverlapping time, resulting in attribute/activity updates
    rule = Incursion("incursion rule", FakeAOIExtractor())

    mock_observation_response = MagicMock()
    mock_observation_response.data = []
    mock_get_observations.return_value = mock_observation_response
    mock_attribute_response = MagicMock()
    mock_attribute_response.data = [attribute2]
    mock_get_attributes.return_value = mock_attribute_response

    rule.action(RuleContext(observation=observational_node_region1))
    mock_get_observations.assert_called_with(
        ObservationQuery(
            nodeId=[incurring_object.id],
            startTime=TimeQuery(gt=attribute2.valueEnd),
            endTime=TimeQuery(lte=observational_node_region1.startTime),
            geometry=GeoQuery(queryGeoJson=areas_of_interest[0].geometry_dict, queryType=GeoQueryType.DISJOINT),
        )
    )
    mock_update_attribute.assert_called_with(
        UpdateAttributeInput(
            id=attribute2.id,
            valueStart=attribute2.valueStart,
            valueEnd=observational_node_region1.endTime,
            labels=[
                SETTINGS.sm_enriched_label,
            ],
        )
    )
    mock_update_activity.assert_called_with(
        UpdateActivityInput(
            id="incActi1",
            observationIds=UpdateUuidList(add=[observational_node_region1.id]),
            startTime=attribute2.valueStart,
            endTime=observational_node_region1.endTime,
            labels=[SETTINGS.sm_enriched_label],
        )
    )


def test_new_incursion_region3(
    activity1,
    observational_node_region3,
    incurring_object,
    mock_get_node,
    mock_get_activities,
    mock_get_attributes,
    mock_create_activity,
    mock_create_attribute,
    areas_of_interest,
):
    # Scenario: Observation input yields new incursion and activity in region2
    rule = Incursion("incursion rule", FakeAOIExtractor())

    rule.action(RuleContext(observation=observational_node_region3))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIris=[SETTINGS.inference_incursion_attribute_iri],
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=areas_of_interest[2].geometry_dict),
            activityIds=[activity1.id],
            tags=SETTINGS.incursion_tags,
        )
    )
    mock_create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_incursion_attribute_iri,
            attributeValue="Incursion",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=observational_node_region3.confidence,
            sourceId=observational_node_region3.sourceId,
            activityId=activity1.id,
            acm=observational_node_region3.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                rule.version_string,
            ],
            geometry=areas_of_interest[2].geometry_dict,
            valueStart=observational_node_region3.startTime,
            valueEnd=observational_node_region3.endTime,
        )
    )
    mock_create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region3.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                rule.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name="Incursion",
            description="Pentagon Polygon",
            state=SETTINGS.inference_incursion_activity_state,
            nodeId=observational_node_region3.nodeId,
            observationIds=[observational_node_region3.id],
            startTime=observational_node_region3.startTime,
            endTime=observational_node_region3.endTime,
        )
    )


def test_new_incursion_region4(
    activity1,
    observational_node_region4,
    incurring_object,
    mock_get_node,
    mock_get_activities,
    mock_get_attributes,
    mock_create_activity,
    mock_create_attribute,
    areas_of_interest,
):
    # Scenario: Observation input yields new incursion and activity in region2
    rule = Incursion("incursion rule", FakeAOIExtractor())

    rule.action(RuleContext(observation=observational_node_region4))
    mock_get_attributes.assert_called_with(
        AttributeQuery(
            attributeIris=[SETTINGS.inference_incursion_attribute_iri],
            attributeValue=StringQuery(equals="Incursion"),
            attributeType={"is": AttributeType.GEOSPATIAL},
            geometry=GeoQuery(queryGeoJson=areas_of_interest[3].geometry_dict),
            activityIds=[activity1.id],
            tags=SETTINGS.incursion_tags,
        )
    )
    mock_create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.inference_incursion_attribute_iri,
            attributeValue="Incursion",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=observational_node_region4.confidence,
            sourceId=observational_node_region4.sourceId,
            activityId=activity1.id,
            acm=observational_node_region4.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                rule.version_string,
            ],
            geometry=areas_of_interest[3].geometry_dict,
            valueStart=observational_node_region4.startTime,
            valueEnd=observational_node_region4.endTime,
        )
    )
    mock_create_activity.assert_called_with(
        CreateActivityInput(
            acm=observational_node_region4.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                rule.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name="Incursion",
            description="Pentagon",
            state=SETTINGS.inference_incursion_activity_state,
            nodeId=observational_node_region4.nodeId,
            observationIds=[observational_node_region4.id],
            startTime=observational_node_region4.startTime,
            endTime=observational_node_region4.endTime,
        )
    )
