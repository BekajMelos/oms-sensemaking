"""COCOM traversal sensemaker controller"""

import logging

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.cocom.sensemaker import COCOMTraversalSensemaker
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import AuditLogEvent, EventFilter

LOGGER: logging.Logger = logging.getLogger(__name__)


class COCOMTraversalSensemakerController(SensemakerController):
    """
    COCOM Traversal sensemaker controller.

    This class manages a collection of COCOM traversal sensemakers.
    """

    def start(self) -> None:
        """Start the controller"""
        if SETTINGS.cocom_traversal_settings.detect_cocom_traversals:
            self.register("COCOM traversal", COCOMTraversalSensemaker(self.oms_crud_tool))

        super().start()


class COCOMTraversalQueueFilter(EventFilter):
    def passes_filter(self, audit_event: AuditLogEvent):
        return audit_event.objectType == ObjectType.NODE.value and audit_event.action == Action.UPDATE.value
