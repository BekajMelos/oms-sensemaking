"""Geospatial Sensemaker models."""

import itertools
import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from functools import cached_property, reduce
from operator import mul
from typing import Iterable, Optional, Union

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape
from oms_sdk.generated.generated_graphql_client import Confidence
from shapely import LineString
from shapely.geometry.point import Point as ShapelyPoint
from sqlalchemy import Column, Float, ForeignKey, String, Table, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    Session,
    declared_attr,
    mapped_column,
    query_expression,
    relationship,
    with_expression,
)

from oms_sensemaking.clients import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.acm import get_acm_rollup

from .base import AuditMixin, BaseORM, OmsObservationMixin, SecurityMarkingMixin, UtcDateTime

LOGGER: logging.Logger = logging.getLogger(__name__)


track_points_table = Table(
    "track_points",
    BaseORM.metadata,
    Column("track_id", ForeignKey("tracks.track_id"), primary_key=True),
    Column("point_id", ForeignKey("points.point_id"), primary_key=True),
)


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


class Point(BaseORM, OmsObservationMixin, OmsGeoMixin, SecurityMarkingMixin, AuditMixin):
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
    - weight
    - point_id (default)

    It should never be necessary to specify point_id in the constructor.
    The parameter is auto-generated for new instances and used by SQLAlchemy.
    """

    __tablename__: str = "points"
    weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
        comment="The weight assigned to the Point from confidence and other factors.",
    )
    point_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False,
        comment="The unique ID of the Sensemaking Point.",
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


class Track(BaseORM):
    """Represents a track."""

    __tablename__: str = "tracks"

    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False,
        comment="The unique ID of the Sensemaking Track.",
    )
    points: Mapped[list[Point]] = relationship(secondary="track_points_table")
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="The node ID of the object associated with this track.",
    )
    algorithm: Mapped[str] = mapped_column(
        String,
        nullable=True,
        comment="The track weaver algorithm used to create this track.",
    )

    @property
    def start_time(self) -> datetime | None:
        if not self.points:
            return None
        return self.points[0].detection_time

    @property
    def end_time(self) -> datetime | None:
        if not self.points:
            return None
        return self.points[-1].detection_time

    @property
    def observation_ids(self) -> list[uuid.UUID]:
        return [p.observation_id for p in self.points]

    def to_linestring(self) -> LineString:
        """Return a linestring representation of the track."""
        return LineString([point.coordinates for point in self.points])


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
        self.version = (1, 1, 0)
        self.name = self.__class__.__name__
        self.config = {}
        self.algorithm = "naive"

    def execute(self, points: list[Point]) -> Track:
        points.sort(key=lambda x: x.detection_time)
        return Track(points=points, node_id=points[0].node_id, algorithm=self.algorithm)


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
        """Create a new instance of TimeBinTrackWeaver."""
        super().__init__()
        self.version = (1, 1, 0)
        self.name = self.__class__.__name__
        self.config = {
            "time_bin_size_seconds": SETTINGS.time_bin_size_seconds,
        }
        self.algorithm = "time_bin_weighted_average"

    def execute(self, points: list[Point]) -> Track:
        points.sort(key=lambda x: x.detection_time)
        # Give the weaved track a new track_id. The old track_id assigned to the parent Points remains in the DB.
        track_id = uuid.uuid4()
        LOGGER.info(f"Weaving new track_id: {track_id}")
        # Integer division by bin size sorts timestamps into bins of arbitrary length
        time_bins = {
            time_bin: tuple(points)
            for time_bin, points in itertools.groupby(
                (p for p in points if p.weight),
                key=lambda x: x.detection_time.timestamp() // self.config["time_bin_size_seconds"],
            )
        }
        confidence_map = SETTINGS.confidence_weight_map
        weighted_points: list[Point] = []
        with db_session() as db:
            db.expire_on_commit = False
            for bin_points in time_bins.values():
                # TODO: Skip this process for bins containing a single Point. Associate Point to new track_id.
                # Reuse most of the attributes from the first point in the bin
                # TODO: Deal with altitudes
                # TODO: Observation_id is still fake. Source_id is from a Point, should belong to Sensemaker eventually
                LOGGER.info(f"Averaging {len(bin_points)} points: {', '.join(str(p.coordinates) for p in bin_points)}")
                acm_rollup = get_acm_rollup([{"ACM": point.acm} for point in bin_points])
                point_dict = {
                    "node_id": bin_points[0].node_id,
                    "node_version": bin_points[0].node_version,
                    "source_id": bin_points[0].source_id,
                    "observation_id": uuid.uuid4(),
                    "observation_version": bin_points[0].observation_version,
                    "altitude": None,
                    "detection_time": datetime.fromtimestamp(
                        weighted_average(
                            (p.detection_time.astimezone(UTC).timestamp() for p in bin_points),
                            (p.weight for p in bin_points),
                        ),
                        tz=UTC,
                    ),
                    "acm": acm_rollup,
                    "track_id": track_id,
                }
                lon = weighted_average((p.coordinates[0] for p in bin_points), (p.weight for p in bin_points))
                lat = weighted_average((p.coordinates[1] for p in bin_points), (p.weight for p in bin_points))
                point_dict["location"] = f"Point({lon} " f"{lat})"
                # Find the Confidence enum member mapped to the lowest weight among parent Point confidences
                confidence_level = Confidence.UNKNOWN
                confidence_val = min(confidence_map[p.observation_confidence] for p in bin_points)
                for confidence, weight in confidence_map.items():
                    if weight == confidence_val:
                        confidence_level = confidence
                point_dict["observation_confidence"] = confidence_level
                # Multiply parent Point weights to get new Point weight [0.0 - 1.0]
                point_dict["weight"] = reduce(mul, (point.weight for point in bin_points))
                weighted_point, _ = Point.get_or_create(db, defaults=None, **point_dict)
                weighted_points.append(weighted_point)
                LOGGER.info(f"Averaged point: {weighted_point.coordinates}")
        LOGGER.info("GeoJSON features:")
        LOGGER.info(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "name": "Original Points",
                                "num_points": len(points),
                                "stroke": "#ff0000",
                                "stroke-width": 2,
                                "stroke-opacity": 1,
                            },
                            "geometry": LineString([point.coordinates for point in points]).__geo_interface__,
                            "id": 0,
                        },
                        {
                            "type": "Feature",
                            "properties": {
                                "name": "Weaved Track",
                                "algorithm": self.algorithm,
                                "num_points": len(weighted_points),
                                "average_point_weight": round(
                                    sum(p.weight for p in weighted_points) / len(weighted_points), 2
                                ),
                                "stroke": "#00ff1e",
                                "stroke-width": 2,
                                "stroke-opacity": 1,
                            },
                            "geometry": LineString([point.coordinates for point in weighted_points]).__geo_interface__,
                            "id": 1,
                        },
                    ],
                }
            )
        )
        return Track(points=weighted_points, node_id=weighted_points[0].node_id, algorithm=self.algorithm)


def weighted_average(values: Iterable[int | float], weights: Iterable[int | float]) -> float:
    # Consume input iterables into reusable collection type
    values = tuple(values)
    weights = tuple(weights)
    if sum(weights) == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights, strict=True)) / sum(weights)


def get_track_points(db: Session, track_id: Union[str, uuid.UUID]) -> list[Point]:
    """
    Get track points for a given track id.

    :param db: A database session.
    :param track_id: The Track's unique identifier.
    """
    # TODO: Add track_points relation table to DB. Stop storing track_id on points table or Point model.
    #       Add tracks table to DB. Store all Track attributes and pk track_ids there.
    #       Query points by JOIN on track_points table.
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
