"""Test DB Logging"""
import uuid
from unittest import mock

from oms_sdk.generated.generated_graphql_client import GraphQLClientError, NodeNode
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import AuditLogEvent, DummyAuditLogEventConsumer
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.models.logs import AuditLogError


class DummySensemaker(Sensemaker):
    """Dummy Sensemaker"""

    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of MilSymbolSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = {}
        self.oms_crud_tool = oms_crud_tool

    def process_data(self, data: any, config: any) -> any:
        return []


def test_db_logging(db: Session, session_local: Session):
    """Test that errors are logged to DB"""

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

    # check that AuditLogErrors were created
    logs = (
        db.execute(select(AuditLogError).order_by(desc(AuditLogError.created_at)))
        .scalars()
        .all()
    )

    assert len(logs) == 1, "Error should be found when failing to rehydrate node"
    log = logs[0]
    assert log.message
    assert node_id in log.message
    assert "GraphQLClientError" in log.exc_text
    assert log.module_name == "oms_sensemaking.core.controllers"
    assert log.acm == SETTINGS.highest_classification


def test_db_logging_within_sensemaker(db: Session, session_local, mock_oms_crud_tool, ts_acm):
    """Test that errors are logged to DB"""

    controller = SensemakerController(DummyAuditLogEventConsumer())
    sensemaker = DummySensemaker(mock_oms_crud_tool)
    controller.register("dummy", sensemaker)

    node_id = str(uuid.uuid4())
    event = AuditLogEvent(
        objectId=node_id,
        userId="user",
        objectType="NODE",
        action="CREATE"
    )
    mock_node = NodeNode.model_construct(id=node_id, acm=ts_acm)
    controller.oms_crud_tool.rehydrate_oms_obj = mock.MagicMock(return_value=mock_node)
    sensemaker.process_data = mock.MagicMock(side_effect=TypeError("sensemaker failed"))

    controller.handle_event(event)

    # check that AuditLogErrors were created
    logs = (
        db.execute(select(AuditLogError).order_by(desc(AuditLogError.created_at)))
        .scalars()
        .all()
    )

    assert len(logs) == 1, "Error should be found when TypeError occurs during process_data"
    log = logs[0]
    assert log.message
    assert node_id in log.message
    assert "sensemaker failed" in log.exc_text
    assert log.module_name == "oms_sensemaking.core.controllers"
    assert log.acm == ts_acm
