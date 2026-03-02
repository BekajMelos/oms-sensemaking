"""Object standards sensemaker controller."""

import json
import logging
from itertools import chain

from oms_sdk.generated.generated_graphql_client.enums import Action

from oms_sensemaking.clients.instances import ontology_service
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import (
    AuditLogEvent,
    EventFilter,
    ObjectType,
)
from oms_sensemaking.object_standards.sensemaker import (
    ObjectStandards,
    ObjectStandardsDataRetriever,
    ObjectStandardsRubric,
)

LOGGER: logging.Logger = logging.getLogger(__name__)


class ObjStandardsDataProvider:
    def __init__(self, file_path=SETTINGS.object_standards_settings.rubrics_file_path) -> None:
        self.file_path = file_path
        self.entries = self._load_from_json()
        self.criteria = list(
            chain.from_iterable(
                entry.get(key, []) for entry in self.entries.values() for key in ("ATTRIBUTES", "RELATIONSHIPS")
            )
        )

    def _load_from_json(self):
        with open(self.file_path) as file:
            data = json.load(file)
        return data


class ObjectStandardsSensemakerController(SensemakerController):
    """
    Resolution sensemaker controller.

    This class manages a collection of resolution sensemakers.
    """

    def start(self) -> None:
        """Start the controller."""
        if SETTINGS.object_standards_settings.enable_object_standards_sensemaker:
            with open(SETTINGS.object_standards_settings.rubrics_file_path) as fd:
                rubric_criteria = json.load(fd)

            self.register(
                "object standards",
                ObjectStandards(
                    self.oms_crud_tool,
                    ontology_service,
                    ObjectStandardsDataRetriever(),
                    ObjectStandardsRubric(),
                    rubric_criteria,
                ),
            )
        super().start()


class ObjectStandardsQueueFilter(EventFilter):
    # Should we also do node creation as an event we care about to assign it a score of 0?
    def __init__(self, data_provider: ObjStandardsDataProvider) -> None:
        self.obj_standards_data = data_provider

    def passes_filter(self, audit_log_event: AuditLogEvent) -> bool:
        handled_object_types = [ObjectType.ATTRIBUTE.value, ObjectType.RELATIONSHIP.value]
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value, Action.UPDATE.value, Action.DELETE.value]
        criteria = self.obj_standards_data.criteria
        return (
            audit_log_event.objectType in handled_object_types
            and audit_log_event.action in handled_event_types
            and audit_log_event.headers.iri in criteria
        )
