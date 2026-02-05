"""Tests for co-travler sensemaker."""

from collections.abc import Generator
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from geoalchemy2.shape import to_shape
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.client import (
    CreateAttributeInput,
    CreateEventCreateEvent,
    CreateEventInput,
    CreateNodeCreateNode,
    CreateRelationshipCreateRelationship,
    CreateRelationshipInput,
    NodeNode,
)
from oms_sdk.generated.generated_graphql_client.enums import AttributeType, Confidence
from sqlalchemy import select
from sqlalchemy.orm import Session

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker
from oms_sensemaking.geospatial.sensemakers.cotravel import Cotravel, CotravelType
from oms_sensemaking.models.geo import Point, Track
from oms_sensemaking.models.sensemaking import Finding, FindingType
from tests_int.conftest import rollup_unclass_acm_3_0
from tests_int.geospatial.helper import TimeLocation

ROLLUP_DEFAULT_ACM = rollup_unclass_acm_3_0()
NODE_UUID1 = uuid4()
NODE_UUID2 = uuid4()
NODE_UUID3 = uuid4()
SOURCE_ID = uuid4()
PROVIDER_ID = uuid4()
TRACK_UUID1 = uuid4()
TRACK_UUID2 = uuid4()
TRACK_UUID3 = uuid4()
TRACK_UUID4 = uuid4()
DATA = {  # Latitude, Longitude, Altitude (m), Description, Node ID, Obs ID, detection_time, Obs confidence
    # Track 1
    TRACK_UUID1: [
        [
            51.482286,
            -0.165222,
            None,
            "London",
            NODE_UUID1,
            uuid4(),
            datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
            Confidence.HIGH,
        ],
        [
            51.466103,
            -0.210562,
            None,
            "London",
            NODE_UUID1,
            uuid4(),
            datetime.fromisoformat("2024-03-20T12:10:00-04:00"),
            Confidence.HIGH,
        ],
        [
            51.487613,
            -0.229466,
            None,
            "London",
            NODE_UUID1,
            uuid4(),
            datetime.fromisoformat("2024-03-20T12:20:00-04:00"),
            Confidence.HIGH,
        ],
        # point that shouldn't be included in the cotravel
        [
            50,
            0,
            None,
            "English Channel",
            NODE_UUID1,
            uuid4(),
            datetime.fromisoformat("2024-03-20T12:30:00-04:00"),
            Confidence.HIGH,
        ],
    ],
    # Track 2
    TRACK_UUID2: [
        [
            41.399953,
            2.217167,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:10:00-04:00"),
            Confidence.HIGH,
        ],
        [
            41.467810,
            2.289575,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:00:00-04:00"),
            Confidence.HIGH,
        ],
        [
            41.356069,
            2.183748,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:20:00-04:00"),
            Confidence.HIGH,
        ],
        [
            41.296465,
            2.130487,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:30:00-04:00"),
            Confidence.HIGH,
        ],
    ],
    # Track 3
    TRACK_UUID3: [
        [
            41.467811,
            2.289576,
            None,
            "Barcelona",
            NODE_UUID3,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:19:00-04:00"),
            Confidence.HIGH,
        ],
        [
            41.399954,
            2.217168,
            None,
            "Barcelona",
            NODE_UUID3,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:29:00-04:00"),
            Confidence.HIGH,
        ],
        [
            41.356070,
            2.183749,
            None,
            "Barcelona",
            NODE_UUID3,
            uuid4(),
            datetime.fromisoformat("2024-08-20T16:39:00-04:00"),
            Confidence.HIGH,
        ],
    ],
    # Track 4
    TRACK_UUID4: [
        [
            38.252533,
            15.650729,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-09-10T05:00:00-04:00"),
            Confidence.HIGH,
        ],
        [
            38.228556,
            15.610534,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-09-10T05:10:00-04:00"),
            Confidence.HIGH,
        ],
        [
            38.185378,
            15.594253,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-09-10T05:20:00-04:00"),
            Confidence.HIGH,
        ],
        [
            38.142175,
            15.578989,
            None,
            "Barcelona",
            NODE_UUID2,
            uuid4(),
            datetime.fromisoformat("2024-09-10T05:30:00-04:00"),
            Confidence.HIGH,
        ],
    ],
}


@pytest.fixture
def tester_db(db: Session) -> Generator[Session, Any, None]:
    for track_uuid, rows in DATA.items():
        points: list[Point] = []
        for row in rows:
            point, _ = Point.get_or_create(
                session=db,
                node_id=row[4],
                node_version=1,
                observation_id=row[5],
                observation_version=1,
                location=f"POINT({row[1]} {row[0]})",  # lng lat
                altitude=row[2],
                detection_time=row[6],
                acm=DEFAULT_ACM,
                source_id=SOURCE_ID,
                observation_confidence=row[7],
                # geohash=geohash.encode(lat=row[1], lon=row[0], precision=10)
            )
            points.append(point)
        Track.get_or_create(
            session=db,
            defaults=dict(
                points=points,
                node_id=points[0].node_id,
                algorithm="cotravel_test_track",
                acm=DEFAULT_ACM,
                provider_id=PROVIDER_ID,
            ),
            track_uuid=track_uuid,
        )

    yield db


def get_geospatial_labels(sensemaker: CotravelSensemaker):
    return [
        SETTINGS.sm_inferenced_label,
        SETTINGS.geospatial_sm_label,
        SETTINGS.cotravel_sm_label,
        sensemaker.version_string,
    ]


def test_cotravel_success(
    mock_oms_client: MagicMock, tester_db: Session, mock_oms_crud_tool: OmsCrudTool, aircraft_geo_config: dict
):
    node_id = uuid4()
    track_uuid = uuid4()

    # 10 minutes behind fixture track
    p1 = TimeLocation("POINT (-0.148931 51.484423)", "2024-03-20T12:05:00-04:00").create_node_point(node_id)
    p2 = TimeLocation("POINT (-0.186849 51.465229)", "2024-03-20T12:15:00-04:00").create_node_point(node_id)
    p3 = TimeLocation("POINT (-0.225258 51.476589)", "2024-03-20T12:25:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3],
        node_id=node_id,
        algorithm="test_algorithm",
        track_uuid=track_uuid,
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    # Set up mocks
    cotravel_event_id = uuid4()
    mock_oms_client.create_event = MagicMock(
        return_value=CreateEventCreateEvent.model_construct(id=cotravel_event_id, acm=ROLLUP_DEFAULT_ACM)
    )
    mock_oms_client.create_attribute.return_value = MagicMock()

    sensemaker = CotravelSensemaker(mock_oms_crud_tool)
    cotravels: list[Cotravel] = sensemaker.execute(track, aircraft_geo_config)

    assert len(cotravels) == 1
    cotravel = cotravels[0]
    assert cotravel.cotravel_type == CotravelType.cotravel
    assert cotravel.track1.node_id == track.node_id
    assert cotravel.start_time == datetime.fromisoformat("2024-03-20T12:00:00-04:00")
    assert cotravel.last_time == p3.detection_time

    tags = [SETTINGS.geo_sensemaker_event_tag]

    mock_oms_client.create_event.assert_called_with(
        CreateEventInput(
            acm=ROLLUP_DEFAULT_ACM,
            tags=tags,
            labels=get_geospatial_labels(sensemaker),
            classIri=SETTINGS.cotravel_event_iri,
            name=SETTINGS.cotravel_event_name,
            nodeIds=[cotravel.track1.node_id, cotravel.track2.node_id],
            geometry=cotravel.to_geojson(),
            sourceId=p1.source_id,
            startTime=cotravel.start_time,
            endTime=cotravel.last_time,
        )
    )

    mock_oms_client.create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.cotravel_event_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=Confidence.HIGH,
            tags=tags,
            labels=get_geospatial_labels(sensemaker),
            sourceId=p1.source_id,
            geometry=cotravel.to_geojson(),
            eventId=cotravel_event_id,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=cotravel.start_time,
            valueEnd=cotravel.last_time,
        )
    )

    # check that cotravels exist in Findings table
    findings = (
        tester_db.execute(select(Finding).filter(Finding.finding_type == FindingType.GEO_COTRAVEL.value))
        .scalars()
        .all()
    )

    assert len(findings) == 1
    assert findings[0].finding_data["track1"]["points"][0]["location"] == to_shape(p1.location).wkt
    assert findings[0].algorithm_configuration


def make_potential_duplicate_track() -> Track:
    node_id = uuid4()
    track_id = uuid4()

    # <30 seconds behind fixture track
    p1 = TimeLocation("POINT (-0.148931 51.484423)", "2024-03-20T12:00:27-04:00").create_node_point(node_id)
    p2 = TimeLocation("POINT (-0.186849 51.465229)", "2024-03-20T12:10:28-04:00").create_node_point(node_id)
    p3 = TimeLocation("POINT (-0.225258 51.476589)", "2024-03-20T12:20:29-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3],
        node_id=node_id,
        algorithm="test_algorithm",
        track_uuid=track_id,
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    return track


def test_potential_duplicate_success(
    mock_oms_client: MagicMock,
    tester_db: Session,
    db: Session,
    mock_oms_crud_tool: OmsCrudTool,
    aircraft_geo_config: dict,
):
    track = make_potential_duplicate_track()
    node_id = track.node_id
    p1 = track.points[0]
    p3 = track.points[2]

    # Set up mocks
    cotravel_node_id = uuid4()
    mock_oms_client.create_node = MagicMock(
        return_value=CreateNodeCreateNode.model_construct(id=cotravel_node_id, acm=ROLLUP_DEFAULT_ACM, isNso=True)
    )
    mock_oms_client.create_relationship.return_value = MagicMock()
    mock_oms_client.create_attribute.return_value = MagicMock()
    mock_oms_client.create_relationship.return_value = CreateRelationshipCreateRelationship.model_construct(id=uuid4())

    sensemaker = CotravelSensemaker(mock_oms_crud_tool)
    cotravels: list[Cotravel] = sensemaker.execute(track, aircraft_geo_config)

    assert len(cotravels) == 1
    cotravel = cotravels[0]
    assert cotravel.cotravel_type == CotravelType.potential_duplicate
    assert cotravel.track1.node_id == track.node_id
    assert cotravel.start_time == datetime.fromisoformat("2024-03-20T12:00:00-04:00")
    assert cotravel.last_time == p3.detection_time

    mock_oms_client.create_relationship.assert_called_with(
        CreateRelationshipInput(
            tags=[SETTINGS.geo_sensemaker_event_tag],
            labels=get_geospatial_labels(sensemaker),
            name=SETTINGS.potential_duplicate_relationship_name,
            startNodeId=node_id,
            endNodeId=NODE_UUID1,
            confidence=Confidence.HIGH,
            acm=ROLLUP_DEFAULT_ACM,
            objectPropertyIri=SETTINGS.resolution_relationship_iri,
            sourceId=p1.source_id,
        )
    )

    # check that cotravels exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.COTRAVEL_POTENTIAL_DUPLICATE.value))
        .scalars()
        .all()
    )

    assert len(findings) == 1
    assert findings[0].finding_data["track1"]["points"][0]["location"] == to_shape(p1.location).wkt
    assert findings[0].algorithm_configuration


def test_potential_duplicate_with_nso(
    mock_oms_client: MagicMock,
    tester_db: Session,
    db: Session,
    mock_oms_crud_tool: OmsCrudTool,
    aircraft_geo_config: dict,
):
    track = make_potential_duplicate_track()

    # Test isNSO True should return duplicate
    # Set up mocks
    cotravel_node_id = uuid4()
    mock_oms_client.create_node = MagicMock(
        return_value=CreateNodeCreateNode.model_construct(id=cotravel_node_id, acm=ROLLUP_DEFAULT_ACM)
    )

    mock_oms_client.node.return_value = NodeNode.model_construct(
        id=cotravel_node_id, acm=ROLLUP_DEFAULT_ACM, isNso=True
    )
    mock_oms_client.create_relationship.return_value = MagicMock()
    mock_oms_client.create_attribute.return_value = MagicMock()
    mock_oms_client.create_relationship.return_value = CreateRelationshipCreateRelationship.model_construct(id=uuid4())

    cotravels: list[Cotravel] = CotravelSensemaker(mock_oms_crud_tool).execute(track, aircraft_geo_config)

    assert len(cotravels) == 1
    cotravel = cotravels[0]
    assert cotravel.cotravel_type == CotravelType.potential_duplicate


def test_potential_duplicate_with_known_node(
    mock_oms_client: MagicMock,
    tester_db: Session,
    db: Session,
    mock_oms_crud_tool: OmsCrudTool,
    aircraft_geo_config: dict,
):
    track = make_potential_duplicate_track()

    # Test isNSO False should return cotravel
    # Set up mocks
    cotravel_event_id = uuid4()
    mock_oms_client.create_event = MagicMock(
        return_value=CreateEventCreateEvent.model_construct(id=cotravel_event_id, acm=ROLLUP_DEFAULT_ACM)
    )
    mock_oms_client.node.return_value = NodeNode.model_construct(id=uuid4(), acm=ROLLUP_DEFAULT_ACM, isNso=False)
    mock_oms_client.create_attribute.return_value = MagicMock()

    cotravels: list[Cotravel] = CotravelSensemaker(mock_oms_crud_tool).execute(track, aircraft_geo_config)

    assert len(cotravels) == 1
    cotravel = cotravels[0]
    print("mock: ", mock_oms_client)
    assert cotravel.cotravel_type == CotravelType.cotravel


def test_potential_duplicate_failure(
    mock_oms_client: MagicMock,
    tester_db: Session,
    db: Session,
    mock_oms_crud_tool: OmsCrudTool,
    aircraft_geo_config: dict,
):
    node_id = uuid4()
    track_id = uuid4()

    # average time behind is >30s
    p1 = TimeLocation("POINT (-0.148931 51.484423)", "2024-03-20T12:00:30-04:00").create_node_point(node_id)
    p2 = TimeLocation("POINT (-0.186849 51.465229)", "2024-03-20T12:10:30-04:00").create_node_point(node_id)
    p3 = TimeLocation("POINT (-0.225258 51.476589)", "2024-03-20T12:20:31-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3],
        node_id=node_id,
        algorithm="test_algorithm",
        track_uuid=track_id,
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    # Set up mocks
    cotravel_event = uuid4()
    mock_oms_client.create_event = MagicMock(
        return_value=CreateEventCreateEvent.model_construct(id=cotravel_event, acm=ROLLUP_DEFAULT_ACM)
    )
    mock_oms_client.create_attribute.return_value = MagicMock()

    cotravels: list[Cotravel] = CotravelSensemaker(mock_oms_crud_tool).execute(track, aircraft_geo_config)

    assert len(cotravels) == 1
    cotravel = cotravels[0]
    assert cotravel.cotravel_type == CotravelType.cotravel

    # check that cotravels exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.GEO_COTRAVEL.value)).scalars().all()
    )

    assert len(findings) == 1


def test_multiple_cotravel_success(
    mock_oms_client: MagicMock, tester_db: Session, mock_oms_crud_tool: OmsCrudTool, aircraft_geo_config: dict
):
    node_id = uuid4()
    track_uuid = uuid4()

    # 10 minutes behind fixture track
    p1 = TimeLocation("POINT (2.289577 41.467812)", "2024-08-20T16:39:00-04:00").create_node_point(node_id)
    p2 = TimeLocation("POINT (2.217169 41.399955)", "2024-08-20T16:49:00-04:00").create_node_point(node_id)
    p3 = TimeLocation("POINT (2.183750 41.356071)", "2024-08-20T16:59:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3],
        node_id=node_id,
        algorithm="test_algorithm",
        track_uuid=track_uuid,
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    # Set up mocks
    cotravel_event_id = uuid4()
    mock_oms_client.create_event.side_effect = [
        CreateEventCreateEvent.model_construct(id=cotravel_event_id, acm=ROLLUP_DEFAULT_ACM),
        CreateEventCreateEvent.model_construct(id=cotravel_event_id, acm=ROLLUP_DEFAULT_ACM),
    ]
    mock_oms_client.create_attribute.return_value = MagicMock()

    sensemaker = CotravelSensemaker(mock_oms_crud_tool)
    cotravels: list[Cotravel] = sensemaker.execute(track, aircraft_geo_config)

    assert len(cotravels) == 2
    cotravels = sorted(cotravels, key=lambda cotravel: cotravel.cotravel_type.value)  # check lag_lead first

    cotravel: Cotravel = cotravels[0]
    assert cotravel.cotravel_type == CotravelType.cotravel
    assert cotravel.track1.node_id == track.node_id
    assert cotravel.start_time == datetime.fromisoformat("2024-08-20T16:19:00-04:00")
    assert cotravel.last_time == p3.detection_time

    lag_lead: Cotravel = cotravels[1]
    assert lag_lead.cotravel_type == CotravelType.lag_lead
    assert lag_lead.track1.node_id == track.node_id
    assert lag_lead.start_time == datetime.fromisoformat("2024-08-20T16:00:00-04:00")
    assert lag_lead.last_time == p3.detection_time

    tags = [SETTINGS.geo_sensemaker_event_tag]

    assert mock_oms_client.create_event.call_count == 2
    mock_oms_client.create_event.assert_any_call(
        CreateEventInput(
            acm=ROLLUP_DEFAULT_ACM,
            tags=tags,
            labels=get_geospatial_labels(sensemaker),
            classIri=SETTINGS.cotravel_event_iri,
            name=SETTINGS.lag_lead_event_name,
            nodeIds=[lag_lead.track1.node_id, lag_lead.track2.node_id],
            geometry=lag_lead.to_geojson(),
            sourceId=p1.source_id,
            startTime=lag_lead.start_time,
            endTime=lag_lead.last_time,
        )
    )
    mock_oms_client.create_event.assert_any_call(
        CreateEventInput(
            acm=ROLLUP_DEFAULT_ACM,
            tags=tags,
            labels=get_geospatial_labels(sensemaker),
            classIri=SETTINGS.cotravel_event_iri,
            name=SETTINGS.cotravel_event_name,
            nodeIds=[cotravel.track1.node_id, cotravel.track2.node_id],
            geometry=cotravel.to_geojson(),
            sourceId=p1.source_id,
            startTime=cotravel.start_time,
            endTime=cotravel.last_time,
        )
    )

    assert mock_oms_client.create_attribute.call_count == 2
    mock_oms_client.create_attribute.assert_any_call(
        CreateAttributeInput(
            attributeIri=SETTINGS.cotravel_event_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=Confidence.HIGH,
            tags=tags,
            labels=get_geospatial_labels(sensemaker),
            sourceId=p1.source_id,
            geometry=lag_lead.to_geojson(),
            eventId=cotravel_event_id,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=lag_lead.start_time,
            valueEnd=lag_lead.last_time,
        )
    )
    mock_oms_client.create_attribute.assert_any_call(
        CreateAttributeInput(
            attributeIri=SETTINGS.cotravel_event_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=Confidence.HIGH,
            tags=tags,
            labels=get_geospatial_labels(sensemaker),
            sourceId=p1.source_id,
            geometry=cotravel.to_geojson(),
            eventId=cotravel_event_id,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=cotravel.start_time,
            valueEnd=cotravel.last_time,
        )
    )

    # check that cotravels exist in Findings table
    findings = (
        tester_db.execute(select(Finding).filter(Finding.finding_type == FindingType.GEO_COTRAVEL.value))
        .scalars()
        .all()
    )

    assert len(findings) == 2
    assert findings[0].finding_data["track1"]["points"][0]["location"] == to_shape(p1.location).wkt
    assert findings[0].algorithm_configuration


def test_lag_lead_success(
    mock_oms_client: MagicMock, tester_db: Session, mock_oms_crud_tool: OmsCrudTool, aircraft_geo_config: dict
):
    node_id = uuid4()
    track_uuid = uuid4()

    # 35 minutes behind fixture track
    p1 = TimeLocation("POINT (-0.148931 51.484423)", "2024-03-20T12:35:00-04:00").create_node_point(node_id)
    p2 = TimeLocation("POINT (-0.186849 51.465229)", "2024-03-20T12:45:00-04:00").create_node_point(node_id)
    p3 = TimeLocation("POINT (-0.225258 51.476589)", "2024-03-20T12:55:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3],
        node_id=node_id,
        algorithm="test_algorithm",
        track_uuid=track_uuid,
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    # Set up mocks
    cotravel_event_id = uuid4()
    mock_oms_client.create_event.return_value = CreateEventCreateEvent.model_construct(
        id=cotravel_event_id, acm=ROLLUP_DEFAULT_ACM
    )
    mock_oms_client.create_attribute.return_value = MagicMock()

    sensemaker = CotravelSensemaker(mock_oms_crud_tool)
    cotravels: list[Cotravel] = sensemaker.execute(track, aircraft_geo_config)

    assert len(cotravels) == 1
    cotravel: Cotravel = cotravels[0]
    assert cotravel.cotravel_type == CotravelType.lag_lead
    assert cotravel.track1.node_id == track.node_id
    assert cotravel.start_time == datetime.fromisoformat("2024-03-20T12:00:00-04:00")
    assert cotravel.last_time == p3.detection_time

    tags = [SETTINGS.geo_sensemaker_event_tag]

    mock_oms_client.create_event.assert_called_with(
        CreateEventInput(
            acm=ROLLUP_DEFAULT_ACM,
            tags=tags,
            labels=get_geospatial_labels(sensemaker),
            classIri=SETTINGS.cotravel_event_iri,
            name=SETTINGS.lag_lead_event_name,
            nodeIds=[cotravel.track1.node_id, cotravel.track2.node_id],
            geometry=cotravel.to_geojson(),
            sourceId=p1.source_id,
            startTime=cotravel.start_time,
            endTime=cotravel.last_time,
        )
    )

    mock_oms_client.create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.cotravel_event_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=Confidence.HIGH,
            tags=tags,
            labels=get_geospatial_labels(sensemaker),
            sourceId=p1.source_id,
            geometry=cotravel.to_geojson(),
            eventId=cotravel_event_id,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=cotravel.start_time,
            valueEnd=cotravel.last_time,
        )
    )

    # check that cotravels exist in Findings table
    findings = (
        tester_db.execute(select(Finding).filter(Finding.finding_type == FindingType.GEO_COTRAVEL.value))
        .scalars()
        .all()
    )

    assert len(findings) == 1
    assert findings[0].finding_data["track1"]["points"][0]["location"] == to_shape(p1.location).wkt
    assert findings[0].algorithm_configuration


def test_cotravel_too_far_behind(tester_db: Session, mock_oms_crud_tool: OmsCrudTool, aircraft_geo_config: dict):
    node_id = uuid4()
    track_uuid = uuid4()

    # 95 minutes behind fixture track
    p1 = TimeLocation("POINT (-0.148931 51.484423)", "2024-03-20T13:35:00-04:00").create_node_point(node_id)
    p2 = TimeLocation("POINT (-0.186849 51.465229)", "2024-03-20T13:45:00-04:00").create_node_point(node_id)
    p3 = TimeLocation("POINT (-0.225258 51.476589)", "2024-03-20T13:55:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3],
        node_id=node_id,
        algorithm="test_algorithm",
        track_uuid=track_uuid,
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    cotravels: list[Cotravel] = CotravelSensemaker(mock_oms_crud_tool).execute(track, aircraft_geo_config)

    assert len(cotravels) == 0


def test_cotravel_valid_before_observation_threshold_exceeded(
    mock_oms_client: MagicMock,
    tester_db: Session,
    db: Session,
    mock_oms_crud_tool: OmsCrudTool,
    aircraft_geo_config: dict,
):
    node_id = uuid4()
    track_uuid = uuid4()

    # 10 minutes behind fixture track
    p1 = TimeLocation("POINT (15.650729 38.252533)", "2024-09-10T05:10:00-04:00").create_node_point(node_id)
    p2 = TimeLocation("POINT (15.610534 38.228556)", "2024-09-10T05:20:00-04:00").create_node_point(node_id)
    p3 = TimeLocation("POINT (15.594253 38.185378)", "2024-09-10T05:30:00-04:00").create_node_point(node_id)
    # past observational threshold so shouldn't be added
    p4 = TimeLocation("POINT (15.578989 38.142175)", "2024-09-10T05:46:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3, p4],
        node_id=node_id,
        algorithm="test_algorithm",
        track_uuid=track_uuid,
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    # Set up mocks
    cotravel_event_id = uuid4()
    mock_oms_client.create_event = MagicMock(
        return_value=CreateEventCreateEvent.model_construct(id=cotravel_event_id, acm=ROLLUP_DEFAULT_ACM, isNso=False)
    )
    mock_oms_client.create_attribute.return_value = MagicMock()

    sensemaker = CotravelSensemaker(mock_oms_crud_tool)
    cotravels: list[Cotravel] = sensemaker.execute(track, aircraft_geo_config)

    assert len(cotravels) == 1
    cotravel: Cotravel = cotravels[0]
    assert cotravel.cotravel_type == CotravelType.cotravel
    assert cotravel.track1.node_id == track.node_id
    assert cotravel.start_time == datetime.fromisoformat("2024-09-10T05:00:00-04:00")
    assert cotravel.last_time == p3.detection_time

    tags = [SETTINGS.geo_sensemaker_event_tag]

    mock_oms_client.create_event.assert_called_with(
        CreateEventInput(
            acm=ROLLUP_DEFAULT_ACM,
            tags=tags,
            labels=get_geospatial_labels(sensemaker),
            classIri=SETTINGS.cotravel_event_iri,
            name=SETTINGS.cotravel_event_name,
            nodeIds=[cotravel.track1.node_id, cotravel.track2.node_id],
            geometry=cotravel.to_geojson(),
            sourceId=p1.source_id,
            startTime=cotravel.start_time,
            endTime=cotravel.last_time,
        )
    )

    mock_oms_client.create_attribute.assert_called_with(
        CreateAttributeInput(
            attributeIri=SETTINGS.cotravel_event_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=Confidence.HIGH,
            tags=tags,
            labels=get_geospatial_labels(sensemaker),
            sourceId=p1.source_id,
            geometry=cotravel.to_geojson(),
            eventId=cotravel_event_id,
            acm=ROLLUP_DEFAULT_ACM,
            valueStart=cotravel.start_time,
            valueEnd=cotravel.last_time,
        )
    )

    # check that cotravels exist in Findings table
    findings = (
        db.execute(select(Finding).filter(Finding.finding_type == FindingType.GEO_COTRAVEL.value)).scalars().all()
    )

    assert len(findings) == 1
    assert findings[0].finding_data["track1"]["points"][0]["location"] == to_shape(p1.location).wkt
    assert findings[0].algorithm_configuration
