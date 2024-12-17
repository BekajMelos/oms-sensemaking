"""Attribute sensemaker controller."""

import logging
from datetime import datetime, timedelta, timezone
from oms_sensemaking.config import SETTINGS
from typing import Optional
from time import sleep
from threading import Event, Timer
from botocore.exceptions import BotoCoreError
from oms_sdk import get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client.enums import Action, AttributeType
from oms_sensemaking.core.controllers import SensemakerController
from oms_sdk.generated.generated_graphql_client.client import Client
from oms_sensemaking.core.oms_crud import OmsCrudTool
from uuid import UUID
from oms_sensemaking.core.events import (
    EVENT_HANDLER,
    ObjectEvent,
    ObjectEventConsumer,
    ObjectType,
    SQSListener,
)

LOGGER: logging.Logger = logging.getLogger(__name__)

class AttributeSQSListener(SQSListener):

    def __init__(self, handle_event: Optional[EVENT_HANDLER] = None):
        """Create a new instance of AttributeSqsObjectEventConsumer."""
        super().__init__(handle_event)

    def process_object_events(self) -> None:
        """Process geo-temporal object events from OMS."""
        if not callable(self.handle_event):
            raise ValueError(f"handle_event must be a callable object, got {type(self.handle_event)}")

        while not self.stopped.is_set():
            LOGGER.info("Waiting for events in SQS")

            for _ in range(0, SETTINGS.sqs_read_loops):
                if self.stopped.is_set():
                    LOGGER.debug("Shutting down AttributeSQSListener")
                    break

                # Receive message from SQS queue
                try:
                    response = self.sqs.receive_message(
                        QueueUrl=SETTINGS.sqs_attribute_queue_url,
                        AttributeNames=["SentTimestamp"],
                        MaxNumberOfMessages=10,
                        MessageAttributeNames=["All"],
                        VisibilityTimeout=0,
                        WaitTimeSeconds=0,
                    )
                except (BotoCoreError, self.sqs.exceptions.QueueDoesNotExist) as ex:
                    LOGGER.error(f"Unable to connect to SQS: {ex}. Trying again...")
                    break

                if "Messages" not in response:
                    LOGGER.debug("No Messages in response.")
                    sleep(SETTINGS.sqs_read_wait_seconds)
                    continue

                for message in response["Messages"]:
                    object_event: ObjectEvent = ObjectEvent.from_json((message["Body"]))

                    # ignore if not the right type of event
                    if ((object_event.objectType != ObjectType.ATTRIBUTE.value)
                            and (object_event.eventType != Action.CREATE.value)):
                        continue

                    # Modify this
                    LOGGER.info(f"Received Geo Attribute: {object_event.objectId}")

                    if self.handle_event(object_event):
                        # Delete received message from queue - required, so you don't get the same message
                        self.sqs.delete_message(
                            QueueUrl=SETTINGS.sqs_queue_url,
                            ReceiptHandle=message["ReceiptHandle"]
                        )
                    else:
                        LOGGER.warning("object event was not processed successfully.")

class AttributeSensemakerController(SensemakerController):
    def __init__(self, event_consumer: ObjectEventConsumer) -> None:
        """Create a new instance of AttributeSensemakerController."""
        super().__init__(event_consumer)

        # initialize buffer
        self.buffer: dict[UUID, Optional[datetime]] = {}
        self.autoflush_enabled: Event = Event()
        self.buffer_autoflush: Timer = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)

        #: OMS GraphQL client
        self.oms_client: Client = get_generated_graphql_client(
            SETTINGS.omsb_url, SETTINGS.user_dn, SETTINGS.cert_path, SETTINGS.key_path
        )
        self.oms_crud_tool = OmsCrudTool()
