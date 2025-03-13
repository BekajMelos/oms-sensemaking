"""PyTest Configuration."""
import json
from logging.config import dictConfig
from typing import Dict
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
def ts_acm():
    acm = {
        "classif": "TS",
        "classif_type": "US",
        "owner_prod": [
            "USA"
        ],
        "sci_ctrls": [
            "TK"
        ],
        "dissem_ctrls": [
            "NF"
        ],
        "rsrc_elem": False,
        "ex_from_rollup": False,
        "portion": "TS//TK//NF",
        "banner": "TOP SECRET//TK//NOFORN",
        "dissem_countries": [
            "USA"
        ],
        "f_clearance": [
            "ts"
        ],
        "f_sci_ctrls": [
            "tk"
        ]
    }
    return acm

@pytest.fixture
def mock_oms_client():
    return mock.MagicMock(spec=Client)

@pytest.fixture
def mock_oms_crud_tool():

    def mock_all_but_rehydrate_oms_obj_method(name, *args, **kwargs):
        if name == 'rehydrate_oms_obj':
            return OmsCrudTool().rehydrate_oms_obj(*args, **kwargs)  # Call the real method1
        else:
            return mock.MagicMock()(*args, **kwargs)  # Mock other methods

    return mock.MagicMock(spec=OmsCrudTool, side_effect=mock_all_but_rehydrate_oms_obj_method)


@pytest.fixture
def mil_symbol_rules() -> Dict:
    with open(SETTINGS.mil_symbol_settings.rules_file_path) as fd:
        rules = json.load(fd)
    return rules
