"""Resolution sensemaker controller."""

import json
import logging
from itertools import chain

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
            duplicate_object_iris = ResolutionJsonLoader()
            self.register("resolution", ResolutionSensemaker(duplicate_object_iris.iris, self.oms_crud_tool))
        super().start()


class ResolutionQueueFilter(EventFilter):
    def __init__(self) -> None:
        self.duplicate_object_iris = ResolutionJsonLoader()

    def passes_filter(self, audit_log_event: AuditLogEvent) -> bool:
        handled_object_types = [ObjectType.ATTRIBUTE.value]
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value]
        attribute_iris = list(chain.from_iterable(self.duplicate_object_iris.iris.values()))
        return (
            audit_log_event.objectType in handled_object_types
            and audit_log_event.action in handled_event_types
            and audit_log_event.headers.iri in attribute_iris
        )


class ResolutionJsonLoader:
    def __init__(self, file_path=SETTINGS.duplicate_object_iris_file_path) -> None:
        self.file_path = file_path
        self.iris = self._load_from_json()

    def _load_from_json(self):
        with open(self.file_path) as file:
            data = json.load(file)
        return data
