"""Attribute sensemaker controller."""

import logging

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import EventFilter, ObjectEvent, ObjectEventConsumer
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.inference.rules.rule_context import RuleContext
from oms_sensemaking.inference.sensemakers.inference import InferenceSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class InferenceSensemakerController(SensemakerController):
    def __init__(self, event_consumer: ObjectEventConsumer) -> None:
        """Create a new instance of InferenceSensemakerController."""
        super().__init__(event_consumer)
        self.oms_crud_tool = OmsCrudTool()

    def start(self) -> None:
        # check to make sure its starting
        """Start the controller."""
        if SETTINGS.generate_inferences:
            self.register("inference", InferenceSensemaker())

        super().start()

    def handle_event(self, event: ObjectEvent) -> bool:
        """
        Handle inbound OMS event.

        :param event: The event to process.
        :return: True if the object event was successfully processed, False otherwise.
        """
        LOGGER.debug("Received ObjectEvent(objectId=%s)", event.objectId)

        if isinstance(self.event_consumer, ObjectEventConsumer):
            # extract info from OMS via API calls
            oms_data = self.get_oms_data(event)

            # skip if we can't rehydrate the data
            if not oms_data:
                return True

            for sensemaker in self._registry.values():
                sensemaker.execute(oms_data)
            return True

        else:
            LOGGER.warning("No ObjectEventConsumer found.")

        return False

    def get_oms_data(self, event: ObjectEvent) -> RuleContext | None:
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
    def passes_filter(self, object_event: ObjectEvent):
        handled_object_types = [ObjectType.ACTIVITY.value, ObjectType.ATTRIBUTE.value, ObjectType.OBSERVATION.value]
        handled_event_types = [Action.CREATE]
        return object_event.objectType in handled_object_types and object_event.eventType in handled_event_types
