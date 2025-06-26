"""Test DB Logging"""
import logging
import logging.config
import time
import uuid
from datetime import datetime, timezone
from unittest import mock

import pytest
from oms_sdk.generated.generated_graphql_client import GraphQLClientError, NodeNode
from sqlalchemy import create_engine, delete, desc, select
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from oms_sensemaking.config import SETTINGS, LogConfig
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import AuditLogEvent, DummyAuditLogEventConsumer
from oms_sensemaking.core.logging import handlers
from oms_sensemaking.mil_symbol.controllers import MilSymbolSensemakerController
from oms_sensemaking.mil_symbol.sensemaker import MilSymbolSensemaker
from oms_sensemaking.models.logs import LogLevel, LogRecord


@pytest.fixture
def test_db():

    db_engine = create_engine(
        "postgresql+psycopg://appuser:password@localhost:5432/oms_sensemaking_test",  # type: ignore
        pool_pre_ping=True,
        connect_args={"sslmode": "require" if SETTINGS.db_ssl else "prefer", "options": "-c timezone=utc"},
    )

    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=db_engine))

    sess = SessionLocal

    print("count logrecord: ", len(sess.execute(select(LogRecord)).scalars().all()))

    yield sess

    sess.close()


def test_db_logging(db: Session, test_db: Session):
    """Test that errors are logged to DB"""

    logging.config.dictConfig(LogConfig().model_dump())

    # overwrite the log handler db
    handlers.db_session = test_db

    start_time = datetime.now(tz=timezone.utc)

    # check that cotravels exist in Findings table
    logs = test_db.execute(delete(LogRecord))

    dummy_consumer = DummyAuditLogEventConsumer()
    controller = SensemakerController(dummy_consumer)
    controller.oms_crud_tool.rehydrate_oms_obj = mock.MagicMock(side_effect=GraphQLClientError)

    node_id = str(uuid.uuid4())
    event = AuditLogEvent(
        objectId=node_id,
        userId="user",
        objectType="NODE",
        action="CREATE"
    )

    controller.handle_event(event)

    for _ in range(3):
        # check that cotravels exist in Findings table
        logs = (
            test_db.execute(
                select(LogRecord).filter(LogRecord.level == LogLevel.ERROR).order_by(desc(LogRecord.created_at))
                )
            .scalars()
            .all()
        )
        if logs and logs[0].created_at > start_time:
            break
        time.sleep(1)

    assert len(logs) == 1
    log = logs[0]
    assert log.message
    assert node_id in log.message
    assert "GraphQLClientError" in log.exc_text
    assert log.module_name == "oms_sensemaking.core.controllers"


def test_db_logging_within_sensemaker(db: Session, test_db: Session, mock_oms_crud_tool):
    """Test that errors are logged to DB"""

    logging.config.dictConfig(LogConfig().model_dump())

    # overwrite the log handler db
    handlers.db_session = test_db

    start_time = datetime.now(tz=timezone.utc)

    # check that cotravels exist in Findings table
    logs = test_db.execute(delete(LogRecord))

    controller = MilSymbolSensemakerController(DummyAuditLogEventConsumer())
    mil_sensemaker = MilSymbolSensemaker({}, mock_oms_crud_tool)
    controller._registry["mil_symbol"] = mil_sensemaker

    node_id = str(uuid.uuid4())
    event = AuditLogEvent(
        objectId=node_id,
        userId="user",
        objectType="NODE",
        action="CREATE"
    )
    controller.oms_crud_tool.rehydrate_oms_obj = mock.MagicMock(return_value=NodeNode.model_construct(id=node_id))
    mil_sensemaker.is_attribute_to_ignore = mock.MagicMock(side_effect=TypeError("sensemaker failed"))

    controller.handle_event(event)

    for _ in range(3):
        # check that cotravels exist in Findings table
        logs = (
            test_db.execute(
                select(LogRecord).filter(LogRecord.level == LogLevel.ERROR).order_by(desc(LogRecord.created_at))
                )
            .scalars()
            .all()
        )
        if logs and logs[0].created_at > start_time:
            break
        time.sleep(1)

    assert len(logs) == 1
    log = logs[0]
    assert log.message
    assert "sensemaker failed" in log.message
    assert log.module_name == "oms_sensemaking.core.controllers"
