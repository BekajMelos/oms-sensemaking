"""Module for listening on an SQS Queue and handling geo attributes"""

import asyncio
import logging
import uuid
from datetime import timezone
from typing import Dict, Optional

from dateutil.parser import isoparse
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.enums import Action, AttributeType, ObjectType
from oms_sdk.generated.generated_graphql_client.input_types import (
    IdQuery,
    RelationshipNodeQuery,
    RelationshipQuery,
)
from oms_sdk.generated.generated_graphql_client.node import NodeNode

from oms_sensemaking.clients import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.sqs_listener import SQSListener
from oms_sensemaking.models.geo import Point

LOGGER = logging.getLogger(__name__)


class GeoSQSListener(SQSListener):
    """Class for listening to Geo objects on an SQS Queue"""

    def __init__(self, track_cache_queue: asyncio.Queue):
        super().__init__()
        self.track_cache_queue: asyncio.Queue = track_cache_queue

    async def handle_sqs_event(self, event: Dict) -> None:
        """Checks that the event is valid, creates an attribute object and puts it on the queue.

        :param event: SQS Message Body
        :return: None
        """

        # ignore if not the right type of event
        if event["objectType"] != ObjectType.ATTRIBUTE.value or event["eventType"] != Action.CREATE.value:
            return

        try:
            oms_attr = await self.get_oms_attribute(event["objectId"])
        except KeyError:
            return

        if oms_attr:
            track_node = await self.get_track_node(oms_attr)
            if track_node:
                point = Point(
                    acm=oms_attr.acm,
                    location=(f'Point({oms_attr.geo.geoJson["coordinates"][0]} '
                              f'{oms_attr.geo.geoJson["coordinates"][1]})'),
                    altitude=None,  # TODO include this
                    detection_time=isoparse(oms_attr.geo.startTime).replace(tzinfo=timezone.utc),
                    node_id=track_node.id,
                    node_version=track_node.version,
                    attribute_id=oms_attr.id,
                    attribute_version=oms_attr.version
                )

                with db_session() as db:
                    # we're still using the point object for detections, so don't expire it
                    db.expire_on_commit = False
                    db.add(point)
                    db.commit()

                # Place on the Queue for the Track Cache to receive
                await self.track_cache_queue.put(point)

    async def get_oms_attribute(self, attribute_id: uuid.UUID) -> Optional[AttributeAttribute]:
        """
        Given an OMS Attribute ID, get the OMS Attribute.

        :param attribute_id: ID of the attribute
        :return: None if no attribute exists, or the OMS Attribute
        """

        # get attribute
        oms_attr: AttributeAttribute = self.graphql_client.attribute(IdQuery(id=attribute_id))

        # Filter Attributes
        # Only process if there is a node ID
        if not oms_attr or oms_attr.nodeId is None:
            return None
        # Only process if this is a spatiotemporal attribute with a Point
        if (
            oms_attr.attributeType != AttributeType.SPATIOTEMPORAL.value
            or oms_attr.geo.geoJson.get("type").lower() != "point"
        ):
            return None

        return oms_attr

    async def get_track_node(self, oms_attr: AttributeAttribute) -> Optional[NodeNode]:
        """
        Given an OMS Observation Geo Attribute, get the associated Flight Activity Node - AKA Track Node ID.

        :param attribute_id: Attribute object
        :return: None if no relationship exists, or the Track Node id
        """

        # get relationship
        observation_node_id = oms_attr.nodeId
        rel = self.graphql_client.relationships(
            query=RelationshipQuery(
                nodes=RelationshipNodeQuery(endNodeIds=[observation_node_id]),
                objectPropertyIris=[SETTINGS.operated_by_iri],
            )
        )

        if not len(rel.data) > 0:
            return None

        # ADSB Flight Activity Node. AKA Track Node ID
        track_node_id = rel.data[0].startNodeId

        node = self.graphql_client.node(query=IdQuery(id=track_node_id))

        if not node:
            return None

        return node
