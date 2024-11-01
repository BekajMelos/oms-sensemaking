"""Tests for loiter sensemaker."""

import random
from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import shapely
from geoalchemy2.shape import to_shape
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.client import (
    CreateAttributeInput,
    CreateNodeCreateNode,
    CreateNodeInput,
    CreateRelationshipInput,
)
from oms_sdk.generated.generated_graphql_client.enums import AttributeType, Confidence, ObjectTier
from oms_sdk.generated.generated_graphql_client.input_types import GeoInput
from sqlalchemy import select

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.geospatial.sensemakers.loiters import Loiter, LoiterSensemaker
from oms_sensemaking.models.geo import Point, Track
from oms_sensemaking.models.sensemaking import Finding, FindingType

ROLLUP_DEFAULT_ACM = {
    'version': '3.0',
    'classif_type': 'US',
    'classif': 'U',
    'owner_prod': ['USA'],
    'non_us_ctrls': [],
    'sci_ctrls': [],
    'disponly_to': [''],
    'dissem_ctrls': [],
    'non_ic': [],
    'rel_to': [],
    'fgi_open': [],
    'fgi_protect': [],
    'portion': 'U//DISPLAY ONLY',
    'banner': 'UNCLASSIFIED//DISPLAY ONLY',
    'dissem_countries': [],
    'accms': [],
    'macs': [],
    'oc_attribs': [{'orgs': [], 'missions': [], 'regions': []}],
    'share': {'users': [], 'projects': {}},
    'f_clearance': ['u'],
    'f_sci_ctrls': [],
    'f_accms': [],
    'f_oc_org': [],
    'f_regions': [],
    'f_missions': [],
    'f_share': [],
    'f_macs': []
}


def get_random_stamford_bridge_point() -> str:
    #  Get point near Stamford Bridge - all within geohash5 gcpug
    lon_max = -0.189286
    lon_min = -0.192512
    lat_max = 51.482857
    lat_min = 51.480729

    return shapely.Point(random.uniform(lon_min, lon_max), random.uniform(lat_min, lat_max)).wkt


def get_random_emirates_stadium_point() -> str:
    #  Get point near Emirates stadium - all within geohash5 gcpvm
    lon_max = -0.107211
    lon_min = -0.109761
    lat_max = 51.556461
    lat_min = 51.554000

    return shapely.Point(random.uniform(lon_min, lon_max), random.uniform(lat_min, lat_max)).wkt


def test_loiter_success(mock_oms_client, db):
    """Simple success track."""
    node_id = uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:16:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(acm=DEFAULT_ACM, location=p6_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # West London way later
    p7 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.413890, 51.474942).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:44:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7], node_id=node_id)

    # Set up mocks
    loiter_node_id = uuid4()
    mock_oms_client.create_node = MagicMock(
        return_value=CreateNodeCreateNode.model_construct(id=loiter_node_id, acm=p1.acm))
    mock_oms_client.create_relationship.return_value = MagicMock()
    mock_oms_client.create_attribute.return_value = MagicMock()
    loiters = LoiterSensemaker(mock_oms_client).execute(track)

    assert len(loiters) == 1
    loiter: Loiter = loiters[0]

    assert loiter.geohash_low == "gcpug"
    assert len(loiter.processed_points) == 5
    known_loiter_points = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points, loiter.processed_points, strict=False)
    )
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points])
    assert loiter.geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter.start_time == p2.detection_time
    assert loiter.end_time == p6.detection_time

    event_name = SETTINGS.loiter_event_name + '-' + str(node_id)
    tags = [SETTINGS.geo_sensemaker_event_tag]

    mock_oms_client.create_node.assert_called_with(
        CreateNodeInput(
            acm=ROLLUP_DEFAULT_ACM,
            name=event_name,
            tier=ObjectTier.DERIVATIVE,
            tags=tags,
            classIri=SETTINGS.loiter_event_node_iri,
            ifcCodes=set(),
            isNso=True
        ))

    mock_oms_client.create_relationship.assert_called_with(
        CreateRelationshipInput(
            tags=tags,
            name=event_name,
            startNodeId=loiter_node_id,
            endNodeId=node_id,
            confidence=Confidence.HIGH,
            acm=ROLLUP_DEFAULT_ACM,
            objectPropertyIri=SETTINGS.loiter_relationship_iri,
            sourceId=p1.source_id
        ))

    mock_oms_client.create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.loiter_event_node_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.SPATIOTEMPORAL.value,
            confidence=Confidence.HIGH,
            tags=tags,
            sourceId=p1.source_id,
            geo=GeoInput(
                geoJson=loiter.to_geojson(),
                startTime=p2.detection_time,
                endTime=p6.detection_time
                ),
            nodeId=loiter_node_id,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=p2.detection_time,
            valueEnd=p6.detection_time
        )
    )

    # check that loiters exist in Findings table
    findings = db.execute(
        select(
            Finding
        ).filter(
            Finding.finding_type == FindingType.GEO_LOITER.value
        )
    ).scalars().all()

    assert len(findings) == 1
    assert findings[0].finding_data['processed_points'][0]['location'] == to_shape(p2.location).wkt


def test_loiter_invalid_not_long_enough(mock_oms_client, db):
    """Loiter is only 8 minutes vs required 15."""
    node_id = uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # Still within stamford bridge but past the observation time
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T14:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5], node_id=uuid4())

    loiters = LoiterSensemaker(mock_oms_client).execute(track)
    assert len(loiters) == 0


def test_loiter_fails_valid_observed_threshold(mock_oms_client):
    """Failure. Unobserved for too long."""
    node_id = uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:40:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(acm=DEFAULT_ACM, location=p6_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:40:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # West London
    p7 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.413890, 51.474942).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T14:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7], node_id=uuid4())

    loiters = LoiterSensemaker(mock_oms_client).execute(track)
    assert len(loiters) == 0


def test_loiter_fails_valid_observed_threshold_within_geohash(mock_oms_client, db):
    """Don't remove valid loiters even if unobserved for too long."""
    # tests the find_prospective_loiters validity_time_diff

    node_id = uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:16:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(acm=DEFAULT_ACM, location=p6_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # Still within stamford bridge but past the observation time
    p7_point = get_random_stamford_bridge_point()
    p7 = Point(acm=DEFAULT_ACM, location=p7_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T14:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7], node_id=uuid4())

    # Set up mocks
    loiter_node_id = uuid4()
    mock_oms_client.create_node = MagicMock(
        return_value=CreateNodeCreateNode.model_construct(id=loiter_node_id, acm=p1.acm))
    mock_oms_client.create_relationship.return_value = MagicMock()
    mock_oms_client.create_attribute.return_value = MagicMock()

    loiters = LoiterSensemaker(mock_oms_client).execute(track)
    assert len(loiters) == 1
    loiter = loiters[0]

    assert loiter.geohash_low == "gcpug"
    assert len(loiter.processed_points) == 5
    known_loiter_points = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points, loiter.processed_points, strict=False)
    )
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points])
    assert loiter.geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter.start_time == p2.detection_time
    assert loiter.end_time == p6.detection_time

    event_name = SETTINGS.loiter_event_name + '-' + str(track.node_id)
    tags = [SETTINGS.geo_sensemaker_event_tag]

    mock_oms_client.create_node.assert_called_with(
        CreateNodeInput(
            acm=ROLLUP_DEFAULT_ACM,
            name=event_name,
            tier=ObjectTier.DERIVATIVE,
            tags=tags,
            classIri=SETTINGS.loiter_event_node_iri,
            ifcCodes=set(),
            isNso=True
        ))
    mock_oms_client.create_relationship.assert_called_with(
        CreateRelationshipInput(
            tags=tags,
            name=event_name,
            startNodeId=loiter_node_id,
            endNodeId=track.node_id,
            confidence=Confidence.HIGH,
            acm=ROLLUP_DEFAULT_ACM,
            objectPropertyIri=SETTINGS.loiter_relationship_iri,
            sourceId=p1.source_id
        ))
    mock_oms_client.create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.loiter_event_node_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.SPATIOTEMPORAL,
            confidence=Confidence.HIGH,
            tags=tags,
            sourceId=p1.source_id,
            geo=GeoInput(
                geoJson=loiter.to_geojson(),
                startTime=p2.detection_time,
                endTime=p6.detection_time
                ),
            nodeId=loiter_node_id,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=p2.detection_time,
            valueEnd=p6.detection_time
        )
    )

    # check that loiters exist in Findings table
    findings = db.execute(
        select(
            Finding
        ).filter(
            Finding.finding_type == FindingType.GEO_LOITER.value
        )
    ).scalars().all()

    assert len(findings) == 1
    assert findings[0].finding_data['processed_points'][0]['location'] == to_shape(p2.location).wkt


def test_loiter_success_multiple_in_same_geohash(mock_oms_client, db):
    """Two separate loiters in the same geohash."""
    node_id = uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # Loiter 1 Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:16:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(acm=DEFAULT_ACM, location=p6_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # West London way later
    p7 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.413890, 51.474942).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:44:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # Loiter 2 Points
    p8_point = get_random_stamford_bridge_point()
    p8 = Point(acm=DEFAULT_ACM, location=p8_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:48:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p9_point = get_random_stamford_bridge_point()
    p9 = Point(acm=DEFAULT_ACM, location=p9_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:53:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p10_point = get_random_stamford_bridge_point()
    p10 = Point(acm=DEFAULT_ACM, location=p10_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:58:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p11_point = get_random_stamford_bridge_point()
    p11 = Point(acm=DEFAULT_ACM, location=p11_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:03:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11], node_id=uuid4())

    # Set up mocks
    loiter_node_id1 = uuid4()
    loiter_node_id2 = uuid4()
    mock_oms_client.create_node.side_effect = [
        CreateNodeCreateNode.model_construct(id=loiter_node_id1, acm=p1.acm),
        CreateNodeCreateNode.model_construct(id=loiter_node_id2, acm=p1.acm)
    ]
    mock_oms_client.create_relationship.return_value = MagicMock()
    mock_oms_client.create_attribute.return_value = MagicMock()

    loiters = LoiterSensemaker(mock_oms_client).execute(track)
    assert len(loiters) == 2

    loiter1 = loiters[0]
    assert loiter1.geohash_low == "gcpug"
    assert len(loiter1.processed_points) == 5
    known_loiter_points1 = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points1, loiter1.processed_points, strict=False)
    )
    expected_linestring1 = shapely.LineString([p.coordinates for p in known_loiter_points1])
    assert loiter1.geometry.equals_exact(expected_linestring1, 1e-10)
    assert loiter1.start_time == p2.detection_time
    assert loiter1.end_time == p6.detection_time

    loiter2 = loiters[1]
    assert loiter2.geohash_low == "gcpug"
    assert len(loiter2.processed_points) == 4
    known_loiter_points2 = [p8, p9, p10, p11]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points2, loiter2.processed_points, strict=False)
    )
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points2])
    assert loiter2.geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter2.start_time == p8.detection_time
    assert loiter2.end_time == p11.detection_time

    event_name = SETTINGS.loiter_event_name + '-' + str(track.node_id)
    tags = [SETTINGS.geo_sensemaker_event_tag]

    assert mock_oms_client.create_node.call_count == 2
    mock_oms_client.create_node.assert_any_call(
        CreateNodeInput(
            acm=ROLLUP_DEFAULT_ACM,
            name=event_name,
            tier=ObjectTier.DERIVATIVE,
            tags=tags,
            classIri=SETTINGS.loiter_event_node_iri,
            ifcCodes=set(),
            isNso=True
        )
    )
    assert mock_oms_client.create_relationship.call_count == 2
    mock_oms_client.create_relationship.assert_any_call(
        CreateRelationshipInput(
            tags=tags,
            name=event_name,
            startNodeId=loiter_node_id1,
            endNodeId=track.node_id,
            confidence=Confidence.HIGH,
            acm=ROLLUP_DEFAULT_ACM,
            objectPropertyIri=SETTINGS.loiter_relationship_iri,
            sourceId=p1.source_id
        )
    )
    mock_oms_client.create_relationship.assert_any_call(
        CreateRelationshipInput(
            tags=tags,
            name=event_name,
            startNodeId=loiter_node_id2,
            endNodeId=track.node_id,
            confidence=Confidence.HIGH,
            acm=ROLLUP_DEFAULT_ACM,
            objectPropertyIri=SETTINGS.loiter_relationship_iri,
            sourceId=p1.source_id
        )
    )
    assert mock_oms_client.create_attribute.call_count == 2
    mock_oms_client.create_attribute.assert_any_call(
        CreateAttributeInput(
            attributeIri=SETTINGS.loiter_event_node_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.SPATIOTEMPORAL,
            confidence=Confidence.HIGH,
            tags=tags,
            sourceId=p1.source_id,
            geo=GeoInput(
                geoJson=loiter1.to_geojson(),
                startTime=p2.detection_time,
                endTime=p6.detection_time
                ),
            nodeId=loiter_node_id1,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=p2.detection_time,
            valueEnd=p6.detection_time
        )
    )
    mock_oms_client.create_attribute.assert_any_call(
        CreateAttributeInput(
            attributeIri=SETTINGS.loiter_event_node_attribute_iri,
            # TODO make sure these are right
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.SPATIOTEMPORAL,
            confidence=Confidence.HIGH,
            tags=tags,
            sourceId=p1.source_id,
            geo=GeoInput(
                geoJson=loiter2.to_geojson(),
                startTime=p8.detection_time,
                endTime=p11.detection_time
                ),
            nodeId=loiter_node_id2,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=p8.detection_time,
            valueEnd=p11.detection_time
        )
    )

    # check that loiters exist in Findings table
    findings = db.execute(
        select(
            Finding
        ).filter(
            Finding.finding_type == FindingType.GEO_LOITER.value
        )
    ).scalars().all()

    assert len(findings) == 2
    assert findings[0].finding_data['processed_points'][0]['location'] == to_shape(p2.location).wkt


def test_loiter_success_multiple_in_different_geohash(mock_oms_client, db):
    """Two separate loiters in different geohashes."""
    node_id = uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # Loiter 1 Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:16:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(acm=DEFAULT_ACM, location=p6_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # West London way later
    p7 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.413890, 51.474942).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:44:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    # Loiter 2 Points
    p8_point = get_random_emirates_stadium_point()
    p8 = Point(acm=DEFAULT_ACM, location=p8_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:48:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p9_point = get_random_emirates_stadium_point()
    p9 = Point(acm=DEFAULT_ACM, location=p9_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:53:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p10_point = get_random_emirates_stadium_point()
    p10 = Point(acm=DEFAULT_ACM, location=p10_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:58:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())
    p11_point = get_random_emirates_stadium_point()
    p11 = Point(acm=DEFAULT_ACM, location=p11_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:03:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11], node_id=uuid4())

    # Set up mocks
    loiter_node_id1 = uuid4()
    loiter_node_id2 = uuid4()
    mock_oms_client.create_node.side_effect = [
        CreateNodeCreateNode.model_construct(id=loiter_node_id1, acm=p1.acm),
        CreateNodeCreateNode.model_construct(id=loiter_node_id2, acm=p1.acm)
    ]
    mock_oms_client.create_relationship.return_value = MagicMock()
    mock_oms_client.create_attribute.return_value = MagicMock()

    loiters = LoiterSensemaker(mock_oms_client).execute(track)
    assert len(loiters) == 2

    loiter1: Loiter = loiters[0]
    assert loiter1.geohash_low == "gcpug"
    assert len(loiter1.processed_points) == 5
    known_loiter_points1 = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points1, loiter1.processed_points, strict=False)
    )
    expected_linestring1 = shapely.LineString([p.coordinates for p in known_loiter_points1])
    assert loiter1.geometry.equals_exact(expected_linestring1, 1e-10)
    assert loiter1.start_time == p2.detection_time
    assert loiter1.end_time == p6.detection_time

    loiter2: Loiter = loiters[1]
    assert loiter2.geohash_low == "gcpvm"
    assert len(loiter2.processed_points) == 4
    known_loiter_points2 = [p8, p9, p10, p11]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points2, loiter2.processed_points, strict=False)
    )
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points2])
    assert loiter2.geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter2.start_time == p8.detection_time
    assert loiter2.end_time == p11.detection_time

    event_name = SETTINGS.loiter_event_name + '-' + str(track.node_id)
    tags = [SETTINGS.geo_sensemaker_event_tag]

    assert mock_oms_client.create_node.call_count == 2
    mock_oms_client.create_node.assert_any_call(
        CreateNodeInput(
            acm=ROLLUP_DEFAULT_ACM,
            name=event_name,
            tier=ObjectTier.DERIVATIVE,
            tags=tags,
            classIri=SETTINGS.loiter_event_node_iri,
            ifcCodes=set(),
            isNso=True
        )
    )
    assert mock_oms_client.create_relationship.call_count == 2
    mock_oms_client.create_relationship.assert_any_call(
        CreateRelationshipInput(
            tags=tags,
            name=event_name,
            startNodeId=loiter_node_id1,
            endNodeId=track.node_id,
            confidence=Confidence.HIGH,
            acm=ROLLUP_DEFAULT_ACM,
            objectPropertyIri=SETTINGS.loiter_relationship_iri,
            sourceId=p1.source_id
        )
    )
    mock_oms_client.create_relationship.assert_any_call(
        CreateRelationshipInput(
            tags=tags,
            name=event_name,
            startNodeId=loiter_node_id2,
            endNodeId=track.node_id,
            confidence=Confidence.HIGH,
            acm=ROLLUP_DEFAULT_ACM,
            objectPropertyIri=SETTINGS.loiter_relationship_iri,
            sourceId=p1.source_id
        )
    )
    assert mock_oms_client.create_attribute.call_count == 2
    mock_oms_client.create_attribute.assert_any_call(
        CreateAttributeInput(
            attributeIri=SETTINGS.loiter_event_node_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.SPATIOTEMPORAL,
            confidence=Confidence.HIGH,
            tags=tags,
            sourceId=p1.source_id,
            geo=GeoInput(
                geoJson=loiter1.to_geojson(),
                startTime=p2.detection_time,
                endTime=p6.detection_time
                ),
            nodeId=loiter_node_id1,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=p2.detection_time,
            valueEnd=p6.detection_time
        )
    )
    mock_oms_client.create_attribute.assert_any_call(
        CreateAttributeInput(
            attributeIri=SETTINGS.loiter_event_node_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.SPATIOTEMPORAL,
            confidence=Confidence.HIGH,
            tags=tags,
            sourceId=p1.source_id,
            geo=GeoInput(
                geoJson=loiter2.to_geojson(),
                startTime=p8.detection_time,
                endTime=p11.detection_time
                ),
            nodeId=loiter_node_id2,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=p8.detection_time,
            valueEnd=p11.detection_time,
        )
    )

    # check that loiters exist in Findings table
    findings = db.execute(
        select(
            Finding
        ).filter(
            Finding.finding_type == FindingType.GEO_LOITER.value
        )
    ).scalars().all()

    assert len(findings) == 2
    assert findings[0].finding_data['processed_points'][0]['location'] == to_shape(p2.location).wkt
