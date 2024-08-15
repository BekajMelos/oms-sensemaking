"""Clients to external services."""
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from .config import SETTINGS

db_engine = create_engine(
    SETTINGS.db_uri,
    pool_pre_ping=True,
    connect_args={
        'options': '-c timezone=utc'
    }
)

SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=True, bind=db_engine)
)


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
