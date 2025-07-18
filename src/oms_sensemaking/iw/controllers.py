"""Observable controller"""

import logging
import time
from collections.abc import Callable
from uuid import uuid4

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import AuditLogEvent, AuditLogEventConsumer

from .sensemakers.process_observables import process_observables

LOGGER: logging.Logger = logging.getLogger(__name__)
EVENT_HANDLER = Callable[[AuditLogEvent], bool]


class PeriodicEventConsumer(AuditLogEventConsumer):
    """An event consumer that emits an event every 15 minutes."""

    def __init__(self, handle_event: EVENT_HANDLER | None = None):
        super().__init__(handle_event)
        self.interval = SETTINGS.iw_settings.observable_query_frequency * 60  # 15 minutes in seconds

    def process_audit_log_events(self) -> None:
        """Process audit log events periodically."""
        while not self.stopped.is_set():
            event = AuditLogEvent(
                userId="PeriodicEventConsumer", objectId=uuid4(), objectType=ObjectType.ATTRIBUTE, action=Action.CREATE
            )

            if callable(self.handle_event):
                LOGGER.info(f"Emitting periodic event at {time.time()}")
                self.handle_event(event)

            # Sleep for the interval or until stopped
            self.stopped.wait(timeout=self.interval)

    def start(self) -> None:
        """Start consuming events."""
        super().start()

    def stop(self) -> None:
        """Stop consuming events."""
        super().stop()


class ObservableSensemakerController(SensemakerController):
    def __init__(self):
        super().__init__(PeriodicEventConsumer())

    def handle_event(self, event: AuditLogEvent) -> bool:
        LOGGER.info(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\nObservableSensemakerController triggered at {time.time()}")
        process_observables()
        return True
