"""COCOM traversal sensemaker controller"""

import logging
from uuid import UUID

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from oms_sdk.generated.generated_graphql_client.observation import ObservationObservation

from oms_sensemaking.cocom.sensemaker import COCOMTraversalSensemaker
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.error_loggers import BaseErrorLogger
from oms_sensemaking.core.events import AuditLogEvent, AuditLogEventConsumer, EventFilter

LOGGER: logging.Logger = logging.getLogger(__name__)


class COCOMTraversalSensemakerController(SensemakerController):
    """
    COCOM Traversal sensemaker controller.

    This class manages a collection of COCOM traversal sensemakers.
    """

    def __init__(self, event_consumer: AuditLogEventConsumer, err_logger: BaseErrorLogger) -> None:
        """Create a new instance of InPortSensemakerController."""
        super().__init__(event_consumer, err_logger)

    def start(self) -> None:
        """Start the controller"""
        if SETTINGS.cocom_traversal_settings.detect_cocom_traversals:
            self.register("COCOM traversal", COCOMTraversalSensemaker(self.oms_crud_tool))

        super().start()

    def handle_event(self, event: AuditLogEvent) -> bool:
        """
        Handle inbound ATOMS event.

        :param event: The event to process.
        :return: True if the audit log event was successfully processed, False otherwise.
        """
        LOGGER.debug("Received AuditLogEvent(objectId=%s)", event.objectId)

        # Retrieve observation
        oms_obs = self.get_oms_observation(event.objectId)

        return bool(not oms_obs)

    def get_oms_observation(self, observation_id: UUID) -> ObservationObservation | None:
        """
        Given an ATOMS Observation ID, get the ATOMS Observation.

        :param observation_id: ID of the observation
        :return: None if no observation exists, or the ATOMS Observation
        """
        # get observation
        oms_obs: ObservationObservation = self.oms_crud_tool.get_observation(observation_id)

        # Filter observations
        # Only process if there is an observation
        if not oms_obs:
            return None

        return oms_obs


class COCOMTraversalQueueFilter(EventFilter):
    def passes_filter(self, audit_event: AuditLogEvent):
        handled_object_types = [ObjectType.OBSERVATION.value]
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value, Action.UPDATE.value]
        return audit_event.objectType in handled_object_types and audit_event.action in handled_event_types
