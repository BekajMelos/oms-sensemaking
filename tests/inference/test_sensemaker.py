from unittest.mock import MagicMock

import pytest

# Assuming your imports
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.domain.area_of_interest.base import AOIExtractor


@pytest.fixture
def mock_engine(mocker):
    return mocker.patch("oms_sensemaking.inference.sensemakers.inference.Engine")


@pytest.fixture
def mock_rules(mocker):
    mock_in_garrison = mocker.patch("oms_sensemaking.inference.rules.in_out_garrison.InOrOutOfGarrison")
    mock_incursion = mocker.patch("oms_sensemaking.inference.rules.incursions.Incursion")
    mock_extractor = mocker.patch("oms_sensemaking.domain.area_of_interest.aoi_extractor.RealAOIDataExtractor")
    return mock_in_garrison, mock_incursion, mock_extractor


@pytest.fixture
def mock_crud_tool(mock_oms_client):
    crud_tool = MagicMock(spec=OmsCrudTool)
    crud_tool.oms_client = mock_oms_client
    return crud_tool


@pytest.fixture
def mock_extractor():
    extractor = MagicMock(spec=AOIExtractor)
    return extractor
