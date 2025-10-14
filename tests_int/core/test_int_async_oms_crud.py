import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_async_graphql_client import (
    CreateActivityInput,
    CreateNodeCreateNode,
    CreateNodeInput,
    CreateObservationInput,
    CreateOriginatorCreateOriginator,
    CreateOriginatorInput,
    CreateProviderCreateProvider,
    CreateProviderInput,
    CreateSourceCreateSource,
    CreateSourceInput,
    ObjectTier,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.async_atoms_crud import AsyncOmsCrudTool
from oms_sensemaking.core.oms_crud import OmsCrudTool as SyncOmsCrudTool


@pytest.fixture
def oms_crud_tool():
    return AsyncOmsCrudTool()


@pytest.fixture
def sync_oms_crud_tool():
    return SyncOmsCrudTool()


@pytest.fixture
def node_input():
    return CreateNodeInput(
        acm=DEFAULT_ACM,
        name="test create node",
        tier=ObjectTier.PRIMARY,
        domain=None,
        tags=SETTINGS.sm_test_tags,
        labels=[SETTINGS.loiter_sm_label],
        classIri=SETTINGS.loiter_event_node_iri,
        allegiance="USA",
    )


@pytest.fixture
def observation_input():
    return CreateObservationInput(
        acm=DEFAULT_ACM,
        labels=None,
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/GeospatialLocation",
        tags=SETTINGS.sm_test_tags,
        geometry={
            "type": "Point",
            "coordinates": [-77.04007, 38.85109],
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        },
    )


@pytest.fixture
def inject_tags():
    return SETTINGS.sm_test_tags


@pytest.fixture
def cleanup_data(inject_tags, sync_oms_crud_tool):
    """Cleanup method to destory anything in the database that might conflict with data created in this test"""
    yield
    tags = inject_tags

    sync_oms_crud_tool.delete_observations_by_tags(tags)
    sync_oms_crud_tool.delete_observations_by_node_tags(tags)
    sync_oms_crud_tool.delete_activities_by_tags(tags)
    sync_oms_crud_tool.delete_nodes_by_tags(tags)
    sync_oms_crud_tool.delete_sources_by_tags(tags)
    sync_oms_crud_tool.delete_providers_by_tags(tags)
    sync_oms_crud_tool.delete_originators_by_tags(tags)


@pytest.fixture
@pytest.mark.asyncio
async def starter_graph(oms_crud_tool, node_input, cleanup_data):
    node = await oms_crud_tool.create_node(node_input)

    originator_input = CreateOriginatorInput(
        name="Test Originator", description="originator desc", tags=SETTINGS.sm_test_tags, acm=DEFAULT_ACM
    )
    originator = await oms_crud_tool.create_originator(originator_input)
    provider_input = CreateProviderInput(
        name="Test Provider",
        description="provider desc",
        tags=SETTINGS.sm_test_tags,
        originatorId=originator.id,
        defaultAcm=DEFAULT_ACM,
        acm=DEFAULT_ACM,
    )
    provider = await oms_crud_tool.create_provider(provider_input)
    source_input = CreateSourceInput(
        name="Test Source",
        description="source desc",
        tags=SETTINGS.sm_test_tags,
        providerId=provider.id,
        acm=DEFAULT_ACM,
        dateOfReport="2004-05-23T00:00:00-04:00",
        dateOfInformation="2004-05-23T00:00:00-04:00",
        identifier="nlp_test_identifier",
        dataAcm=DEFAULT_ACM,
    )
    source = await oms_crud_tool.create_source(source_input)

    yield SimpleTestGraph(node, originator, provider, source)


class SimpleTestGraph:
    def __init__(
        self,
        node: CreateNodeCreateNode,
        originator: CreateOriginatorCreateOriginator,
        provider: CreateProviderCreateProvider,
        source: CreateSourceCreateSource,
    ):
        self.node = node
        self.originator = originator
        self.provider = provider
        self.source = source


@pytest.mark.asyncio
async def test_create_node(cleanup_data, oms_crud_tool, node_input):
    response = await oms_crud_tool.create_node(node_input)

    assert response.id


@pytest.mark.asyncio
async def test_create_observation(oms_crud_tool, starter_graph):
    async for graph in starter_graph:
        obs_input = CreateObservationInput(
            acm=DEFAULT_ACM,
            labels=None,
            classIri="http://www.ontologyrepository.com/CommonCoreOntologies/GeospatialLocation",
            tags=SETTINGS.sm_test_tags,
            geometry={
                "type": "Point",
                "coordinates": [-77.04007, 38.85109],
                "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
            },
            nodeId=graph.node.id,
            sourceId=graph.source.id,
        )

        obs = await oms_crud_tool.create_observation(obs_input)

        assert obs.id


@pytest.mark.asyncio
async def test_create_activity(oms_crud_tool, starter_graph):
    async for graph in starter_graph:
        activity_input = CreateActivityInput(
            name="test activity",
            acm=DEFAULT_ACM,
            sourceId=graph.source.id,
            tags=SETTINGS.sm_test_tags,
            startTime="2004-05-23T00:00:00-04:00",
            endTime="2004-05-23T00:00:00-04:00",
            classIri="https://foundry.ai.mil/ontology/4901-001/MilitaryExercise",
            nodeId=graph.node.id,
            state="UNKNOWN",
        )

        activity = await oms_crud_tool.create_activity(activity_input)

        assert activity.id
