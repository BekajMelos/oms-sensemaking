"""Tests for geo ORM models."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from oms_sdk import DEFAULT_ACM
from oms_sensemaking.models.geo import Point
from sqlalchemy import func, select
from sqlalchemy.orm import Session

DATA: list = [  # Latitude, Longitude, Altitude (m), Description, Node ID
    [34.052235, -118.243683, 100, "Central Los Angeles, downtown area", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.052500, -118.245000, 150, "Near Los Angeles State Historic Park", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.053000, -118.247000, 120, "Close to Chinatown", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.054000, -118.249000, 180, "Elysian Park entrance", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.055000, -118.251000, 200, "Elysian Park trailhead", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.056000, -118.253000, 250, "Midpoint of trail, higher elevation", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.057000, -118.255000, 230, "Near Dodger Stadium", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.058000, -118.257000, 190, "Downhill from Dodger Stadium", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.059000, -118.259000, 160, "Park exit", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.060000, -118.261000, 140, "Residential area", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.061000, -118.263000, 110, "End of the route, nearby school", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [34.062000, -118.265000, 90, "Final point, local marketplace", "0c5c85b1-fa89-4b78-a4cd-a5cee6e90ec8"],
    [38.846224, -77.306373, None, "Fairfax, VA", "6796b293-e0b2-4ba3-a361-c59c6e07248b"]
]


def test_points_lat_lon(db: Session):
    attr_id: UUID = uuid4()

    for row in DATA:
        point: Point = Point(
            node_id=row[4],
            node_version=1,
            attribute_id=attr_id,
            attribute_version=1,
            location=f"POINT({row[1]} {row[0]})",  # lng lat
            altitude=row[2],
            geohash="xxxx",
            detection_time=datetime.now(tz=timezone.utc),
            acm=DEFAULT_ACM
        )

        db.add(point)

    db.commit()

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
    assert point.point_id

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

    # select(User).where(User.name == "spongebob")
    point = db.execute(
        select(
            Point
        ).where(
            Point.altitude.is_(None)
        ).where(Point.node_id == "6796b293-e0b2-4ba3-a361-c59c6e07248b")
    ).scalars().one()

    assert point
    coords: list[float] = point.coordinates
    assert len(coords) == 2
    assert point.coordinates[0] == -77.306373
    assert point.coordinates[1] == 38.846224
