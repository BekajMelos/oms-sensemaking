"""Object minimums sensemaker controller."""

import json
import logging

from oms_sdk.generated.generated_graphql_client.enums import Action

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import (
    AuditLogEvent,
    EventFilter,
    ObjectType,
)
from oms_sensemaking.object_minimums.sensemaker import ObjectMinimumDataRetriever, ObjectMinimumRubric, ObjectMinimums

LOGGER: logging.Logger = logging.getLogger(__name__)


class ObjectMinimumsSensemakerController(SensemakerController):
    """
    Resolution sensemaker controller.

    This class manages a collection of resolution sensemakers.
    """

    def start(self) -> None:
        """Start the controller."""
        if SETTINGS.object_minimum_settings.enable_object_minimums_sensemaker:
            with open(SETTINGS.object_minimum_settings.rubrics_file_path) as fd:
                rubric_criteria = json.load(fd)

            self.register(
                "object minimums",
                ObjectMinimums(
                    self.oms_crud_tool,
                    ObjectMinimumDataRetriever(),
                    ObjectMinimumRubric(),
                    rubric_criteria,
                ),
            )
        super().start()


class ObjectMinimumsQueueFilter(EventFilter):
    # Should we also do node creation as an event we care about to assign it a score of 0?

    # we should implement a filter similar to the resolution sensemaker
    # to only keep attributes we care about

    def passes_filter(self, audit_log_event: AuditLogEvent) -> bool:
        handled_object_types = [ObjectType.ATTRIBUTE.value, ObjectType.RELATIONSHIP.value]
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value, Action.UPDATE.value, Action.DELETE.value]
        return audit_log_event.objectType in handled_object_types and audit_log_event.action in handled_event_types
