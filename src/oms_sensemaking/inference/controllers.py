"""Attribute sensemaker controller."""

import logging
from typing import Optional
from uuid import UUID

from oms_sdk import get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.client import Client
from oms_sdk.generated.generated_graphql_client.input_types import IdQuery

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import ObjectEvent, ObjectEventConsumer
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.inference.sensemakers.inference import InferenceSensemaker

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
        LOGGER.warning(f"{vars(event)}")

        if isinstance(self.event_consumer, ObjectEventConsumer):
            # extract info from OMS via API calls
            oms_attr: Optional[AttributeAttribute] = self.get_oms_attribute(event.objectId)

            # right now we only expect attributes, skip if it's not an attribute
            if not oms_attr:
                return True

            for sensemaker in self._registry.values():
                sensemaker.execute(oms_attr)

            return True

        else:
            LOGGER.warning("No ObjectEventConsumer found.")

        return False

    def get_oms_attribute(self, attribute_id: UUID) -> Optional[AttributeAttribute]:
        """
        Given an OMS Attribute ID, get the OMS Attribute.

        :param attribute_id: ID of the attribute
        :return: None if no attribute exists, or the OMS Attribute
        """
        # get attribute
        oms_attr: AttributeAttribute = self.oms_client.attribute(IdQuery(id=attribute_id))

        # Only process if we got an attibute back
        # TODO:  Is this necessary? attribute query already return Attribute or None
        if not oms_attr:
            return None

        return oms_attr
