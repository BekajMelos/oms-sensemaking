from unittest.mock import MagicMock

import pytest

# Assuming your imports
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.domain.area_of_interest.base import AOIExtractor
from oms_sensemaking.inference.rules.incursions import IncursionSensemaker


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


@pytest.mark.skip("Depreceated test, this will be removed when Inference SM is fully removed")
def test_init_adds_rules_based_on_settings(mocker, mock_engine, mock_crud_tool, mock_extractor):
    mock_settings = mocker.patch("oms_sensemaking.config.SETTINGS")
    mock_settings.toggle_add_garrison_rule = True
    mock_settings.toggle_incursion_rule = True

    sensemaker = IncursionSensemaker(mock_extractor, mock_crud_tool)
    print("Config rules:", sensemaker.config["rules"])
    print("Add_rule calls:", mock_engine.return_value.add_rule.call_args_list)

    assert len(sensemaker.config["rules"]) == 2
    assert mock_engine.return_value.add_rule.call_count == 2
