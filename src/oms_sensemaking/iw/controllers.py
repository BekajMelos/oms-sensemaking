"""Observable controller"""

import logging
from collections.abc import Callable

from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import AuditLogEvent
from oms_sensemaking.core.observability import with_metrics_collection

from .sensemakers.process_observables import process_observables

LOGGER: logging.Logger = logging.getLogger(__name__)
EVENT_HANDLER = Callable[[AuditLogEvent], bool]


class ObservableSensemakerController(SensemakerController):
    @with_metrics_collection
    def handle_event(self, event: AuditLogEvent) -> bool:
        process_observables()
        return True
