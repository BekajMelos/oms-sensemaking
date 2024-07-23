"""Module for listening on an SQS Queue"""

import asyncio
import json
import logging
from typing import Dict

import boto3
from oms_sdk import get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client import Client as GeneratedClient

from oms_sensemaking.config import SETTINGS

LOGGER = logging.getLogger(__name__)


ATTRIBUTE_OBJECT_TYPE = "ATTRIBUTE"
CREATE_EVENT_TYPE = "CREATE"
SPATIOTEMPORAL_ATTR_TYPE = "spatiotemporal"


class SQSListener:
    """Class for listening on an SQS Queue"""

    def __init__(self, q: asyncio.Queue):
        self.q = q
        self.sqs = boto3.client(
            "sqs",
            region_name=SETTINGS.aws_region_name,
            use_ssl=SETTINGS.aws_use_ssl,
            verify=SETTINGS.aws_verify,
            endpoint_url=SETTINGS.aws_endpoint_url,
            aws_access_key_id=SETTINGS.aws_access_key_id,
            aws_secret_access_key=SETTINGS.aws_secret_access_key,
        )

        # OMS Connection
        self.graphql_client: GeneratedClient = get_generated_graphql_client(
            SETTINGS.omsb_url, SETTINGS.user_dn, SETTINGS.cert_path, SETTINGS.key_path
        )

    async def listen(self) -> None:
        """Listen for messages on the SQS Queue

        :return: None
        """

        while True:
            LOGGER.info("Waiting for events in SQS")

            for _ in range(0, SETTINGS.sqs_read_loops):
                # Receive message from SQS queue
                response = self.sqs.receive_message(
                    QueueUrl=SETTINGS.sqs_queue_url,
                    AttributeNames=["SentTimestamp"],
                    MaxNumberOfMessages=10,
                    MessageAttributeNames=["All"],
                    VisibilityTimeout=0,
                    WaitTimeSeconds=0,
                )

                if "Messages" not in response:
                    continue

                for message in response["Messages"]:
                    # Delete received message from queue - required so you don't get the same message
                    self.sqs.delete_message(QueueUrl=SETTINGS.sqs_queue_url, ReceiptHandle=message["ReceiptHandle"])

                    await self.handle_sqs_event(json.loads(message["Body"]))

            await asyncio.sleep(5)

    async def handle_sqs_event(self, event: Dict) -> None:
        """Checks that the event is valid and puts it in the queue to be processed

        Should be overriden but sub classes

        :param event: SQS Message Body
        :return: None
        """
        raise NotImplementedError
