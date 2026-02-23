"""Tests for geo ORM models."""

from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pygeohash as pgh
import pytest
import shapely
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import Confidence
from sqlalchemy import func, select
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session

from oms_sensemaking.models.geo import Point, Track, get_track
from tests_int.geospatial.test_int_similar_tracks import ROLLUP_DEFAULT_ACM

ATTR_ID_FFX: UUID = UUID("f604f7d3-b78d-49af-a2cf-75eae08cec52")
NODE_ID_FFX: UUID = UUID("6796b293-e0b2-4ba3-a361-c59c6e07248b")
NODE_ID: UUID = UUID("0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8")
SOURCE_ID: UUID = uuid4()
TRACK_UUID: UUID = UUID("5f2fa1af-a602-4411-8b76-3a9b1f70ae1d")
TRACK_UUID_FFX: UUID = UUID("f96437e0-bb67-4f59-8b0c-61a01cc5b870")

DATA = {  # Latitude, Longitude, Altitude (m), Description, Node ID, Obs ID, detection_time, Obs confidence
    # Track 1
    TRACK_UUID: [
        [34.052235, -118.243683, 100, "Central Los Angeles, downtown area", NODE_ID, uuid4(), Confidence.HIGH],
        [34.052500, -118.245000, 150, "Near Los Angeles State Historic Park", NODE_ID, uuid4(), Confidence.HIGH],
        [34.053000, -118.247000, 120, "Close to Chinatown", NODE_ID, uuid4(), Confidence.HIGH],
        [34.054000, -118.249000, 180, "Elysian Park entrance", NODE_ID, uuid4(), Confidence.HIGH],
        [34.055000, -118.251000, 200, "Elysian Park trailhead", NODE_ID, uuid4(), Confidence.HIGH],
        [34.056000, -118.253000, 250, "Midpoint of trail, higher elevation", NODE_ID, uuid4(), Confidence.HIGH],
        [34.057000, -118.255000, 230, "Near Dodger Stadium", NODE_ID, uuid4(), Confidence.HIGH],
        [34.058000, -118.257000, 190, "Downhill from Dodger Stadium", NODE_ID, uuid4(), Confidence.HIGH],
        [34.059000, -118.259000, 160, "Park exit", NODE_ID, uuid4(), Confidence.HIGH],
        [34.060000, -118.261000, 140, "Residential area", NODE_ID, uuid4(), Confidence.HIGH],
        [34.061000, -118.263000, 110, "End of the route, nearby school", NODE_ID, uuid4(), Confidence.HIGH],
        [34.062000, -118.265000, 90, "Final point, local marketplace", NODE_ID, uuid4(), Confidence.HIGH],
    ],
    TRACK_UUID_FFX: [
        [38.846224, -77.306373, None, "Fairfax, VA", NODE_ID_FFX, ATTR_ID_FFX, Confidence.HIGH],
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
                detection_time=datetime.now(tz=timezone.utc),
                acm=DEFAULT_ACM,
                source_id=SOURCE_ID,
                observation_confidence=row[6],
            )
            points.append(point)
        Track.get_or_create(
            session=db,
            defaults=dict(
                points=points,
                node_id=points[0].node_id,
                algorithm="geo_test_track",
                acm=DEFAULT_ACM,
            ),
            track_uuid=track_uuid,
        )

    yield db


def test_points_2d_and_3d(tester_db: Session):
    count: int = tester_db.scalar(select(func.count()).select_from(Point))

    # ensure all data made it into the database
    assert count == sum(len(points) for points in DATA.values())

    # get the first record from the db
    point = tester_db.execute(select(Point)).scalars().first()
    assert point

    for coords in [point.coordinates, point.to_geojson()["geometry"]["coordinates"]]:
        # validate coordinates
        assert len(coords) == 3
        assert coords[0] == DATA[TRACK_UUID][0][1]
        assert coords[1] == DATA[TRACK_UUID][0][0]
        assert coords[2] == DATA[TRACK_UUID][0][2]

    # check to_dict
    assert point.location == point.to_dict()["location"]
    assert point.location == point.to_dict()["location"]
    assert "coordinates" not in point.to_dict()

    point = (
        tester_db.execute(
            select(Point)
            .where(Point.altitude.is_(None))
            .where(Point.node_id == NODE_ID_FFX, Point.observation_id == ATTR_ID_FFX)
        )
        .scalars()
        .one()
    )

    assert point
    coords: list[float] = point.coordinates
    assert len(coords) == 2
    assert point.coordinates[0] == DATA[TRACK_UUID_FFX][0][1]
    assert point.coordinates[1] == DATA[TRACK_UUID_FFX][0][0]


def test_get_or_create_existing_record(tester_db: Session):
    # get a specific point
    point: Point = (
        tester_db.execute(
            select(Point)
            .where(Point.altitude.is_(None))
            .where(Point.node_id == NODE_ID_FFX, Point.observation_id == ATTR_ID_FFX)
        )
        .scalars()
        .one()
    )

    assert point
    coords: list[float] = point.coordinates
    assert len(coords) == 2
    assert point.coordinates[0] == DATA[TRACK_UUID_FFX][0][1]
    assert point.coordinates[1] == DATA[TRACK_UUID_FFX][0][0]

    point2, is_new = Point.get_or_create(tester_db, node_id=NODE_ID_FFX, observation_id=ATTR_ID_FFX)
    assert point2
    assert not is_new
    assert point == point2


def test_get_or_create_new_record(tester_db: Session):
    point, is_new = Point.get_or_create(
        tester_db,
        defaults=dict(
            node_id=NODE_ID_FFX,
            node_version=1,
            observation_version=1,
            observation_confidence=Confidence.HIGH,
            location="POINT(-77.306373 38.846224)",  # lng lat
            altitude=None,
            detection_time=datetime.now(timezone.utc),
            acm=DEFAULT_ACM,
            source_id=SOURCE_ID,
        ),
        node_id=NODE_ID_FFX,
        observation_id=uuid4(),
    )

    assert point
    assert is_new


def test_point_updated_at_no_timezone(tester_db: Session):
    point, is_new = Point.get_or_create(
        tester_db,
        defaults=dict(
            node_id=NODE_ID_FFX,
            node_version=1,
            observation_version=1,
            observation_confidence=Confidence.HIGH,
            location="POINT(-77.306373 38.846224)",  # lng lat
            altitude=None,
            detection_time=datetime.now(tz=timezone.utc),
            acm=DEFAULT_ACM,
            source_id=SOURCE_ID,
        ),
        node_id=NODE_ID_FFX,
        observation_id=uuid4(),
    )

    tester_db.refresh(point)

    point.updated_at = datetime.now()
    tester_db.add(point)

    with pytest.raises(StatementError):
        tester_db.commit()


def test_geohash(tester_db: Session):
    point = (
        tester_db.execute(  # fairfax query
            select(Point)
            .where(Point.altitude.is_(None))
            .where(Point.node_id == NODE_ID_FFX, Point.observation_id == ATTR_ID_FFX)
        )
        .scalars()
        .one()
    )

    assert point
    assert point.geohash == pgh.encode(38.846224, -77.306373, 12)


def test_geohash_nearby_query(tester_db: Session):
    point1_node_id: UUID = uuid4()
    point1_attr_id: UUID = uuid4()
    point1, is_new = Point.get_or_create(
        tester_db,
        defaults=dict(
            node_version=1,
            observation_version=1,
            observation_confidence=Confidence.HIGH,
            location="POINT(-73.8456 40.7246)",
            altitude=None,
            detection_time=datetime.now(timezone.utc),
            acm=DEFAULT_ACM,
            source_id=SOURCE_ID,
        ),
        node_id=point1_node_id,
        observation_id=point1_attr_id,
    )
    point2_node_id: UUID = uuid4()
    point2_attr_id: UUID = uuid4()
    point2, is_new = Point.get_or_create(
        session=tester_db,
        defaults=dict(
            node_version=1,
            observation_version=1,
            observation_confidence=Confidence.HIGH,
            location="POINT(-73.8456 40.7246)",
            altitude=None,
            detection_time=datetime.now(timezone.utc),
            acm=DEFAULT_ACM,
            source_id=SOURCE_ID,
        ),
        node_id=point2_node_id,
        observation_id=point2_attr_id,
    )
    point3, is_new = Point.get_or_create(
        tester_db,
        defaults=dict(
            node_version=1,
            observation_version=1,
            observation_confidence=Confidence.HIGH,
            location="POINT(-77.306373 38.846224)",  # lng lat
            altitude=None,
            detection_time=datetime.now(tz=timezone.utc),
            acm=DEFAULT_ACM,
            source_id=SOURCE_ID,
        ),
        node_id=NODE_ID_FFX,
        observation_id=ATTR_ID_FFX,
    )

    nearby_points = (
        tester_db.execute(
            select(Point)
            .filter(
                Point.geohash.like("dr5rxtembz9t%")  # full value should be dr5rxtembz9tw6b30s9w
            )
            .order_by(Point.detection_time.asc())
        )
        .scalars()
        .all()
    )

    assert len(nearby_points) == 2


def test_get_points_track(tester_db: Session):
    points = get_track(tester_db, TRACK_UUID).points

    assert len(points) == 12
    assert points[0].detection_time < points[-1].detection_time
    assert points[0].geohash is not None


def test_get_track(tester_db: Session):
    track: Track = get_track(tester_db, TRACK_UUID)

    assert track
    assert len(track.points) == 12
    assert track.points[0].node_id == NODE_ID
    assert track.points[0].observation_id == DATA[TRACK_UUID][0][5]
    assert track.points[0].coordinates[0] == DATA[TRACK_UUID][0][1]
    assert track.points[0].coordinates[1] == DATA[TRACK_UUID][0][0]


def test_get_track_uuid_str(tester_db: Session):
    track: Track = get_track(tester_db, UUID("5f2fa1af-a602-4411-8b76-3a9b1f70ae1d"))

    assert track
    assert len(track.points) == 12
    assert track.points[0].node_id == NODE_ID
    assert track.points[0].observation_id == DATA[TRACK_UUID][0][5]


def test_geometry_crosses_antimeridian_same_lat(tester_db: Session):
    """Test that to_geoemtry splits input into MultiLineString"""
    node_id = uuid4()
    track_uuid = uuid4()
    p1 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(178, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p2 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(179, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p3 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-179, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:25:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    # Create Track Object
    track = Track(
        points=[p1, p2, p3],
        node_id=node_id,
        track_uuid=track_uuid,
        algorithm="test_track",
        acm=ROLLUP_DEFAULT_ACM,
    )
    geometry = track.to_geometry()
    # assert geometry["type"] == "MultiLineString"
    expected = {
        "coordinates": [[[178.0, 22.6683], [179.0, 22.6683], [180.0, 22.6683]], [[-180.0, 22.6683], [-179.0, 22.6683]]],
        "type": "MultiLineString",
    }
    assert geometry == expected


def test_geometry_crosses_antimeridian_diff_lat(tester_db: Session):
    """Test that to_geoemtry splits input into MultiLineString"""
    node_id = uuid4()
    track_uuid = uuid4()
    p1 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(178, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p2 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(179, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p3 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-179, 24.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:25:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    # Create Track Object
    track = Track(
        points=[p1, p2, p3],
        node_id=node_id,
        track_uuid=track_uuid,
        algorithm="test_track",
        acm=ROLLUP_DEFAULT_ACM,
    )
    geometry = track.to_geometry()
    # assert geometry["type"] == "MultiLineString"
    expected = {
        "coordinates": [[[178.0, 22.6683], [179.0, 22.6683], [180.0, 23.6683]], [[-180.0, 23.6683], [-179.0, 24.6683]]],
        "type": "MultiLineString",
    }
    assert geometry == expected


def test_geometry_crosses_antimeridian_other_direction(tester_db: Session):
    """Test that to_geoemtry splits input into MultiLineString"""
    node_id = uuid4()
    track_uuid = uuid4()
    p1 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-178, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p2 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-179, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p3 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(179, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:25:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    # Create Track Object
    track = Track(
        points=[p1, p2, p3],
        node_id=node_id,
        track_uuid=track_uuid,
        algorithm="test_track",
        acm=ROLLUP_DEFAULT_ACM,
    )
    geometry = track.to_geometry()
    # assert geometry["type"] == "MultiLineString"
    expected = {
        "coordinates": [
            [[-178.0, 22.6683], [-179.0, 22.6683], [-180.0, 22.6683]],
            [[180.0, 22.6683], [179.0, 22.6683]],
        ],
        "type": "MultiLineString",
    }
    assert geometry == expected


def test_geometry_not_crosses_antimeridian(tester_db: Session):
    """Test that to_geoemtry keeps input as LineString"""
    node_id = uuid4()
    track_uuid = uuid4()
    p1 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(178, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p2 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(179, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p3 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(180, 22.6683).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:25:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    # Create Track Object
    track = Track(
        points=[p1, p2, p3],
        node_id=node_id,
        track_uuid=track_uuid,
        algorithm="test_track",
        acm=ROLLUP_DEFAULT_ACM,
    )
    geometry = track.to_geometry()
    # assert geometry["type"] == "MultiLineString"
    expected = {"coordinates": [[178.0, 22.6683], [179.0, 22.6683], [180.0, 22.6683]], "type": "LineString"}
    assert geometry == expected


def test_geometry_crosses_antimeridian_three_intersections(tester_db: Session):
    """Test that to_geometry splits input into MultiLineString"""
    node_id = uuid4()
    track_uuid = uuid4()
    p1 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-178, 22).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p2 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(178, 22).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p3 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(176, 20).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:25:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )
    p4 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-176, 20).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:35:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p5 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-174, 18).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:45:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    p6 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(174, 18).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:55:00-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=uuid4(),
        observation_version=1,
        source_id=uuid4(),
        observation_confidence=Confidence.HIGH,
    )

    # Create Track Object
    points = [p1, p2, p3, p4, p5, p6]
    track = Track(
        points=points,
        node_id=node_id,
        track_uuid=track_uuid,
        algorithm="test_track",
        acm=ROLLUP_DEFAULT_ACM,
    )
    geometry = track.to_geometry()
    # assert geometry["type"] == "MultiLineString"
    expected = {
        "coordinates": [
            [[-178.0, 22], [-180.0, 22]],
            [[180.0, 22], [178.0, 22], [176, 20], [180, 20]],
            [[-180, 20], [-176.0, 20], [-174, 18], [-180, 18]],
            [[180, 18], [174, 18]],
        ],
        "type": "MultiLineString",
    }
    assert geometry == expected
