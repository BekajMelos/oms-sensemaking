"""PyTest Configuration."""

from logging.config import dictConfig
from pathlib import Path
from typing import Iterator
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
from sqlalchemy.orm.session import Session

from oms_sensemaking.config import PROJECT_PATH, SETTINGS, LogConfig
from oms_sensemaking.core.oms_crud import OmsCrudTool

load_dotenv()
dictConfig(LogConfig().model_dump())  # initialize logging

# reconfigure database for testing before importing app
if not SETTINGS.db_uri.endswith("_test"):
    SETTINGS.db_uri = f"{SETTINGS.db_uri}_test"

# the session generator should initialized after the config hack above
from oms_sensemaking.clients import SessionLocal

# alembic configuration
alembic_cfg: Config = Config(str(Path.joinpath(PROJECT_PATH, "alembic.ini")))
alembic_cfg.set_main_option("script_location", str(Path.joinpath(PROJECT_PATH, "migrations")))
alembic_cfg.set_main_option("sqlalchemy.url", SETTINGS.db_uri)

# NLP Configuration
if SETTINGS.corenlp_host != SETTINGS.corenlp_localhost:
    SETTINGS.corenlp_host = SETTINGS.corenlp_localhost

# Update aac url to hit our test instance
SETTINGS.aac_url = "http://localhost:5022"

# Source and provider creation for tests
if not SETTINGS.create_source_if_none:
    SETTINGS.create_source_if_none = True
if not SETTINGS.create_provider_if_none:
    SETTINGS.create_provider_if_none = True


@pytest.fixture
def db() -> Iterator[Session]:
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
def mock_source() -> CreateSourceCreateSource:
    test_originator_name = "nlp_test_originator"
    test_provider_name = "nlp_test_provider"
    test_source_name = "nlp_test_source"

    oms_crud_tool = OmsCrudTool()

    # Create test originator if it doesn't already exist
    originator = oms_crud_tool.get_originator_by_name(test_originator_name).data[0]
    if not originator:
        originator = oms_crud_tool.create_originator(
            CreateOriginatorInput(
                name=test_originator_name,
                description="A test originator",
                acm=DEFAULT_ACM,
                tags=["test_nlp_originator"],
            )
        )

    # Create test provider if it doesn't already exist
    provider = oms_crud_tool.get_provider_by_name(test_provider_name).data[0]
    if not provider:
        provider = oms_crud_tool.create_provider(
            CreateProviderInput(
                name=test_provider_name, description="A test provider", originatorId=originator.id, acm=DEFAULT_ACM
            )
        )

    # Create test source if it doesn't already exist
    source = oms_crud_tool.get_source_by_name(test_source_name).data[0]
    if not source:
        source = oms_crud_tool.create_source(
            CreateSourceInput(
                name="nlp_test_source",
                dateOfReport="2004-05-23T00:00:00-04:00",
                dateOfInformation="2004-05-23T00:00:00-04:00",
                providerId=provider.id,
                acm=DEFAULT_ACM,
                identifier="nlp_test_identifier",
                dataAcm=DEFAULT_ACM,
            )
        )

    yield source
