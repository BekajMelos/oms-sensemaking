"""Clients to external services."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.base_client import BaseClient
from oms_sensemaking.clients.health_checker import HealthChecker
from oms_sensemaking.clients.ontology_client import OntologyClient
from oms_sensemaking.core.oms_crud import OmsCrudTool

from ..config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)


@contextmanager
def db_session() -> Iterator[Session]:
    """
    Database session contextmanager.

    This function yields a database session and automatically closes the
    session when processing is complete. This can be used with Python's with
    command. For example:

        with db_session() as db:
            db.add(some_orm_model)
            db.commit()
    """

    db_engine = create_engine(
        SETTINGS.db_uri,  # type: ignore
        pool_pre_ping=True,
        pool_size=SETTINGS.db_pool_size,
        max_overflow=SETTINGS.db_max_overflow,
        pool_timeout=SETTINGS.db_pool_timeout_seconds,
        connect_args={"sslmode": "require" if SETTINGS.db_ssl else "prefer", "options": "-c timezone=utc"},
    )

    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=db_engine))  # noqa: N806

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


aac_client = AacClient(SETTINGS.cert_path, SETTINGS.key_path, SETTINGS.aac_cacert_path, SETTINGS.aac_verification_mode)

oms_crud_tool = OmsCrudTool()

health_checker = HealthChecker()

ontology_service = OntologyClient(oms_crud_tool)


def ping_db() -> bool:
    """Simple database connectivity check via SELECT 1."""
    try:
        with db_session() as db:
            statement_timeout_ms = int(max(SETTINGS.ping_timeout_seconds, 0.1) * 1000)
            db.execute(text(f"SET statement_timeout = {statement_timeout_ms}"))
            db.execute(text("SELECT 1"))
        LOGGER.info("DB connectivity check successful")
        return True
    except Exception as ex:
        LOGGER.warning(f"DB connectivity check failed: {ex}")
        return False


def ping_db_host_wait() -> bool:
    """Resolve and ping DB host:port once on startup using BaseClient."""
    try:
        host = SETTINGS.db_host
        port: int = int(SETTINGS.db_port)
        client = BaseClient(host, port, "Postgres")
        return client.wait_until_ready()
    except Exception as ex:
        LOGGER.warning(f"DB host readiness check encountered an issue: {ex}")
        return False
