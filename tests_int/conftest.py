"""PyTest Configuration."""

import json
from collections.abc import Generator
from logging.config import dictConfig
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from oms_sdk.generated.generated_graphql_client import CreateSourceCreateSource
from oms_sdk.generated.generated_graphql_client.client import Client
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from oms_sensemaking.config import PROJECT_PATH, SETTINGS, LogConfig
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.schemas import GeospatialSensemakerConfig

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

# Update OMSB URL
SETTINGS.omsb_url = "https://localhost:8020/graphql"

# Source and provider creation for tests
if not SETTINGS.create_source_if_none:
    SETTINGS.create_source_if_none = True
if not SETTINGS.create_provider_if_none:
    SETTINGS.create_provider_if_none = True

SETTINGS.nlp_tags = ["SMOKE_TEST_TAG", "SENSEMAKING_NLP"]


@pytest.fixture(scope="function")
def session_local():
    """
    Get a database session generator.

    This function:
      - Upgrades the database schema definition to HEAD using Alembic
      - Yields a database session generator
      - Downgrades the database schema definition to BASE using Alembic

    It is intended on being used as a pytest fixture.
    """

    # run database migrations
    command.upgrade(alembic_cfg, "head")

    # TODO reuse from instances.py?
    db_engine = create_engine(
        SETTINGS.db_uri,  # type: ignore
        pool_pre_ping=True,
        connect_args={"sslmode": "require" if SETTINGS.db_ssl else "prefer", "options": "-c timezone=utc"},
    )

    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=db_engine))  # noqa: N806

    yield SessionLocal

    # purge database tables
    command.downgrade(alembic_cfg, "base")


@pytest.fixture(scope="function")
def db(session_local) -> Generator[Session, Any, None]:
    db: Session = session_local()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def mock_oms_client():
    return mock.MagicMock(spec=Client)


@pytest.fixture(scope="session")
def mock_source() -> Generator[CreateSourceCreateSource, Any, None]:
    oms_crud_tool = OmsCrudTool()
    source = oms_crud_tool.create_test_source()
    yield source


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
