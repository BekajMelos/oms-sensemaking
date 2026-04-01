"""In Port sensemaker controller."""

import logging

from oms_sdk.generated.generated_graphql_client import Action

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.error_loggers import BaseErrorLogger
from oms_sensemaking.core.events import (
    AuditLogEvent,
    AuditLogEventConsumer,
    EventFilter,
    ObjectType,
)
from oms_sensemaking.in_port.sensemaker import InPort

LOGGER: logging.Logger = logging.getLogger(__name__)


class InPortSensemakerController(SensemakerController):
    """
    In Port sensemaker controller.

    This class manages a collection of In Port sensemakers.
    """

    def __init__(self, event_consumer: AuditLogEventConsumer, err_logger: BaseErrorLogger) -> None:
        """Create a new instance of InPortSensemakerController."""
        super().__init__(event_consumer, err_logger)

    def start(self) -> None:
        """Start the controller."""
        if SETTINGS.in_port_settings.enable_in_port_sensemaker:
            self.register(
                "in port",
                InPort(self.oms_crud_tool),
            )

        super().start()


class InPortQueueFilter(EventFilter):
    def passes_filter(self, audit_log_event: AuditLogEvent) -> bool:
        handled_object_types = [ObjectType.OBSERVATION.value, ObjectType.OBSERVATION.value]
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value, Action.UPDATE.value, Action.DELETE.value]
        return audit_log_event.objectType in handled_object_types and audit_log_event.action in handled_event_types
