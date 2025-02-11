"""Geospatial Sensemaker models."""

import itertools
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import cached_property, reduce
from operator import mul
from typing import Iterable, Optional, Union

import timehash
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape
from oms_sdk.generated.generated_graphql_client import Confidence
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
from oms_sensemaking.core.acm import get_acm_rollup

from .base import AuditMixin, BaseORM, OmsObservationMixin, SecurityMarkingMixin, TrackMixin, UtcDateTime


class OmsGeoMixin(MappedAsDataclass):
    """Declare OMS geospatial metadata."""

    location: Mapped[WKTElement] = mapped_column(
        # NOTE: this could alternatively be represented as a 3D point, which
        # seems to be an undocumented feature in geoalchemy. Using a 2D point
        # now, because the source data does not seem to enforce the presence
        # of an altitude/elevation field.
        #
        # https://github.com/geoalchemy/geoalchemy2/issues/157
        Geometry("POINT", dimension=2, srid=SETTINGS.srid, spatial_index=False),
        nullable=False,
        unique=False,
        comment="The 2D location of the point.",
    )

    altitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="The altitude of the point.")

    @declared_attr
    def geohash(self) -> Mapped[str]:
        """
        Return a geocoded representation of the location.

        This value is calculated when the data is queried and may be
        null if the query was not configured to populate it.
        """
        return query_expression(doc="A geocoded representation of the location.")

    detection_time: Mapped[datetime] = mapped_column(
        UtcDateTime, unique=False, nullable=False, comment="The time the point was detected."
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
        return {"type": "Feature", "geometry": {"type": "Point", "coordinates": self.coordinates}}


class Point(BaseORM, OmsObservationMixin, OmsGeoMixin, SecurityMarkingMixin, AuditMixin, TrackMixin):
    """
    Represents a geolocation in OMS.

    This model is also a dataclass. The order of the positional parameters in
    the generated ``__init__()`` method are:

    - node_id
    - node_version
    - source_id
    - observation_id
    - observation_version
    - observation_confidence
    - location
    - altitude
    - detection_time
    - acm
    - track_id
    - weight
    """

    __tablename__: str = "points"
    weight: Mapped[float] = mapped_column(
        Float, nullable=False, comment="The weight assigned to the Point from confidence and other factors."
    )

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
    # TODO: Add optional parameter(s) for metadata:
    #   aggregate confidence, excluded Points, track weaver algorithm, etc.

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


class TrackWeaverBase(ABC):
    """Abstract TrackWeaver base class."""

    def __init__(self, *args, **kwargs) -> None:
        """Create a new instance of the track weaver."""
        super().__init__()
        self.name: str = self.__class__.__name__
        self.config: dict = {}

    @abstractmethod
    def execute(self, points: list[Point]) -> Track:
        """
        Weave a Track from a series of Points.

        This method provides the implementation of the track weaver's business
        logic. Subclasses must override this method.
        """
        raise NotImplementedError()


class NaiveTrackWeaver(TrackWeaverBase):
    """
    A simple track weaver that accepts all points in order.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial "naive" algorithm implementation.

    """

    def __init__(self) -> None:
        """Create a new instance of NaiveTrackWeaver."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = {}

    def execute(self, points: list[Point]) -> Track:
        points.sort(key=lambda x: x.detection_time)
        return Track(points=points, node_id=points[0].node_id)


class TimeBinTrackWeaver(TrackWeaverBase):
    """
    A track weaver that bins Points by time, then weighted averages bins by confidence.

    Algorithm ChangeLog
    ===================

    [1.0.1]

    - Use Point.weight attribute instead of confidence weight map.

    [1.0.0]

    - Initial "time binning" algorithm implementation.

    """

    def __init__(self) -> None:
        """Create a new instance of NaiveTrackWeaver."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = {
            "timehash_bin_size": SETTINGS.timehash_bin_size,
        }

    def execute(self, points: list[Point]) -> Track:
        points.sort(key=lambda x: x.detection_time)
        time_bins = {
            time_bin: tuple(points)
            for time_bin, points in itertools.groupby(
                points,
                key=lambda x: timehash.encode_from_datetime(
                    x.detection_time, precision=self.config["timehash_bin_size"]
                ),
            )
        }
        confidence_map = SETTINGS.confidence_weight_map
        weighted_points: list[Point] = []
        for points in time_bins.values():
            # Reuse most of the attributes from the first point in the bin
            # TODO: Deal with altitudes
            # TODO: Observation_id is still fake. Source_id is from a Point, should belong to Sensemaker eventually
            point_dict = {
                "node_id": points[0].node_id,
                "node_version": points[0].node_version,
                "source_id": points[0].source_id,
                "observation_id": uuid.uuid4(),
                "observation_version": points[0].observation_version,
                "altitude": None,
                "detection_time": points[0].detection_time,
                "acm": get_acm_rollup([point.acm for point in points]),
                "track_id": points[0].track_id,
            }
            lon = weighted_average((p.coordinates[0] for p in points), (p.weight for p in points))
            lat = weighted_average((p.coordinates[1] for p in points), (p.weight for p in points))
            point_dict["location"] = f"Point({lon} " f"{lat})"
            confidence_level = Confidence.UNKNOWN
            confidence_val = min(confidence_map[p.observation_confidence] for p in points)
            for confidence, weight in confidence_map.items():
                if weight == confidence_val:
                    confidence_level = confidence
            point_dict["observation_confidence"] = confidence_level
            point_dict["weight"] = reduce(mul, (point.weight for point in points))
            weighted_points.append(Point(**point_dict))

        return Track(points=weighted_points, node_id=weighted_points[0].node_id)


def weighted_average(values: Iterable[int | float], weights: Iterable[int | float]):
    # Consume input iterables into reusable collection type
    values = tuple(values)
    weights = tuple(weights)
    if sum(weights) == 0:
        return 0
    return sum(v * w for v, w in zip(values, weights, strict=True)) / sum(weights)


def get_track_points(db: Session, track_id: Union[str, uuid.UUID]) -> list[Point]:
    """
    Get track points for a given track id.

    :param db: A database session.
    :param track_id: The Track's unique identifier.
    """
    # NOTE: this a naive implementation.
    #
    # @see https://stackoverflow.com/questions/7389759/memory-efficient-built-in-sqlalchemy-iterator-generator
    return list(
        db.execute(
            select(Point)
            .where(Point.track_id == track_id)
            .order_by(Point.detection_time.asc())
            .options(with_expression(Point.geohash, func.ST_GeoHash(Point.location)))
        )
        .scalars()
        .all()
    )


def get_track(db: Session, track_id: Union[str, uuid.UUID]) -> Track:
    """
    Get track for a given track id.

    :param db: A database session.
    :param track_id: The Track's unique identifier.
    :return: A Track.
    """
    points = get_track_points(db, track_id)
    node_id = points[0].node_id

    return Track(points=points, node_id=node_id)
