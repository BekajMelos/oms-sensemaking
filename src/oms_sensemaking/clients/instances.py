"""Clients to external services."""

import logging
import socket
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.health_checker import HealthChecker
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.nlp.corenlp_client import CoreNlpClient

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

    # Log resolved Postgres IP address
    try:
        db_url = make_url(SETTINGS.db_uri)  # type: ignore[arg-type]
        if db_url.host:
            resolved_db_host = socket.gethostbyname(db_url.host)
            LOGGER.info(f"Resolved Postgres host '{db_url.host}' to IP {resolved_db_host}:{db_url.port or '5432'}")
    except Exception as ex:
        LOGGER.warning(f"Unable to resolve Postgres host from DB URI: {ex}")

    db_engine = create_engine(
        SETTINGS.db_uri,  # type: ignore
        pool_pre_ping=True,
        connect_args={"sslmode": "require" if SETTINGS.db_ssl else "prefer", "options": "-c timezone=utc"},
    )

    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=db_engine))  # noqa: N806

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


aac_client = AacClient(SETTINGS.cert_path, SETTINGS.key_path, SETTINGS.cacert_path, SETTINGS.aac_verification_mode)

oms_crud_tool = OmsCrudTool()

corenlp_client = CoreNlpClient(props=SETTINGS.corenlp_client_props, hostname=SETTINGS.corenlp_host)

health_checker = HealthChecker()


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
