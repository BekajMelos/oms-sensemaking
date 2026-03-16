"""Test DB Logging"""

import uuid
from unittest import mock

import pytest
from oms_sdk.generated.generated_graphql_client import GraphQLClientError, NodeNode
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from oms_sensemaking import __version__
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.error_loggers import ErrorLogger, RethrowErrorLogger
from oms_sensemaking.core.events import AuditLogEvent, DummyAuditLogEventConsumer
from oms_sensemaking.core.exceptions import SensemakingError
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


@pytest.fixture
def mock_controller() -> SensemakerController:
    return SensemakerController(DummyAuditLogEventConsumer(), RethrowErrorLogger(ErrorLogger()))


def test_db_logging(mock_controller: SensemakerController, db: Session, session_local: Session):
    """Test that errors are logged to DB"""

    mock_controller.oms_crud_tool.rehydrate_oms_obj = mock.MagicMock(side_effect=GraphQLClientError)

    node_id = str(uuid.uuid4())
    event = AuditLogEvent(objectId=node_id, userId="user", objectType="NODE", action="CREATE")

    with pytest.raises(GraphQLClientError):
        mock_controller.handle_event(event)

    # check that AuditLogErrors were created
    logs = db.execute(select(AuditLogError).order_by(desc(AuditLogError.created_at))).scalars().all()

    assert len(logs) == 1, "Error should be found when failing to rehydrate node"
    log = logs[0]
    assert log.object_id == uuid.UUID(node_id)
    assert log.object_type == "NODE"
    assert log.event_type == "CREATE"
    assert log.function_name == "get_oms_data"
    assert isinstance(log.line_no, int)
    assert "self.oms_crud_tool.rehydrate_oms_obj" in log.code
    assert log.exception_name == "GraphQLClientError"
    assert log.message is None
    assert log.exc_text is None
    assert log.module_name.endswith("oms_sensemaking/core/controllers.py")
    assert log.acm is not None and log.acm == SETTINGS.audit_log_error_acm
    assert log.version == __version__


def test_db_logging_within_sensemaker(
    mock_controller: SensemakerController, db: Session, session_local, mock_oms_crud_tool, ts_acm
):
    """Test that errors are logged to DB"""

    sensemaker = DummySensemaker(mock_oms_crud_tool)
    mock_controller.register("dummy", sensemaker)

    node_id = str(uuid.uuid4())
    event = AuditLogEvent(objectId=node_id, userId="user", objectType="NODE", action="CREATE")
    mock_node = NodeNode.model_construct(id=node_id, acm=ts_acm)
    mock_controller.oms_crud_tool.rehydrate_oms_obj = mock.MagicMock(return_value=mock_node)
    sensemaker.process_data = mock.MagicMock(side_effect=SensemakingError("sensemaker failed"))

    with pytest.raises(SensemakingError):
        mock_controller.handle_event(event)

    # check that AuditLogErrors were created
    logs = db.execute(select(AuditLogError).order_by(desc(AuditLogError.created_at))).scalars().all()

    assert len(logs) == 1, "Error should be found when TypeError occurs during process_data"
    log = logs[0]
    assert log.object_id == uuid.UUID(node_id)
    assert log.object_type == "NODE"
    assert log.event_type == "CREATE"
    assert log.function_name == "execute"  # execute since process_data is in this tests_int dir
    assert isinstance(log.line_no, int)
    assert "Any = self.process_data(*data)" in log.code
    assert node_id in log.message
    assert "sensemaker failed" in log.exc_text
    assert log.exception_name == "SensemakingError"
    assert log.module_name.endswith("oms_sensemaking/core/sensemakers.py")
    assert log.acm is not None and log.acm == ts_acm
    assert log.version == __version__
