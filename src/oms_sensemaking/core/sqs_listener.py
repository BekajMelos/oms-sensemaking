"""Module for listening on an SQS Queue"""

import asyncio
import json
import logging
from typing import Dict

import boto3
import botocore
from oms_sdk import get_generated_graphql_client

from oms_sensemaking.config import SETTINGS

LOGGER = logging.getLogger(__name__)


class SQSListener:
    """Class for listening on an SQS Queue"""

    def __init__(self):
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
        self.graphql_client: get_generated_graphql_client.GeneratedClient = get_generated_graphql_client(
            SETTINGS.omsb_url, SETTINGS.user_dn, SETTINGS.cert_path, SETTINGS.key_path
        )

    async def listen(self) -> None:
        """Listen for messages on the SQS Queue and calls `handle_sqs_event`.

        :return: None
        """

        while True:
            LOGGER.info("Waiting for events in SQS")

            for _ in range(0, SETTINGS.sqs_read_loops):
                # Receive message from SQS queue
                try:
                    response = self.sqs.receive_message(
                        QueueUrl=SETTINGS.sqs_queue_url,
                        AttributeNames=["SentTimestamp"],
                        MaxNumberOfMessages=10,
                        MessageAttributeNames=["All"],
                        VisibilityTimeout=0,
                        WaitTimeSeconds=0,
                    )
                except botocore.exceptions.BotoCoreError as e:
                    LOGGER.error(f"Unable to connect to SQS: {e}. Trying again...")
                    break

                if "Messages" not in response:
                    continue

                for message in response["Messages"]:
                    await self.handle_sqs_event(json.loads(message["Body"]))

                    # Delete received message from queue - required so you don't get the same message
                    self.sqs.delete_message(QueueUrl=SETTINGS.sqs_queue_url, ReceiptHandle=message["ReceiptHandle"])

            await asyncio.sleep(SETTINGS.sqs_read_wait_seconds)

    async def handle_sqs_event(self, event: Dict) -> None:
        """Checks that the event is valid and puts it in the queue to be processed.

        Should be overriden but sub classes

        :param event: SQS Message Body
        :return: None
        """
        raise NotImplementedError
