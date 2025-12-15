"""Attribute sensemaker controller."""

import logging

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import AuditLogEvent, EventFilter
from oms_sensemaking.domain.area_of_interest.aoi_extractor import RealAOIDataExtractor
from oms_sensemaking.inference.rules.in_out_garrison import InOrOutOfGarrison
from oms_sensemaking.inference.rules.incursions import Incursion

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
            self.register("incursion", Incursion(RealAOIDataExtractor(), self.oms_crud_tool))
            self.register("garrison", InOrOutOfGarrison(self.oms_crud_tool))

        super().start()


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
