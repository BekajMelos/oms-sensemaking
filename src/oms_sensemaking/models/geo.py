"""Geospatial Sensemaker models."""

import itertools
import json
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import UTC, datetime
from functools import cached_property, reduce
from operator import mul

import geopy.distance
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape
from geolib import geohash
from oms_sdk.generated.generated_graphql_client import Confidence
from shapely import LineString
from shapely.geometry.point import Point as ShapelyPoint
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table, func, select
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    Session,
    mapped_column,
    relationship,
)

from oms_sensemaking.clients.instances import aac_client, db_session
from oms_sensemaking.config import SETTINGS

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

    altitude: Mapped[float | None] = mapped_column(Float, nullable=True, comment="The altitude of the point.")

    @hybrid_property
    def geohash(self):
        """
        Return a geocoded representation of the location.

        This value is calculated when the data is queried
        or provided by Python if accessed in a Python expression
        """
        return geohash.encode(self.coordinates[1], self.coordinates[0], 20)

    @geohash.expression  # type: ignore [no-redef]
    @classmethod
    def geohash(cls):
        """
        Return a geocoded representation of the location when accessed in a query.
        Example: 'Point.geohash.like("ttnfv2u%")'

        Replaces previous use of with_expression:
        with_expression(Point.geohash, func.ST_GeoHash(Point.location))
        """
        return func.ST_GeoHash(cls.location, 20)

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

    You should never refer to point_id outside of a query context.
    The parameter is auto-generated for new instances and used by SQLAlchemy.
    """

    __tablename__: str = "points"
    point_id: Mapped[int] = mapped_column(
        Integer,
        autoincrement=True,
        nullable=False,
        primary_key=True,
        init=False,
        comment="The unique ID of the Sensemaking Point.",
    )
    weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
        comment="The weight assigned to the Point from confidence and other factors.",
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
    """Represents a track.

    This model is also a dataclass. The order of the positional parameters in
    the generated ``__init__()`` method are:

    - points
    - node_id
    - algorithm
    - observation_ids
    - track_uuid

    You should never refer to track_id outside of a query context.
    The parameter is auto-generated for new instances and used only by SQLAlchemy.
    Use track_uuid for Sensemaker's unique identifier for a track.
    """

    points: Mapped[list[Point]] = relationship(secondary=track_points_table, lazy="joined")
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
    observation_ids: Mapped[set[UUID]] = mapped_column(
        ARRAY(UUID),
        nullable=False,
        default_factory=set,
        comment="The list of any observation IDs used to create this track, even if dropped.",
    )
    track_uuid: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        default_factory=uuid.uuid4,
        comment="The UUID of the track within Sensemaker.",
    )
    track_id: Mapped[int] = mapped_column(
        Integer,
        autoincrement=True,
        nullable=False,
        primary_key=True,
        init=False,
        comment="The unique ID of the Track within the database only.",
    )

    __tablename__: str = "tracks"

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
        return Track(
            points=points,
            node_id=points[0].node_id,
            algorithm=self.algorithm,
            observation_ids={p.observation_id for p in points},  # type: ignore
        )


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
        # Integer division by bin size sorts timestamps into bins of arbitrary length
        time_bins = {
            k: tuple(g)
            for k, g in itertools.groupby(
                (p for p in points if p.weight),
                key=lambda x: x.detection_time.timestamp() // self.config["time_bin_size_seconds"],
            )
        }
        confidence_map = SETTINGS.confidence_weight_map
        weighted_points: list[Point] = []
        with db_session() as db:
            db.expire_on_commit = False
            for bin_points in time_bins.values():
                if len(bin_points) == 1:
                    weighted_points.extend(bin_points)
                    continue
                # Reuse most of the attributes from the first point in the bin
                # TODO: Deal with altitudes
                # TODO: Observation_id is still fake. Source_id is from a Point, should belong to Sensemaker eventually
                LOGGER.info(f"Averaging {len(bin_points)} points: {', '.join(str(p.coordinates) for p in bin_points)}")
                acm_rollup = aac_client.get_acm_rollup([{"ACM": point.acm} for point in bin_points])
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
        return Track(
            points=weighted_points,
            node_id=weighted_points[0].node_id,
            algorithm=self.algorithm,
            observation_ids={p.observation_id for p in points},  # type: ignore
        )


def weighted_average(values: Iterable[int | float], weights: Iterable[int | float]) -> float:
    # Consume input iterables into reusable collection type
    values = tuple(values)
    weights = tuple(weights)
    if sum(weights) == 0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights, strict=True)) / sum(weights)


def get_track(db: Session, track_uuid: str | uuid.UUID) -> Track:
    """
    Get track for a given track uuid.

    :param db: A database session.
    :param track_uuid: The Track's unique identifier.
    :return: A Track.
    """
    return db.execute(select(Track).filter_by(track_uuid=track_uuid)).unique().scalar_one()


def apply_common_sense_filters(points: list[Point], iri: str) -> list[Point]:
    """
    Apply common sense filters to the track to identify any outlying points. Runs the following filters:
    - <b>Teleportation</b>: Removes points that are likely the result of teleportation.
    - <b>Altitude</b>: Removes points with negative or extreme altitude/altitude change.

    :param track: The track to apply common sense filters to.
    :param iri: The IRI of the object being tracked.
    :return: The filtered track
    """
    from logging import getLogger

    logger = getLogger(__name__)

    if not SETTINGS.apply_common_sense_filters:
        logger.info("Common sense filters are disabled. Skipping.")
        return points

    filtered_points = _filter_altitude_by_iri(_filter_teleportation(points), iri)
    return filtered_points


def _filter_teleportation(points: list[Point]) -> list[Point]:
    """
    Filter points that are likely the result of teleportation.

    :param points: The list of points to filter teleport anomalies from.
    :return: The filtered points. Points that are likely the result of teleportation have their weights assigned to 0.
    """
    from logging import getLogger

    logger = getLogger(__name__)

    for i in range(1, len(points)):
        # get the current and previous points
        current_point = points[i]
        prev_point = points[i - 1]

        time_delta = current_point.detection_time - prev_point.detection_time
        distance: float = geopy.distance.geodesic(
            (current_point.coordinates[1], current_point.coordinates[0]),
            (prev_point.coordinates[1], prev_point.coordinates[0]),
        ).meters
        relative_velocity = distance / time_delta.total_seconds() if time_delta.total_seconds() > 0 else 0

        # If the distance between two points is very large and the time between them is very small, it's likely that the
        # object teleported. We don't want to include these points in the track, but we'll still keep them in the
        # sensemaking db.
        distance_exceeded = distance > SETTINGS.distance_threshold_meters
        time_within_threshold = time_delta.total_seconds() < SETTINGS.time_threshold_seconds
        velocity_within_threshold = 0 < relative_velocity < SETTINGS.relative_velocity_threshold_mps
        if (distance_exceeded and time_within_threshold) or velocity_within_threshold:
            logger.debug(
                "Removing point %s due to teleportation: distance=%s, time_delta=%s",
                current_point.observation_id,
                distance,
                time_delta,
            )
            points[i].weight *= 0
    return points


def _filter_altitude_by_iri(points: list[Point], iri: str) -> list[Point]:
    """
    Filter out points that drastically deviate in elevation.

    :param track: The track to filter altitude discrepancies from.
    :return: The filtered track.
    """
    from logging import getLogger

    logger = getLogger(__name__)

    if "aircraft" not in iri.lower():
        logger.debug("Skipping altitude filtering for non-aircraft track.")
        return points

    for i in range(1, len(points)):
        # get the current and previous points
        current_point = points[i]
        prev_point = points[i - 1]
        # if either point doesn't have an altitude, skip this filter
        if current_point.altitude is None or prev_point.altitude is None:
            logger.debug("Skipping altitude filter for point %s", current_point.observation_id)
            continue

        # Check if the altitude is negative, zero, or exceeds the maximum altitude threshold.
        if current_point.altitude < 0:
            logger.debug(
                "Removing point %s due to negative altitude: altitude=%s",
                current_point.observation_id,
                current_point.altitude,
            )
            points[i].weight *= 0
            continue
        elif current_point.altitude > SETTINGS.altitude_threshold_meters:
            logger.debug(
                "Removing point %s due to altitude exceeding maximum: altitude=%s",
                current_point.observation_id,
                current_point.altitude,
            )
            points[i].weight *= 0

        # Check if the change in altitude between this point and the previous is large.
        if abs(current_point.altitude - prev_point.altitude) > SETTINGS.altitude_deviation_threshold_meters:
            logger.debug(
                "Removing point %s due to altitude discrepancy: altitude=%s, prev_altitude=%s",
                current_point.observation_id,
                current_point.altitude,
                prev_point.altitude,
            )
            points[i].weight *= 0

    return points
