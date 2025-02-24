"""PyTest Configuration."""

from collections.abc import Generator
from logging.config import dictConfig
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from oms_sdk.generated.generated_graphql_client import (
    CreateSourceCreateSource,
)
from oms_sdk.generated.generated_graphql_client.client import Client
from sqlalchemy.orm.session import Session

from oms_sensemaking.config import PROJECT_PATH, SETTINGS, LogConfig
from oms_sensemaking.core.oms_crud import OmsCrudTool

load_dotenv()
dictConfig(LogConfig().model_dump())  # initialize logging

# reconfigure database for testing before importing app
if not SETTINGS.db_uri.endswith("_test"):
    SETTINGS.db_uri = f"{SETTINGS.db_uri}_test"

# the session generator should initialized after the config hack above
from oms_sensemaking.clients.instances import SessionLocal

# alembic configuration
alembic_cfg: Config = Config(str(Path.joinpath(PROJECT_PATH, "alembic.ini")))
alembic_cfg.set_main_option("script_location", str(Path.joinpath(PROJECT_PATH, "migrations")))
alembic_cfg.set_main_option("sqlalchemy.url", SETTINGS.db_uri)

# NLP Configuration
if SETTINGS.corenlp_host != SETTINGS.corenlp_localhost:
    SETTINGS.corenlp_host = SETTINGS.corenlp_localhost

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
def db() -> Generator[Session, Any, None]:
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

    db: Session = SessionLocal()

    try:
        yield db
    finally:
        db.close()

    # purge database tables
    command.downgrade(alembic_cfg, "base")


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
