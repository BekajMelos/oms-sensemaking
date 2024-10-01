"""PyTest Configuration."""

from logging.config import dictConfig
from pathlib import Path
from typing import Iterator

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from nlp.mock_corenlp_client import MockCoreNlpClient
from nlp.mock_responses import mock_response_short_text
from sqlalchemy.orm.session import Session

from oms_sensemaking.config import PROJECT_PATH, SETTINGS, LogConfig

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

if not isinstance(SETTINGS.corenlp_client, MockCoreNlpClient):
    SETTINGS.corenlp_client = MockCoreNlpClient(props={}, hostname=SETTINGS.corenlp_host)
    SETTINGS.corenlp_client.set_response(mock_response_short_text)


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
