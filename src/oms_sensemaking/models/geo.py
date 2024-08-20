"""Geospatial Sensemaker models."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry.point import Point as ShapelyPoint
from sqlalchemy import Float, String, select
from sqlalchemy.orm import Mapped, MappedAsDataclass, Session, mapped_column

from .base import AuditMixin, BaseORM, OmsAttributeMixin, SecurityMarkingMixin, UtcDateTime


class OmsGeoMixin(MappedAsDataclass):
    """Declare OMS geospatial metadata."""

    location: Mapped[WKBElement] = mapped_column(
        # NOTE: this could alternatively be represented as a 3D point, which
        # seems to be an undocumented feature in geoalchemy. Using a 2D point
        # now, because the source data does not seem to enforce the presence
        # of an altitude/elevation field.
        #
        # https://github.com/geoalchemy/geoalchemy2/issues/157
        Geometry('POINT', dimension=2, srid=4326, spatial_index=False),
        nullable=False,
        unique=False,
        comment='The 2D location of the point.'
    )

    altitude: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        comment='The altitude of the point.'
    )

    geohash: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment='A geocoded representation of the location.'
    )

    detection_time: Mapped[datetime] = mapped_column(
        UtcDateTime,
        unique=False,
        nullable=False,
        comment='The time the point was detected.'
    )

    @property
    def coordinates(self) -> list[float]:
        """Returns the longitude, latitude, and optional altitude (in that order).

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


class Point(BaseORM, OmsAttributeMixin, OmsGeoMixin, SecurityMarkingMixin, AuditMixin):
    """Represents a geolocation in OMS."""

    __tablename__: str = 'points'


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

        if point_count > 0:
            self.start_time = self.points[0].detection_time
            self.end_time = self.points[-1].detection_time


def get_track_points(db: Session, node_id: Union[str, uuid.UUID]) -> list[Point]:
    """
    Get track for a given node id.

    :param db: A database session.
    :param node_id: The Node's unique identifier.
    """
    # NOTE: this a naive implementation.
    #
    # @see https://stackoverflow.com/questions/7389759/memory-efficient-built-in-sqlalchemy-iterator-generator
    return list(db.execute(
        select(
            Point
        ).where(
            Point.node_id == node_id
        ).order_by(Point.detection_time.asc())
    ).scalars().all())


def get_track(db: Session, node_id: Union[str, uuid.UUID]) -> Track:
    """
    Get track for a given Node.

    :param db: A database session.
    :param node_id: The Node's unique identifier.
    :return: A Track.
    """
    if isinstance(node_id, str):
        node_id = uuid.UUID(node_id)

    return Track(points=get_track_points(db, node_id), node_id=node_id)
