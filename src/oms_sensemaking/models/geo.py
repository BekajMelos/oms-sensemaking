"""Geospatial Sensemaker models."""
import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry.point import Point as ShapelyPoint
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .base import AuditMixin, BaseOrm, UtcDateTime


class Point(AuditMixin, BaseOrm):
    """Represents a request to run an algorithm."""

    __tablename__: str = 'points'

    point_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
        comment='Unique identifier.'
    )

    node_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment='The ID of the node associated with this point.'
    )

    node_version: int = Column(
        Integer,
        nullable=False,
        comment='The version of the node associated with this point.'
    )

    attribute_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment='The ID of the attribute associated with this point.'
    )

    attribute_version: int = Column(
        Integer,
        nullable=False,
        comment='The version of the attribute associated with this point.'
    )

    location: WKBElement = Column(
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

    altitude: Optional[float] = Column(
        Float,
        nullable=True,
        comment='The altitude of the point.'
    )

    geohash: str = Column(
        String,
        nullable=False,
        comment='A geocoded representation of the location.'
    )

    detection_time: datetime = Column(
        UtcDateTime,
        unique=False,
        nullable=False,
        comment='The time the point was detected.'
    )

    acm: dict = Column(
        JSONB,
        nullable=False,
        comment='The ACM representing the classification of the Point.'
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
