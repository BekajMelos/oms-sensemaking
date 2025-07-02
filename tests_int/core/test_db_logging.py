"""Test DB Logging"""
import logging
import logging.config
import uuid
from unittest import mock

from oms_sdk.generated.generated_graphql_client import GraphQLClientError, NodeNode
from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from oms_sensemaking.config import LogConfig
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import AuditLogEvent, DummyAuditLogEventConsumer
from oms_sensemaking.core.logging import handlers
from oms_sensemaking.mil_symbol.controllers import MilSymbolSensemakerController
from oms_sensemaking.mil_symbol.sensemaker import MilSymbolSensemaker
from oms_sensemaking.models.logs import LogLevel, LogRecord


def test_db_logging(db: Session, session_local: Session):
    """Test that errors are logged to DB"""

    logging.config.dictConfig(LogConfig().model_dump())

    # overwrite the log handler db
    handlers.db_session = session_local

    # check that logs exist in LogRecord table
    logs = db.execute(delete(LogRecord))

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

    # check that cotravels exist in Findings table
    logs = (
        db.execute(
            select(LogRecord).filter(LogRecord.level == LogLevel.ERROR).order_by(desc(LogRecord.created_at))
            )
        .scalars()
        .all()
    )

    assert len(logs) == 1
    log = logs[0]
    assert log.message
    assert node_id in log.message
    assert "GraphQLClientError" in log.exc_text
    assert log.module_name == "oms_sensemaking.core.controllers"


def test_db_logging_within_sensemaker(db: Session, session_local, mock_oms_crud_tool):
    """Test that errors are logged to DB"""

    logging.config.dictConfig(LogConfig().model_dump())

    # overwrite the log handler db
    handlers.db_session = session_local

    # check that cotravels exist in Findings table
    logs = db.execute(delete(LogRecord))

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

    # check that logs exist in LogRecord table
    logs = (
        db.execute(
            select(LogRecord).filter(LogRecord.level == LogLevel.ERROR).order_by(desc(LogRecord.created_at))
            )
        .scalars()
        .all()
    )

    assert len(logs) == 1
    log = logs[0]
    assert log.message
    assert "sensemaker failed" in log.message
    assert log.module_name == "oms_sensemaking.core.controllers"
