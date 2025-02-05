"""Clients to external services."""

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.health_checker import HealthChecker
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.nlp.corenlp_client import CoreNlpClient

from ..config import SETTINGS

db_engine = create_engine(
    SETTINGS.db_uri,  # type: ignore
    pool_pre_ping=True,
    connect_args={"sslmode": "require" if SETTINGS.db_ssl else "prefer", "options": "-c timezone=utc"},
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=db_engine))


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


def get_db_session() -> Iterator[Session]:
    """
    Get a database session generator.

    This function yields a database session and automatically closes the
    session when processing is complete. This can be used as a dependency
    injected database session in FastAPI.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


aac_client = AacClient(SETTINGS.cert_path, SETTINGS.key_path)
oms_client = OmsCrudTool()
oms_crud_tool = OmsCrudTool()

corenlp_client = CoreNlpClient(props=SETTINGS.corenlp_client_props, hostname=SETTINGS.corenlp_host)

health_checker = HealthChecker()
