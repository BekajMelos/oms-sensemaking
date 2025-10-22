import pytest
from oms_sdk.generated.generated_async_graphql_client import (
    Client,
    CreateActivityInput,
    CreateNodeInput,
    CreateObservationInput,
    CreateOriginatorInput,
    CreateProviderInput,
    CreateSourceInput,
)
from pytest_mock import MockerFixture

from oms_sensemaking.core.async_atoms_crud import AsyncAtomsCrudTool


class AsyncAtomsCrudToolHelper(AsyncAtomsCrudTool):
    def __init__(self, mock: MockerFixture):
        self.mock_client = mock.Mock(spec=Client)
        self._atoms_client: Client = self.mock_client


@pytest.fixture
def make_client(mocker: MockerFixture):
    return AsyncAtomsCrudToolHelper(mocker)


@pytest.mark.asyncio
async def test_create_node(mocker: MockerFixture, make_client: AsyncAtomsCrudToolHelper):
    client = make_client
    await client.create_node(mocker.Mock(spec=CreateNodeInput))


@pytest.mark.asyncio
async def test_create_observation(mocker: MockerFixture, make_client: AsyncAtomsCrudToolHelper):
    client = make_client
    await client.create_observation(mocker.Mock(spec=CreateObservationInput))


@pytest.mark.asyncio
async def test_create_activity(mocker: MockerFixture, make_client: AsyncAtomsCrudToolHelper):
    client = make_client
    await client.create_activity(mocker.Mock(spec=CreateActivityInput))


@pytest.mark.asyncio
async def test_create_originator(mocker: MockerFixture, make_client: AsyncAtomsCrudToolHelper):
    client = make_client
    await client.create_originator(mocker.Mock(spec=CreateOriginatorInput))


@pytest.mark.asyncio
async def test_create_provider(mocker: MockerFixture, make_client: AsyncAtomsCrudToolHelper):
    client = make_client
    await client.create_provider(mocker.Mock(spec=CreateProviderInput))


@pytest.mark.asyncio
async def test_create_source(mocker: MockerFixture, make_client: AsyncAtomsCrudToolHelper):
    client = make_client
    await client.create_source(mocker.Mock(spec=CreateSourceInput))
