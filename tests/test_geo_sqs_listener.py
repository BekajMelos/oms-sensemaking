import asyncio
import logging
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from oms_sdk.generated.generated_graphql_client.attribute import (
    AttributeAttribute,
    AttributeAttributeGeo,
)
from oms_sdk.generated.generated_graphql_client.relationships import (
    RelationshipsRelationships,
    RelationshipsRelationshipsData,
)
from oms_sensemaking.geospatial.geo_sqs_listener import (
    ATTRIBUTE_OBJECT_TYPE,
    CREATE_EVENT_TYPE,
    SPATIOTEMPORAL_ATTR_TYPE,
    GeoSQSListener,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_handle_sqs_event():
    q = asyncio.Queue()
    sqs_listener = GeoSQSListener(q)

    # invalid objectType shouldn't be put in the queue
    event = {"objectType": "invalid type"}
    await sqs_listener.handle_sqs_event(event)
    assert q.empty

    # invalid eventType shouldn't be put in the queue
    event = {"objectType": ATTRIBUTE_OBJECT_TYPE, "eventType": "invalid type"}
    await sqs_listener.handle_sqs_event(event)
    assert q.empty

    # invalid objectId must be included
    event = {"objectType": ATTRIBUTE_OBJECT_TYPE, "eventType": CREATE_EVENT_TYPE}
    await sqs_listener.handle_sqs_event(event)
    assert q.empty

    # valid
    object_id = uuid.uuid4()
    event = {"objectType": ATTRIBUTE_OBJECT_TYPE, "eventType": CREATE_EVENT_TYPE, "objectId": object_id}

    # mock API calls
    sqs_listener.get_oms_attribute = AsyncMock()
    sqs_listener.get_track_node_id = AsyncMock()
    start_time = datetime.now().isoformat()
    track_node_id = uuid.uuid4()
    sqs_listener.get_oms_attribute.return_value = AttributeAttribute.model_construct(
        id=object_id,
        nodeId=uuid.uuid4(),
        attributeType=SPATIOTEMPORAL_ATTR_TYPE,
        geo=AttributeAttributeGeo(
            geoJson={"type": "POINT", "coordinates": [0, 0]}, mgrs="dummy", startTime=start_time, endTime=start_time
        ),
    )
    sqs_listener.get_track_node_id.return_value = track_node_id

    # test
    await sqs_listener.handle_sqs_event(event)
    point_attribute = await q.get()
    assert point_attribute.track_node_id == track_node_id
    assert point_attribute.timestamp.isoformat() == start_time


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
            attributeType=SPATIOTEMPORAL_ATTR_TYPE.upper(),
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
            attributeType=SPATIOTEMPORAL_ATTR_TYPE.upper(),
            geo=AttributeAttributeGeo(
                geoJson={"type": "Point"}, mgrs="dummy", startTime=datetime.now(), endTime=datetime.now()
            ),
        )
        oms_attr = await sqs_listener.get_oms_attribute(uuid.uuid4())
        assert oms_attr == mock_get_attribute.return_value


@pytest.mark.asyncio
async def test_get_track_node_id():
    q = asyncio.Queue()
    sqs_listener = GeoSQSListener(q)

    with patch(
        "oms_sdk.generated.generated_graphql_client.client.Client.relationships"
    ) as mock_get_relationships:
        attr_attr = AttributeAttribute.model_construct(
            id=uuid.uuid4(),
            nodeId=uuid.uuid4(),
            attributeType=SPATIOTEMPORAL_ATTR_TYPE.upper(),
            geo=AttributeAttributeGeo(
                geoJson={"type": "Point"}, mgrs="dummy", startTime=datetime.now(), endTime=datetime.now()
            ),
        )

        # Test when there is no relationship for that attribute
        mock_get_relationships.return_value = RelationshipsRelationships(totalSize=0, rollupAcm={}, data=[])
        track_node_id = await sqs_listener.get_track_node_id(attr_attr)
        assert track_node_id is None

        # Test valid return value
        valid_relationship = RelationshipsRelationshipsData.model_construct(startNodeId=uuid.uuid4())
        mock_get_relationships.return_value = RelationshipsRelationships(
            totalSize=1, rollupAcm={}, data=[valid_relationship]
        )
        track_node_id = await sqs_listener.get_track_node_id(attr_attr)
        assert track_node_id == valid_relationship.startNodeId
