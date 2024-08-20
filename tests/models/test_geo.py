"""Tests for geo ORM models."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pygeohash as pgh
import pytest
from oms_sdk import DEFAULT_ACM
from oms_sensemaking.models.geo import Point, Track, get_track_points, get_track
from sqlalchemy import func, select
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session

ATTR_ID_FFX: UUID = UUID("f604f7d3-b78d-49af-a2cf-75eae08cec52")
NODE_ID_FFX: UUID = UUID("6796b293-e0b2-4ba3-a361-c59c6e07248b")
NODE_ID: UUID = UUID("0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8")

DATA: list = [  # Latitude, Longitude, Altitude (m), Description, Node ID, Attr ID
    [34.052235, -118.243683, 100, "Central Los Angeles, downtown area", NODE_ID, uuid4()],
    [34.052500, -118.245000, 150, "Near Los Angeles State Historic Park", NODE_ID, uuid4()],
    [34.053000, -118.247000, 120, "Close to Chinatown", NODE_ID, uuid4()],
    [34.054000, -118.249000, 180, "Elysian Park entrance", NODE_ID, uuid4()],
    [34.055000, -118.251000, 200, "Elysian Park trailhead", NODE_ID, uuid4()],
    [34.056000, -118.253000, 250, "Midpoint of trail, higher elevation", NODE_ID, uuid4()],
    [34.057000, -118.255000, 230, "Near Dodger Stadium", NODE_ID, uuid4()],
    [34.058000, -118.257000, 190, "Downhill from Dodger Stadium", NODE_ID, uuid4()],
    [34.059000, -118.259000, 160, "Park exit", NODE_ID, uuid4()],
    [34.060000, -118.261000, 140, "Residential area", NODE_ID, uuid4()],
    [34.061000, -118.263000, 110, "End of the route, nearby school", NODE_ID, uuid4()],
    [34.062000, -118.265000, 90, "Final point, local marketplace", NODE_ID, uuid4()],
    [38.846224, -77.306373, None, "Fairfax, VA", NODE_ID_FFX, ATTR_ID_FFX]
]


def load_sample_data(db: Session):
    for row in DATA:
        point: Point = Point(
            node_id=row[4],
            node_version=1,
            attribute_id=row[5],
            attribute_version=1,
            location=f"POINT({row[1]} {row[0]})",  # lng lat
            altitude=row[2],
            geohash=pgh.encode(row[0], row[1]),
            detection_time=datetime.now(tz=timezone.utc),
            acm=DEFAULT_ACM
        )

        db.add(point)

    db.commit()


def test_points_2d_and_3d(db: Session):
    load_sample_data(db)

    count: int = db.scalar(
        select(
            func.count()
        ).select_from(Point)
    )

    # ensure all data made it into the database
    assert count == len(DATA)

    # get the first record from the db
    point = db.execute(select(Point)).scalars().first()
    assert point

    for coords in [point.coordinates, point.to_geojson()["geometry"]["coordinates"]]:
        # validate coordinates
        assert len(coords) == 3
        assert coords[0] == DATA[0][1]
        assert coords[1] == DATA[0][0]
        assert coords[2] == 100

    # check to_dict
    assert point.location == point.to_dict()["location"]
    assert point.location == point.to_dict(True)["location"]
    assert 'coordinates' not in point.to_dict()

    point = db.execute(
        select(
            Point
        ).where(
            Point.altitude.is_(None)
        ).where(
            Point.node_id == NODE_ID_FFX,
            Point.attribute_id == ATTR_ID_FFX
        )
    ).scalars().one()

    assert point
    coords: list[float] = point.coordinates
    assert len(coords) == 2
    assert point.coordinates[0] == -77.306373
    assert point.coordinates[1] == 38.846224


def test_get_or_create_existing_record(db: Session):
    load_sample_data(db)

    # get a specific point
    point: Point = db.execute(
        select(
            Point
        ).where(
            Point.altitude.is_(None)
        ).where(
            Point.node_id == NODE_ID_FFX,
            Point.attribute_id == ATTR_ID_FFX
        )
    ).scalars().one()

    assert point
    coords: list[float] = point.coordinates
    assert len(coords) == 2
    assert point.coordinates[0] == -77.306373
    assert point.coordinates[1] == 38.846224

    point2, is_new = Point.get_or_create(db, node_id=NODE_ID_FFX, attribute_id=ATTR_ID_FFX)
    assert point2
    assert not is_new
    assert point == point2


def test_get_or_create_new_record(db: Session):
    point, is_new = Point.get_or_create(db, defaults=dict(
        node_id=NODE_ID_FFX,
        node_version=1,
        attribute_id=uuid4(),
        attribute_version=1,
        location="POINT(-77.306373 38.846224)",  # lng lat
        altitude=None,
        geohash=pgh.encode(-77.306373, 38.846224),
        detection_time=datetime.now(timezone.utc),
        acm=DEFAULT_ACM
    ), node_id=NODE_ID_FFX, attribute_id=ATTR_ID_FFX)

    assert point
    assert is_new


def test_point_updated_at_no_timezone(db: Session):
    point, is_new = Point.get_or_create(db, defaults=dict(
        node_id=NODE_ID_FFX,
        node_version=1,
        attribute_id=uuid4(),
        attribute_version=1,
        location="POINT(-77.306373 38.846224)",  # lng lat
        altitude=None,
        geohash=pgh.encode(-77.306373, 38.846224),
        detection_time=datetime.now(tz=timezone.utc),
        acm=DEFAULT_ACM
    ), node_id=NODE_ID_FFX, attribute_id=ATTR_ID_FFX)

    db.add(point)
    db.commit()
    db.refresh(point)

    point.updated_at = datetime.now()
    db.add(point)

    with pytest.raises(StatementError):
        db.commit()


def test_get_points_track(db: Session):
    load_sample_data(db)

    points = get_track_points(db, NODE_ID)

    assert len(points) == 12
    assert points[0].detection_time < points[-1].detection_time


def test_get_track(db: Session):
    load_sample_data(db)

    track: Track = get_track(db, NODE_ID)

    assert track
    assert len(track.points) == 12
    assert track.points[0].node_id == NODE_ID
    assert track.points[0].attribute_id == DATA[0][5]
    assert track.points[0].coordinates[0] == DATA[0][1]
    assert track.points[0].coordinates[1] == DATA[0][0]


def test_get_track_uuid_str(db: Session):
    load_sample_data(db)

    track: Track = get_track(db, "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8")

    assert track
    assert len(track.points) == 12
    assert track.points[0].node_id == UUID("0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8")
    assert track.points[0].attribute_id == DATA[0][5]
