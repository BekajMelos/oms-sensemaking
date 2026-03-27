"""Clients to external services."""

import logging
import re
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.base_client import BaseClient
from oms_sensemaking.clients.health_checker import HealthChecker
from oms_sensemaking.clients.ontology_client import OntologyClient
from oms_sensemaking.core.oms_crud import OmsCrudTool

from ..config import SETTINGS

LOGGER: logging.Logger = logging.getLogger(__name__)

db_engine = create_engine(
    SETTINGS.db_uri,  # type: ignore
    pool_pre_ping=True,
    pool_size=SETTINGS.db_pool_size,
    max_overflow=SETTINGS.db_max_overflow,
    pool_timeout=SETTINGS.db_pool_timeout_seconds,
    connect_args={"sslmode": "require" if SETTINGS.db_ssl else "prefer", "options": "-c timezone=utc"},
)

session_maker = sessionmaker(autocommit=False, autoflush=True, bind=db_engine)

SessionLocal = scoped_session(session_maker)  # noqa: N806


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
        LOGGER.warning("DB connectivity check failed: %s", ex)
        return False


def ping_db_host_wait() -> bool:
    """Resolve and ping DB host:port once on startup using BaseClient."""
    try:
        host = SETTINGS.db_host
        port: int = int(SETTINGS.db_port)
        client = BaseClient(host, port, "Postgres")
        return client.wait_until_ready()
    except Exception as ex:
        LOGGER.warning("DB host readiness check encountered an issue: %s", ex)
        return False


def db_metrics() -> dict:
    """Simple database check for pool stats"""
    try:
        with db_session() as db:
            engine = db.get_bind()
            if not isinstance(engine, Engine):
                return {"error": "DB bind is not an Engine"}
            my_pool = engine.pool
            if isinstance(my_pool, QueuePool):
                current_overflow = my_pool.overflow()
                pool_status = my_pool.status()
            else:
                current_overflow = 0
                pool_status = "Non-QueuePool: overflow not applicable"
        LOGGER.info("DB metrics check successful")
        pool_status_dict = parse_pool_status(pool_status)
        return {"current_overflow": current_overflow, "pool_status": pool_status_dict}
    except Exception as ex:
        LOGGER.warning("DB metrics check failed: %s", ex)
        return {"error": "DB metrics check failed"}


def parse_pool_status(status_str: str) -> dict:
    # This regex finds "Label: Number" (including negative numbers)
    pattern = r"([^:]+):\s*(-?\d+)"
    matches = re.findall(pattern, status_str)

    # Convert matches to a dict and cast values to integers
    return {key.strip(): int(val) for key, val in matches}
