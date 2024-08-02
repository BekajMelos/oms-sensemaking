"""Module for listening on an SQS Queue and handling geo attributes"""

import logging
import uuid
from typing import Dict, Optional

import dateutil
import dateutil.parser
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.input_types import (
    IdQuery,
    RelationshipNodeQuery,
    RelationshipQuery,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.sqs_listener import SQSListener
from oms_sensemaking.geospatial.tracks import PointAttribute

LOGGER = logging.getLogger(__name__)


ATTRIBUTE_OBJECT_TYPE = "ATTRIBUTE"
CREATE_EVENT_TYPE = "CREATE"
SPATIOTEMPORAL_ATTR_TYPE = "spatiotemporal"


class GeoSQSListener(SQSListener):
    """Class for listening to Geo objects on an SQS Queue"""

    async def handle_sqs_event(self, event: Dict) -> None:
        """Checks that the event is valid, creates an attribute object and puts it on the queue.

        :param event: SQS Message Body
        :return: None
        """

        # ignore if not the right type of event
        if event["objectType"] != ATTRIBUTE_OBJECT_TYPE or event["eventType"] != CREATE_EVENT_TYPE:
            return

        try:
            oms_attr = await self.get_oms_attribute(event["objectId"])
        except KeyError:
            return

        if oms_attr:
            track_node_id = await self.get_track_node_id(oms_attr)
            if track_node_id:
                # TODO use the oms_common_utils_python Attribute object? or TrackEntry? or Processed Point
                attribute = PointAttribute(
                    track_node_id,
                    oms_attr.geo.geoJson["coordinates"][1],
                    oms_attr.geo.geoJson["coordinates"][0],
                    dateutil.parser.isoparse(oms_attr.geo.startTime),
                )

                # Place on the Queue for the Track Cache to receive
                await self.q.put(attribute)

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
            oms_attr.attributeType.lower() != SPATIOTEMPORAL_ATTR_TYPE
            or oms_attr.geo.geoJson.get("type").lower() != "point"
        ):
            return None

        return oms_attr

    async def get_track_node_id(self, oms_attr: AttributeAttribute) -> Optional[uuid.UUID]:
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
        return rel.data[0].startNodeId
