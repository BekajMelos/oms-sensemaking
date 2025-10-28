"""Military Symbol sensemaker controller."""

import json
import logging

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType

from oms_sensemaking.clients.instances import ontology_service
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import (
    AuditLogEvent,
    EventFilter,
)
from oms_sensemaking.mil_symbol.get_attributes import GetMilSymbolAttributeFactory
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

            self.register(
                "mil_symbol",
                MilSymbolSensemaker(
                    mil_symbol_rules,
                    self.oms_crud_tool,
                    ontology_service,
                    GetMilSymbolAttributeFactory(self.oms_crud_tool).get_attribute_retriever(
                        SETTINGS.mil_symbol_settings.mil_sym_attr_retriever
                    ),
                ),
            )

        super().start()


class MilSymbolQueueFilter(EventFilter):
    def __init__(self) -> None:
        self.handled_iris = (
            SETTINGS.mil_symbol_settings.affiliation_iris
            + SETTINGS.mil_symbol_settings.echelon_iris
            + SETTINGS.mil_symbol_settings.status_iris
        )

    def passes_filter(self, audit_event: AuditLogEvent):
        return self.passes_node_filter(audit_event) or self.passes_attribute_filter(audit_event)

    def passes_node_filter(self, audit_event: AuditLogEvent):
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value]
        return audit_event.objectType == ObjectType.NODE.value and audit_event.action in handled_event_types

    def passes_attribute_filter(self, audit_event: AuditLogEvent):
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value, Action.UPDATE.value]

        return (
            audit_event.objectType == ObjectType.ATTRIBUTE.value
            and audit_event.action in handled_event_types
            and audit_event.headers.iri in self.handled_iris
        )
