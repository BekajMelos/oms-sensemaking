"""Attribute sensemaker controller."""

import logging

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import AuditLogEvent, AuditLogEventConsumer, EventFilter
from oms_sensemaking.inference.rules.rule_context import RuleContext
from oms_sensemaking.inference.sensemakers.inference import InferenceSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class InferenceSensemakerController(SensemakerController):
    """
    Inference sensemaker controller.

    This class manages a collection of inference sensemakers.
    """

    def start(self) -> None:
        # check to make sure its starting
        """Start the controller."""
        if SETTINGS.generate_inferences:
            self.register("inference", InferenceSensemaker())

        super().start()

    def handle_event(self, event: AuditLogEvent) -> bool:
        """
        Handle inbound OMS event.

        :param event: The event to process.
        :return: True if the audit log event was successfully processed, False otherwise.
        """
        LOGGER.debug(f"Received AuditLogEvent(objectId={event.objectId})")

        if isinstance(self.event_consumer, AuditLogEventConsumer):
            # extract info from OMS via API calls
            oms_data = self.get_oms_data(event)

            # skip if we can't rehydrate the data
            if not oms_data:
                return True

            for sensemaker in self._registry.values():
                sensemaker.execute(oms_data)
            return True

        else:
            LOGGER.warning("No AuditLogEventConsumer found.")

        return False

    def get_oms_data(self, event: AuditLogEvent) -> RuleContext | None:
        """
        Given an OMS data object's ID, get the object we'll pass to the sensemaker

        :param event: the object whose creation, update, or deletion we need to process
        :return: None if no object exists, or the OMS Object if it's a type we handle
        """

        if event.objectType == ObjectType.ATTRIBUTE:
            attribute = self.oms_crud_tool.get_attribute(event.objectId)
            return RuleContext(attribute=attribute) if attribute else None
        elif event.objectType == ObjectType.OBSERVATION:
            observation = self.oms_crud_tool.get_observation(event.objectId)
            return RuleContext(observation=observation) if observation else None
        elif event.objectType == ObjectType.ACTIVITY:
            activity = self.oms_crud_tool.get_activity(event.objectId)
            return RuleContext(activity=activity) if activity else None
        return None


class InferenceQueueFilter(EventFilter):
    """Class for filtering AuditLogEvents being processed by the Inference Sensemaker"""

    def passes_filter(self, audit_log_event: AuditLogEvent) -> bool:
        """Filter AuditLogEvents being processed by the Inference Sensemaker"""
        handled_event_types = [Action.CREATE, Action.RESTORE]
        return (audit_log_event.objectType == ObjectType.OBSERVATION.value and
                audit_log_event.action in handled_event_types)
