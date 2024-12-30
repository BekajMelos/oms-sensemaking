"""Geospatial Sensemaker models."""
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import cached_property
from typing import Optional, Union

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape
from shapely import LineString
from shapely.geometry.point import Point as ShapelyPoint
from sqlalchemy import Float, func, select
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    Session,
    declared_attr,
    mapped_column,
    query_expression,
    with_expression,
)

from oms_sensemaking.config import SETTINGS

from .base import AuditMixin, BaseORM, OmsObservationMixin, SecurityMarkingMixin, UtcDateTime


class OmsGeoMixin(MappedAsDataclass):
    """Declare OMS geospatial metadata."""

    location: Mapped[WKTElement] = mapped_column(
        # NOTE: this could alternatively be represented as a 3D point, which
        # seems to be an undocumented feature in geoalchemy. Using a 2D point
        # now, because the source data does not seem to enforce the presence
        # of an altitude/elevation field.
        #
        # https://github.com/geoalchemy/geoalchemy2/issues/157
        Geometry('POINT', dimension=2, srid=SETTINGS.srid, spatial_index=False),
        nullable=False,
        unique=False,
        comment='The 2D location of the point.'
    )

    altitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment='The altitude of the point.'
    )

    @declared_attr
    def geohash(self) -> Mapped[str]:
        """
        Return a geocoded representation of the location.

        This value is calculated when the data is queried and may be
        null if the query was not configured to populate it.
        """
        return query_expression(doc="A geocoded representation of the location.")

    detection_time: Mapped[datetime] = mapped_column(
        UtcDateTime,
        unique=False,
        nullable=False,
        comment='The time the point was detected.'
    )

    @cached_property
    def coordinates(self) -> list[float]:
        """
        Return the longitude, latitude, and optional altitude (in that order).

        If altitude is provided the result will be a three element list, otherwise a 2 element list.
        """
        point_shape: ShapelyPoint = to_shape(self.location)
        coordinates: list[float] = [point_shape.x, point_shape.y]

        if self.altitude is not None:
            coordinates.append(self.altitude)

        return coordinates

    def to_geojson(self) -> dict:
        """Return a GeoJSON representation of the point."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": self.coordinates
            }
        }


class Point(BaseORM, OmsObservationMixin, OmsGeoMixin, SecurityMarkingMixin, AuditMixin):
    """
    Represents a geolocation in OMS.

    This model is also a dataclass. The order of the positional parameters in
    the generated ``__init__()`` method are:

    - acm
    - location
    - altitude
    - detection_time
    - node_id
    - node_version
    - track_id
    - observation_id
    - observation_version
    """

    __tablename__: str = 'points'

    def __post_init__(self):
        """
        Post initialization.

        This function is responsible for formatting the location field in the
        event that it is set as a string, rather than a specific GeoAlchemy type.
        """
        if isinstance(self.location, str):
            self.location = WKTElement(self.location, srid=SETTINGS.srid)

    def __lt__(self, other: "Point"):
        return self.detection_time < other.detection_time


@dataclass
class Track:
    """Represents a track."""

    points: list[Point]
    node_id: uuid.UUID
    start_time: datetime = field(init=False)
    end_time: datetime = field(init=False)

    def __post_init__(self) -> None:
        """
        Create a new instance of Track.

        This method populates the ``start_time`` and ``end_time`` attributes
        based on the ``points`` attribute (i.e. the track).
        """
        point_count: int = len(self.points)

        if point_count < 2:
            # TODO maybe just log this and move on
            raise ValueError("A Track must consist of at least 2 points.")

        if point_count > 0:
            self.start_time = self.points[0].detection_time
            self.end_time = self.points[-1].detection_time

    def to_linestring(self) -> LineString:
        """Return a linestring representation of the track."""
        return LineString([point.coordinates for point in self.points])


    def to_dict(self) -> dict:
        """Return a dictionary representation of the object."""
        return asdict(self)


def get_track_points(db: Session, track_id: Union[str, uuid.UUID]) -> list[Point]:
    """
    Get track points for a given track id.

    :param db: A database session.
    :param track_id: The Track's unique identifier.
    """
    # NOTE: this a naive implementation.
    #
    # @see https://stackoverflow.com/questions/7389759/memory-efficient-built-in-sqlalchemy-iterator-generator
    return list(db.execute(
        select(
            Point
        ).where(
            Point.track_id == track_id
        ).order_by(
            Point.detection_time.asc()
        ).options(
            with_expression(Point.geohash, func.ST_GeoHash(Point.location))
        )
    ).scalars().all())

def get_node_id_by_track_id(db: Session, track_id: Union[str, uuid.UUID]):
    """
    Get node id for a given track id

    ::param db: A database session
    ::param track_id: The Track's unique identifier.
    """
    return db.execute(
        select(
            Point.node_id
        ).where(
            Point.track_id == track_id
        ).order_by(
            Point.detection_time.asc()
        )
    ).scalar()

def get_track_id_by_node_id(
        db: Session, node_id: Union[str, uuid.UUID], start_time: datetime, end_time: datetime):
    """
    Get track id for a given node id and start and end times

    ::param db: A database session
    ::param node_id: The Node's unique identifier.
    ::param start_time: The time the track began
    ::param end_time: The time the track ended
    """
    return db.execute(
        select(
            Point.track_id
        ).where(
            Point.node_id == node_id,
            Point.detection_time > start_time,
            Point.detection_time < end_time
        ).order_by(
            Point.detection_time.asc()
        )
    ).scalar()


def get_track(db: Session, track_id: Union[str, uuid.UUID]) -> Track:
    """
    Get track for a given track id.

    :param db: A database session.
    :param track_id: The Track's unique identifier.
    :return: A Track.
    """
    node_id = get_node_id_by_track_id(db, track_id)

    if isinstance(node_id, str):
        node_id = uuid.UUID(node_id)

    return Track(points=get_track_points(db, track_id), node_id=node_id)
