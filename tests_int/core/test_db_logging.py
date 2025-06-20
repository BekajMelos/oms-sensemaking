"""Test DB Logging"""
import json
import logging
import logging.config
import time
import uuid
from datetime import datetime, timezone
from unittest import mock

import pytest

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from sqlalchemy import delete, desc, select
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from oms_sensemaking.config import LogConfig, SETTINGS
from oms_sensemaking.clients.instances import OmsCrudTool
from oms_sensemaking.core.logging import handlers
from oms_sensemaking.core.events import AuditLogEvent, DummyAuditLogEventConsumer
from oms_sensemaking.core.controllers import SensemakerController, LOGGER
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.models.logs import LogLevel, LogRecord
from oms_sensemaking.mil_symbol.controllers import MilSymbolSensemakerController
from oms_sensemaking.mil_symbol.sensemaker import MilSymbolSensemaker

from oms_sdk.generated.generated_graphql_client import GraphQLClientError, NodeNode



# class DummySensemaker(Sensemaker):
#     """
#     A dummy sensemaker

#     Algorithm ChangeLog
#     ===================

#     [1.0.0]

#     - Initial "dummy" implementation.

#     """

#     def __init__(self, settings: dict, oms_crud_tool: OmsCrudTool) -> None:
#         """Create a new instance of MilSymbolSensemaker."""
#         super().__init__()
#         self.version = (1, 0, 0)
#         self.name = self.__class__.__name__
#         self.config = {}
#         self.settings = settings
#         self.oms_crud_tool = oms_crud_tool

#     def process_data(self, oms_object: any, config: dict | None = None) -> list:
#         """Calls dumb_method"""
#         self.dumb_method()
#         return []

#     def dumb_method(self) -> None:
#         """Doesn't do anything"""
#         return None


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

    print("db bind url: ", db.bind.url)
    print("test_db bind url: ", test_db.bind.url)

    # TEST_LOGGER = logging.getLogger("oms_sensemaking.core.controllers")
    # TEST_LOGGER = logging.getLogger(__name__)
    # TEST_LOGGER.setLevel("DEBUG")
    logging.config.dictConfig(LogConfig().model_dump())

    # config_format = LogConfig().formatters["custom"]
    # formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # formatter = logging.Formatter(fmt=config_format["format"], datefmt=config_format["datefmt"], style=config_format["style"])

    # handler = DatabaseHandler()
    # handler.setFormatter(formatter)
    # print("TEST_LOGGER.level: ", TEST_LOGGER.level)
    # handler.setLevel(TEST_LOGGER.level)

    # TEST_LOGGER.addHandler(handler)

    # print("TEST_LOGGER id: ", hex(id(TEST_LOGGER)))
    # print("root logger id: ", hex(id(TEST_LOGGER.root)))
    # print(TEST_LOGGER.handlers)

    # print("this isn't printing")
    # TEST_LOGGER.info("in the test: does this print")
    # print(f"TEST_LOGGER is LOGGER: {TEST_LOGGER is LOGGER}")

    # overwrite the log handler db
    handlers.db_session = test_db


    start_time = datetime.now(tz=timezone.utc)

    # check that cotravels exist in Findings table
    logs = test_db.execute(delete(LogRecord))


    # create a geocontroller (or dummy controller) and cause the problem
    # it should go into the oms_sensemaking_test db

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
            test_db.execute(select(LogRecord).filter(LogRecord.level == LogLevel.ERROR).order_by(desc(LogRecord.created_at)))
            .scalars()
            .all()
        )
        if logs and logs[0].created_at > start_time:
            break
        time.sleep(1)

    assert len(logs) == 1
    log = logs[0]
    assert log.message
    print(":log.message: ", log.message)
    print("exc_text: :", log.exc_text)
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

    # dummy_sensemaker = DummySensemaker({}, mock_oms_crud_tool)
    # # dummy_consumer = DummyAuditLogEventConsumer()
    # # controller = SensemakerController(dummy_consumer)
    # dummy_sensemaker.dumb_method = mock.MagicMock(side_effect=TypeError)

    # try:
    #     dummy_sensemaker.process_data(NodeNode.model_construct())
    # except TypeError:
    #     # don't fail bc of the type error. Just check that it was logged
    #     pass

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
            test_db.execute(select(LogRecord).filter(LogRecord.level == LogLevel.ERROR).order_by(desc(LogRecord.created_at)))
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
