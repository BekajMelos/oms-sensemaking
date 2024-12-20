"""Attribute sensemaker controller."""

import logging

from oms_sdk import get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client.client import Client

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import ObjectEvent, ObjectEventConsumer
from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER: logging.Logger = logging.getLogger(__name__)


class InferenceSensemakerController(SensemakerController):
    def __init__(self, event_consumer: ObjectEventConsumer) -> None:
        """Create a new instance of InferenceSensemakerController."""
        super().__init__(event_consumer)

        #: OMS GraphQL client
        self.oms_client: Client = get_generated_graphql_client(
            SETTINGS.omsb_url, SETTINGS.user_dn, SETTINGS.cert_path, SETTINGS.key_path
        )
        self.oms_crud_tool = OmsCrudTool()

    def handle_event(self, event: ObjectEvent) -> bool:
        """
        Handle inbound OMS event.

        :param event: The event to process.
        """
        LOGGER.debug("Received ObjectEvent(objectId=%s)", event.objectId)

        return True
