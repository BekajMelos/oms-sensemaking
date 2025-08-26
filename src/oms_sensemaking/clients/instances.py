"""Clients to external services."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.health_checker import HealthChecker
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.nlp.corenlp_client import CoreNlpClient

from ..config import SETTINGS
from ..core.db_monitor import attach_db_monitor


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

    # Server-side protections via Postgres options:
    # - timezone=utc (existing)
    # - statement_timeout (ms) to limit long-running queries
    connect_options = f"-c timezone=utc -c statement_timeout={SETTINGS.db_statement_timeout_ms}"
    db_engine = create_engine(
        SETTINGS.db_uri,  # type: ignore
        pool_pre_ping=True,
        connect_args={
            "sslmode": "require" if SETTINGS.db_ssl else "prefer",
            "options": connect_options,
        },
    )

    if SETTINGS.enable_db_query_monitoring:
        attach_db_monitor(
            db_engine,
            slow_query_threshold_ms=SETTINGS.db_slow_query_threshold_ms,
            queries_per_window=SETTINGS.db_queries_per_window,
            query_window_seconds=SETTINGS.db_query_window_seconds,
            log_sql_parameters=SETTINGS.db_monitor_log_sql_parameters,
            enforce_frequency_limit=SETTINGS.db_enforce_query_frequency_limit,
            throttle_sleep_seconds=SETTINGS.db_query_throttle_sleep_seconds,
            raise_on_exceed=SETTINGS.db_raise_on_frequency_exceed,
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
