"""PyTest Configuration."""

import json
import os
from collections.abc import Generator
from logging.config import dictConfig
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    CreateOriginatorInput,
    CreateProviderInput,
    CreateSourceCreateSource,
    CreateSourceInput,
)
from oms_sdk.generated.generated_graphql_client.client import Client
from sqlalchemy.orm import Session

from oms_sensemaking.config import PROJECT_PATH, SETTINGS, LogConfig
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.schemas import GeospatialSensemakerConfig
from oms_sensemaking.models.base import BaseORM

load_dotenv()
dictConfig(LogConfig().model_dump())  # initialize logging

# reconfigure database for testing before importing app
if not SETTINGS.db_uri.endswith("_test"):
    SETTINGS.db_uri = f"{SETTINGS.db_uri}_test"

# alembic configuration
alembic_cfg: Config = Config(str(Path.joinpath(PROJECT_PATH, "alembic.ini")))
alembic_cfg.set_main_option("script_location", str(Path.joinpath(PROJECT_PATH, "migrations")))
escaped_uri = SETTINGS.db_uri.replace("%", "%%")
alembic_cfg.set_main_option("sqlalchemy.url", escaped_uri)

# Update aac url to hit our test instance
SETTINGS.aac_url = "http://localhost:5022"

# Because of atoms dev on port 8010 vs 8020 set omsb_url appropriately
omsb_url = os.getenv("OMSB_URL", SETTINGS.omsb_url)
omsb_url = "https://localhost:8020/graphql" if "https" in omsb_url else "http://localhost:8010/graphql"

# Update OMSB URL
SETTINGS.omsb_url = omsb_url

# Source and provider creation for tests
if not SETTINGS.create_source_if_none:
    SETTINGS.create_source_if_none = True
if not SETTINGS.create_provider_if_none:
    SETTINGS.create_provider_if_none = True


@pytest.fixture(scope="session")
def session_local():
    """
    Get a database session generator.

    This function:
      - Upgrades the database schema definition to HEAD using Alembic
      - Yields a database session generator
      - Downgrades the database schema definition to BASE using Alembic

    It is intended on being used as a pytest fixture.
    """
    # clear old connections in centralized engine
    from oms_sensemaking.clients import instances

    # run database migrations on test DB
    command.upgrade(alembic_cfg, "head")

    # reuse centralized SessionLocal
    yield instances.session_maker


@pytest.fixture(scope="function")
def db(session_local) -> Generator[Session, Any, None]:
    db: Session = session_local()
    orm = BaseORM()

    try:
        yield db
    finally:
        db.rollback()
        for table in reversed(orm.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()


@pytest.fixture
def mock_oms_client():
    return mock.MagicMock(spec=Client)


@pytest.fixture
def mock_source():
    """Mock source fixture for tests that need a source object."""
    mock_source_obj = mock.MagicMock(spec=CreateSourceCreateSource)
    mock_source_obj.id = "mock-source-id"
    return mock_source_obj


@pytest.fixture(scope="function")
def test_originator() -> Generator[Any, Any, None]:
    """Create a real Originator in ATOMS for integration tests."""
    oms_crud_tool = OmsCrudTool()
    originator_name = "int_test_originator"

    originator = oms_crud_tool.create_originator(
        CreateOriginatorInput(name=originator_name, description="Integration Test", acm=DEFAULT_ACM, tags=[])
    )

    yield originator

    oms_crud_tool.delete_originator(originator_id=originator.id)


@pytest.fixture(scope="function")
def test_provider(test_originator) -> Generator[Any, Any, None]:
    """Create a real Provider in ATOMS for integration tests."""
    oms_crud_tool = OmsCrudTool()
    provider_name = "int_test_provider"

    provider = oms_crud_tool.create_provider(
        CreateProviderInput(
            name=provider_name,
            description="Integration Test",
            originatorId=test_originator.id,
            acm=DEFAULT_ACM,
            tags=[],
        )
    )

    yield provider
    oms_crud_tool.delete_provider(provider_id=provider.id)


@pytest.fixture(scope="function")
def create_source(test_provider) -> Generator[CreateSourceCreateSource, Any, None]:
    """Create a real Source in ATOMS for integration tests."""
    oms_crud_tool = OmsCrudTool()
    source_name = "int_test_source"

    source = oms_crud_tool.create_source(
        CreateSourceInput(
            name=source_name,
            description="Integration Test",
            providerId=test_provider.id,
            acm=DEFAULT_ACM,
            identifier="int_test_identifier",
            dateOfReport="2004-05-23T00:00:00-04:00",
            dateOfInformation="2004-05-23T00:00:00-04:00",
            dataAcm=DEFAULT_ACM,
            tags=[],
        )
    )

    yield source
    oms_crud_tool.delete_source(source_id=source.id)


@pytest.fixture
def mock_oms_crud_tool(mock_oms_client, mock_source):
    def get_source_side_effect(source_id):
        if source_id == mock_source.id:
            return mock_source
        return mock.MagicMock(spec=CreateSourceCreateSource)

    oms_crud_tool = OmsCrudTool()
    oms_crud_tool.get_source = mock.MagicMock(side_effect=get_source_side_effect)
    oms_crud_tool.oms_client = mock_oms_client

    return oms_crud_tool


@pytest.fixture
def mil_symbol_rules() -> dict:
    with open(SETTINGS.mil_symbol_settings.rules_file_path) as fd:
        rules = json.load(fd)
    return rules


@pytest.fixture
def aircraft_geo_config() -> dict:
    with open(SETTINGS.geo_sensemaker_config_file_path) as fd:
        config = json.load(fd)

    geo_config = GeospatialSensemakerConfig(
        **config.get("http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft", {})
    )

    return geo_config.model_dump()


@pytest.fixture
def ts_acm() -> dict:
    return {
        "classif": "TS",
        "classif_type": "US",
        "sci_ctrls": ["TK"],
        "dissem_ctrls": ["NF"],
        "portion": "TS//TK//NF",
        "banner": "TOP SECRET//TK//NOFORN",
        "dissem_countries": ["USA"],
        "f_clearance": ["ts"],
        "f_sci_ctrls": ["tk"],
    }


def rollup_unclass_acm_3_0() -> dict:
    return {
        "version": "3.0",
        "classif_type": "US",
        "classif": "U",
        "owner_prod": ["USA"],
        "non_us_ctrls": [],
        "sci_ctrls": [],
        "disponly_to": [""],
        "dissem_ctrls": [],
        "non_ic": [],
        "rel_to": [],
        "fgi_open": [],
        "fgi_protect": [],
        "portion": "U",
        "banner": "UNCLASSIFIED",
        "dissem_countries": [],
        "accms": [],
        "macs": [],
        "oc_attribs": [{"orgs": [], "missions": [], "regions": []}],
        "share": {"users": [], "projects": {}},
        "f_clearance": ["u"],
        "f_sci_ctrls": [],
        "f_accms": [],
        "f_oc_org": [],
        "f_regions": [],
        "f_missions": [],
        "f_share": [],
        "f_macs": [],
    }
