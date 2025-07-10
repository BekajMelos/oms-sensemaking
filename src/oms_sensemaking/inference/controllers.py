"""Attribute sensemaker controller."""

import logging

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import AuditLogEvent, EventFilter
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

    def get_oms_data(self, event: AuditLogEvent) -> RuleContext | None:
        """
        Given an OMS data object's ID, get the object we'll pass to the sensemaker

        :param event: the object whose creation, update, or deletion we need to process
        :return: None if no object exists, or the OMS Object if it's a type we handle
        """

        oms_obj = super().get_oms_data(event)

        if event.objectType == ObjectType.ATTRIBUTE:
            return RuleContext(attribute=oms_obj) if oms_obj else None
        if event.objectType == ObjectType.OBSERVATION:
            return RuleContext(observation=oms_obj) if oms_obj else None
        if event.objectType == ObjectType.ACTIVITY:
            return RuleContext(activity=oms_obj) if oms_obj else None
        return None


class InferenceQueueFilter(EventFilter):
    def passes_filter(self, audit_event: AuditLogEvent):
        handled_object_types = [ObjectType.ACTIVITY.value, ObjectType.ATTRIBUTE.value, ObjectType.OBSERVATION.value]
        handled_event_types = [Action.CREATE, Action.RESTORE]
        return audit_event.objectType in handled_object_types and audit_event.action in handled_event_types
