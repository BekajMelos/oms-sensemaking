"""PyTest Configuration."""

from unittest import mock

import pytest
from oms_sdk.generated.generated_graphql_client import (
    CreateSourceCreateSource,
)
from oms_sdk.generated.generated_graphql_client.client import Client

from oms_sensemaking.core.oms_crud import OmsCrudTool


@pytest.fixture
def mock_oms_client():
    return mock.MagicMock(spec=Client)


@pytest.fixture(scope="session")
def mock_source() -> CreateSourceCreateSource:
    oms_crud_tool = OmsCrudTool()
    source = oms_crud_tool.create_test_source()
    yield source


@pytest.fixture
def oms_crud_tool():
    return OmsCrudTool()
