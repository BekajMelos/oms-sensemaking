"""PyTest Configuration."""

from logging.config import dictConfig
from unittest import mock

import pytest
from dotenv import load_dotenv
from oms_sdk.generated.generated_graphql_client.client import Client

from oms_sensemaking.config import SETTINGS, LogConfig
from oms_sensemaking.core.oms_crud import OmsCrudTool

load_dotenv()
dictConfig(LogConfig().model_dump())  # initialize logging

SETTINGS.nlp_tags = ["SMOKE_TEST_TAG", "SENSEMAKING_NLP"]

@pytest.fixture
def mock_oms_client():
    return mock.MagicMock(spec=Client)

@pytest.fixture
def mock_oms_crud_tool():
    return mock.MagicMock(spec=OmsCrudTool)

