import asyncio
import logging
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute, AttributeAttributeGeo
from oms_sdk.generated.generated_graphql_client.enums import Action, AttributeType, ObjectType
from oms_sdk.generated.generated_graphql_client.node import NodeNode
from oms_sdk.generated.generated_graphql_client.relationships import (
    RelationshipsRelationships,
    RelationshipsRelationshipsData,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from oms_sensemaking.geospatial.geo_sqs_listener import GeoSQSListener
from oms_sensemaking.models.geo import Point

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_handle_sqs_event(db: Session):
    q = asyncio.Queue()
    sqs_listener = GeoSQSListener(q)

    # invalid objectType shouldn't be put in the queue
    event = {"objectType": "invalid type"}
    await sqs_listener.handle_sqs_event(event)
    assert q.empty

    # invalid eventType shouldn't be put in the queue
    event = {"objectType": ObjectType.ATTRIBUTE.value, "eventType": "invalid type"}
    await sqs_listener.handle_sqs_event(event)
    assert q.empty

    # invalid objectId must be included
    event = {"objectType": ObjectType.ATTRIBUTE.value, "eventType": Action.CREATE}
    await sqs_listener.handle_sqs_event(event)
    assert q.empty

    # valid
    object_id = uuid.uuid4()
    event = {"objectType": ObjectType.ATTRIBUTE.value, "eventType": Action.CREATE, "objectId": object_id}

    # mock API calls
    sqs_listener.get_oms_attribute = AsyncMock()
    sqs_listener.get_track_node = AsyncMock()
    start_time = datetime.now(tz=timezone.utc).isoformat()
    track_node_id = uuid.uuid4()
    sqs_listener.get_oms_attribute.return_value = AttributeAttribute.model_construct(
        id=object_id,
        nodeId=uuid.uuid4(),
        attributeType=AttributeType.SPATIOTEMPORAL.value,
        acm=DEFAULT_ACM,
        geo=AttributeAttributeGeo(
            geoJson={"type": "POINT", "coordinates": [0, 0]}, mgrs="dummy", startTime=start_time, endTime=start_time
        ),
        version=1,
    )
    sqs_listener.get_track_node.return_value = NodeNode.model_construct(id=track_node_id, version=1)

    # test
    await sqs_listener.handle_sqs_event(event)
    point: Point = await q.get()

    point_db = db.execute(
        select(
            Point
        ).where(
            Point.node_id == point.node_id,
            Point.attribute_id == point.attribute_id
        )
    ).scalars().one()

    # Test that the right object was put on the queue
    assert point.node_id == track_node_id
    assert point.detection_time.isoformat() == start_time
    assert point.node_version == 1
    assert point.attribute_version == 1
    assert point.node_id == track_node_id
    assert point.attribute_id == object_id

    # Test that the right object was put in the DB
    assert point_db.node_id == track_node_id
    assert point_db.detection_time.isoformat() == start_time
    assert point_db.node_version == 1
    assert point_db.attribute_version == 1
    assert point_db.node_id == track_node_id
    assert point_db.attribute_id == object_id


@pytest.mark.asyncio
async def test_get_oms_attribute():
    q = asyncio.Queue()
    sqs_listener = GeoSQSListener(q)

    with patch(
        "oms_sdk.generated.generated_graphql_client.client.Client.attribute"
    ) as mock_get_attribute:
        # Test when there is no attribute with that id
        mock_get_attribute.return_value = None
        oms_attr = await sqs_listener.get_oms_attribute(uuid.uuid4())
        assert oms_attr is None

        mock_get_attribute.return_value = AttributeAttribute.model_construct(id=uuid.uuid4(), nodeId=None)
        oms_attr = await sqs_listener.get_oms_attribute(uuid.uuid4())
        assert oms_attr is None

        # Test when the attribute is not a SPATIOTEMPORAL attribute
        mock_get_attribute.return_value = AttributeAttribute.model_construct(
            id=uuid.uuid4(), nodeId=None, attributeType="Not SPATIO"
        )
        oms_attr = await sqs_listener.get_oms_attribute(uuid.uuid4())
        assert oms_attr is None

        # Test when the attribute's geojson obj is not a Point
        mock_get_attribute.return_value = AttributeAttribute.model_construct(
            id=uuid.uuid4(),
            nodeId=None,
            attributeType=AttributeType.SPATIOTEMPORAL.value,
            geo=AttributeAttributeGeo(
                geoJson={"type": "LINESTRING"}, mgrs="dummy", startTime=datetime.now(), endTime=datetime.now()
            ),
        )
        oms_attr = await sqs_listener.get_oms_attribute(uuid.uuid4())
        assert oms_attr is None

        # Test when the attribute has the values that we need
        mock_get_attribute.return_value = AttributeAttribute.model_construct(
            id=uuid.uuid4(),
            nodeId=uuid.uuid4(),
            attributeType=AttributeType.SPATIOTEMPORAL.value,
            geo=AttributeAttributeGeo(
                geoJson={"type": "Point"}, mgrs="dummy", startTime=datetime.now(), endTime=datetime.now()
            ),
        )
        oms_attr = await sqs_listener.get_oms_attribute(uuid.uuid4())
        assert oms_attr == mock_get_attribute.return_value


@pytest.mark.asyncio
async def test_get_track_node():
    q = asyncio.Queue()
    sqs_listener = GeoSQSListener(q)

    with (patch("oms_sdk.generated.generated_graphql_client.client.Client.relationships") as mock_get_relationships,
          patch("oms_sdk.generated.generated_graphql_client.client.Client.node") as mock_get_node):

        attr_attr = AttributeAttribute.model_construct(
            id=uuid.uuid4(),
            nodeId=uuid.uuid4(),
            attributeType=AttributeType.SPATIOTEMPORAL.value,
            geo=AttributeAttributeGeo(
                geoJson={"type": "Point"}, mgrs="dummy", startTime=datetime.now(), endTime=datetime.now()
            ),
        )

        # Test when there is no relationship for that attribute
        mock_get_relationships.return_value = RelationshipsRelationships(totalSize=0, rollupAcm={}, data=[])
        track_node_id = await sqs_listener.get_track_node(attr_attr)
        assert track_node_id is None

        # Test valid return value
        node_id = uuid.uuid4()
        valid_relationship = RelationshipsRelationshipsData.model_construct(startNodeId=node_id)
        mock_get_node.return_value = NodeNode.model_construct(id=node_id)
        mock_get_relationships.return_value = RelationshipsRelationships(
            totalSize=1, rollupAcm={}, data=[valid_relationship]
        )
        track_node = await sqs_listener.get_track_node(attr_attr)
        assert track_node.id == node_id
