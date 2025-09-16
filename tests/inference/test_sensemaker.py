import pytest

# Assuming your imports
from oms_sensemaking.inference.sensemakers.inference import InferenceSensemaker


@pytest.fixture
def mock_engine(mocker):
    return mocker.patch("oms_sensemaking.inference.sensemakers.inference.Engine")


@pytest.fixture
def mock_rules(mocker):
    mock_in_garrison = mocker.patch("oms_sensemaking.inference.rules.in_out_garrison.InOrOutOfGarrison")
    mock_incursion = mocker.patch("oms_sensemaking.inference.rules.incursions.Incursion")
    mock_extractor = mocker.patch("oms_sensemaking.domain.area_of_interest.aoi_extractor.RealAOIDataExtractor")
    return mock_in_garrison, mock_incursion, mock_extractor


def test_init_adds_rules_based_on_settings(mocker, mock_engine, mock_rules):
    mock_settings = mocker.patch("oms_sensemaking.config.SETTINGS")
    mock_settings.toggle_add_garrison_rule = True
    mock_settings.toggle_incursion_rule = True

    sensemaker = InferenceSensemaker()
    print("Config rules:", sensemaker.config["rules"])
    print("Add_rule calls:", mock_engine.return_value.add_rule.call_args_list)

    assert len(sensemaker.config["rules"]) == 2
    assert mock_engine.return_value.add_rule.call_count == 2
