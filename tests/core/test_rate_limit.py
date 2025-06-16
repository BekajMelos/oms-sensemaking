from unittest import mock
from uuid import uuid4

import pytest
from ratelimit import RateLimitException

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool


@pytest.fixture
def mock_oms_crud_tool():
    oms_crud_tool = OmsCrudTool()
    oms_crud_tool.oms_client = mock.MagicMock()
    return oms_crud_tool


def test_rate_limit_only(mock_oms_crud_tool: OmsCrudTool):
    # Hit the limit
    for _ in range(SETTINGS.maximum_oms_api_calls):
        mock_oms_crud_tool.get_node(uuid4())

    # Next call should raise RateLimitException
    with pytest.raises(RateLimitException):
        mock_oms_crud_tool.get_node(uuid4())
