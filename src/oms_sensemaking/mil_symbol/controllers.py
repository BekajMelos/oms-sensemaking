"""Military Symbol sensemaker controller."""

import json
import logging

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import (
    EventFilter,
    ObjectEvent,
)
from oms_sensemaking.mil_symbol.sensemaker import MilSymbolSensemaker

LOGGER: logging.Logger = logging.getLogger(__name__)


class MilSymbolSensemakerController(SensemakerController):
    """
    MilSymbol sensemaker controller.

    This class manages a collection of military symbol sensemakers.
    """

    def start(self) -> None:
        """Start the controller."""
        if SETTINGS.mil_symbol_settings.enable_mil_symbol_sensemaker:

            with open(SETTINGS.mil_symbol_settings.rules_file_path) as fd:
                mil_symbol_rules = json.load(fd)

            self.register("mil_symbol", MilSymbolSensemaker(mil_symbol_rules, self.oms_crud_tool))

        super().start()

class MilSymbolQueueFilter(EventFilter):
    def passes_filter(self, object_event: ObjectEvent):
        return object_event.objectType == ObjectType.NODE.value and object_event.eventType == Action.CREATE.value
