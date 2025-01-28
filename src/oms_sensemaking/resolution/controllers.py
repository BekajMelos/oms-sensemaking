"""Resolution sensemaker controller."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.enums import Action

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import (
    EventFilter,
    ObjectEvent,
    ObjectEventConsumer,
    ObjectType,
    SQSListener,
)
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.resolution.sensemaker import ResolutionSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class ResolutionSensemakerController(SensemakerController):
    """
    Resolution sensemaker controller.

    This class manages a collection of resolution sensemakers.
    """

    def __init__(self, event_consumer: ObjectEventConsumer) -> None:
        """Create a new instance of ResolutionSensemakerController."""
        super().__init__(event_consumer)

        self.oms_crud_tool = OmsCrudTool()

    def start(self) -> None:
        """Start the controller."""
        if SETTINGS.enable_resolution_sensemaker:
            self.register("resolution", ResolutionSensemaker(self.oms_crud_tool))

        super().start()

    def stop(self):
        """
        Stop the controller.

        This method handles stopping the buffer autoflush in addition to
        stopping the controller itself.
        """
        LOGGER.debug("Stopping")

        super().stop()

    def handle_event(self, event: ObjectEvent) -> bool:
        """
        Handle inbound OMS event.

        :param event: The event to process.
        """

        LOGGER.debug("Received ObjectEvent(objectId=%s)", event.objectId)

        if isinstance(self.event_consumer, SQSListener):

            # extract info from OMS via API calls
            oms_attr: Optional[AttributeAttribute] = self.oms_crud_tool.get_attribute(event.objectId)
            if not oms_attr:
                return True

            try:
                with ThreadPoolExecutor() as executor:
                    futures = []
                    for sensemaker in self._registry.values():
                        future = executor.submit(sensemaker.execute, oms_attr)
                        futures.append(future)

                    # make sure errors are caught
                    for future in as_completed(futures):
                        _ = future.result()

                    executor.shutdown(wait=True)
            except Exception:
                LOGGER.exception(f"Error encountered while processing object {event.objectId}")

        else:
            LOGGER.warning("No ObjectEventConsumer found.")

        return True


class ResolutionQueueFilter(EventFilter):
    def passes_filter(self, object_event: ObjectEvent):
        return object_event.objectType == ObjectType.ATTRIBUTE.value and object_event.eventType == Action.CREATE.value
