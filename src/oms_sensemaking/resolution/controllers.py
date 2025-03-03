"""Resolution sensemaker controller."""

import logging

from oms_sdk.generated.generated_graphql_client.enums import Action

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import (
    AuditLogEvent,
    EventFilter,
    ObjectType,
)
from oms_sensemaking.resolution.sensemaker import ResolutionSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class ResolutionSensemakerController(SensemakerController):
    """
    Resolution sensemaker controller.

    This class manages a collection of resolution sensemakers.
    """

    def start(self) -> None:
        """Start the controller."""
        if SETTINGS.enable_resolution_sensemaker:
            self.register("resolution", ResolutionSensemaker(self.oms_crud_tool))

        super().start()


class ResolutionQueueFilter(EventFilter):
    def passes_filter(self, audit_event: AuditLogEvent):
        handled_object_types = [ObjectType.ATTRIBUTE.value]
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value]
        return audit_event.objectType in handled_object_types and audit_event.action in handled_event_types
