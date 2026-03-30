import time
import uuid
from datetime import datetime

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    ActivityQuery,
    AttributeQuery,
    CreateNodeInput,
    CreateObservationInput,
    CreateOriginatorInput,
    CreateProviderInput,
    CreateSourceInput,
    ObjectTier,
    UuidQueryByList,
)

from oms_sensemaking.clients.instances import oms_crud_tool


@pytest.fixture
def inject_tags():
    return [f"incursion_test_{int(time.time())}"]


@pytest.fixture
def tester_db(inject_tags):
    unique_id = str(uuid.uuid4())[:8]

    originator = oms_crud_tool.create_originator(
        CreateOriginatorInput(name=f"test_{unique_id}", description="test", tags=inject_tags, acm=DEFAULT_ACM)
    )
    provider = oms_crud_tool.create_provider(
        CreateProviderInput(
            name=f"provider1_{unique_id}",
            description="test",
            tags=inject_tags,
            originatorId=originator.id,
            acm=DEFAULT_ACM,
        )
    )
    source = oms_crud_tool.create_source(
        CreateSourceInput(
            name=f"Source A_{unique_id}",
            description="test",
            providerId=provider.id,
            acm=DEFAULT_ACM,
            identifier=f"ABC_{unique_id}",
            dateOfReport=datetime.now().strftime(format="%Y-%m-%dT%H:%M:%S.000Z"),
            dateOfInformation=datetime.now().strftime(format="%Y-%m-%dT%H:%M:%S.000Z"),
            dataAcm=DEFAULT_ACM,
            tags=inject_tags,
        )
    )

    node1 = oms_crud_tool.create_node(
        CreateNodeInput(
            acm=DEFAULT_ACM,
            name=f"test node1_{unique_id}",
            tier=ObjectTier.PRIMARY,
            tags=inject_tags,
            classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft",
            allegiance="AUS",
            labels=[],
        )
    )

    node2 = oms_crud_tool.create_node(
        CreateNodeInput(
            acm=DEFAULT_ACM,
            name=f"test node2_{unique_id}",
            tier=ObjectTier.PRIMARY,
            tags=inject_tags,
            classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Watercraft",
            allegiance="AUS",
            labels=[],
        )
    )
    yield {"nodes": [node1, node2], "source": source}

    oms_crud_tool.delete_node(node1.id)
    oms_crud_tool.delete_node(node2.id)
    oms_crud_tool.delete_source(source.id)
    oms_crud_tool.delete_provider(provider.id)
    oms_crud_tool.delete_originator(originator.id)


def test_incursion_includes_node_observation_query(tester_db):
    """Test that new observations are appended to the existing node properly.

    This test ensure that a bug was fixed where checking for observations outside of the area of interest
    in GeoTimeframe.object_observed_between_generic_node_and_observation_times did not account for the nodeId
    """
    node1 = tester_db["nodes"][0]
    node2 = tester_db["nodes"][1]
    source = tester_db["source"]

    obs1 = oms_crud_tool.create_observation(
        CreateObservationInput(
            nodeId=node1.id,
            startTime="2025-08-26T16:10:00.000Z",
            endTime="2025-08-26T16:10:00.000Z",
            geometry={"type": "Point", "coordinates": [-155.65093863031944, 19.695942501190544]},
            classIri="http://www.ontologyrepository.com/CommonCoreOntologies/ObjectTrackPoint",
            acm=DEFAULT_ACM,
            sourceId=source.id,
        )
    )

    separate_obs = oms_crud_tool.create_observation(
        CreateObservationInput(
            nodeId=node2.id,
            startTime="2025-08-26T16:14:00.000Z",
            endTime="2025-08-26T16:14:00.000Z",
            geometry={"type": "Point", "coordinates": [0, 0]},
            classIri="http://www.ontologyrepository.com/CommonCoreOntologies/ObjectTrackPoint",
            acm=DEFAULT_ACM,
            sourceId=source.id,
        )
    )

    obs2 = oms_crud_tool.create_observation(
        CreateObservationInput(
            nodeId=node1.id,
            startTime="2025-08-26T16:15:00.000Z",
            endTime="2025-08-26T16:15:00.000Z",
            geometry={"type": "Point", "coordinates": [-155.63446316240285, 19.69958260215077]},
            classIri="http://www.ontologyrepository.com/CommonCoreOntologies/ObjectTrackPoint",
            acm=DEFAULT_ACM,
            sourceId=source.id,
        )
    )

    time.sleep(3.0)

    activities = []
    activity_query = ActivityQuery(nodeIds=UuidQueryByList(in_=[node1.id]))
    activity_response = oms_crud_tool.get_activities(activity_query)
    if activity_response.data:
        activities = activity_response.data

    try:
        assert len(activities) == 1
        assert activities[0].startTime == "2025-08-26T16:10:00.000Z"
        assert activities[0].endTime == "2025-08-26T16:15:00.000Z"
    finally:
        observations = [obs1, separate_obs, obs2]
        for observation in observations:
            oms_crud_tool.delete_observation(observation.id)

        for activity in activities:
            attribute_query = AttributeQuery(activityIds=[activity.id])
            attribute_response = oms_crud_tool.get_attributes(attribute_query)
            for attribute in attribute_response.data:
                oms_crud_tool.delete_attribute(attribute.id)

            oms_crud_tool.delete_activity(activity.id)
