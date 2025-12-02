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
    """Class for filtering AuditLogEvents being processed by the Inference Sensemaker"""

    def __init__(self) -> None:
        self.ignored_track_obs_iri = SETTINGS.track_iri

    def passes_filter(self, audit_log_event: AuditLogEvent) -> bool:
        """Filter AuditLogEvents being processed by the Inference Sensemaker"""
        handled_event_types = [Action.CREATE, Action.RESTORE]
        return (
            audit_log_event.objectType == ObjectType.OBSERVATION.value
            and audit_log_event.action in handled_event_types
            and audit_log_event.headers.iri != self.ignored_track_obs_iri
        )
