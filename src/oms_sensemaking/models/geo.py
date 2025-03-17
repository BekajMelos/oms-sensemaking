"""Geospatial Sensemaker models."""

import itertools
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta, timezone
from functools import cached_property, reduce
from operator import mul
from typing import TypedDict

import geopy.distance as gd
from dateutil.parser import isoparse
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape
from geolib import geohash
from oms_sdk.generated.generated_graphql_client import Confidence
from oms_sdk.generated.generated_graphql_client.observation import ObservationObservation
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


class TimedCoords(TypedDict):
    detection_time: datetime
    coordinates: Sequence[int]


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
                (p for p in points if p.weight > 0),
                key=lambda x: x.detection_time.timestamp() // self.config["time_bin_size_seconds"],
            )
        }
        confidence_map = SETTINGS.confidence_weight_map
        weighted_points: list[Point] = []
        # db_session is used to persist averaged Points to the DB, but the returned Track is up to the caller to handle
        with db_session() as db:
            db.expire_on_commit = False
            for bin_points in time_bins.values():
                if len(bin_points) == 1:
                    weighted_points.append(bin_points[0])
                    continue
                # Reuse most of the attributes from the first point in the bin
                # TODO: Deal with altitudes
                # TODO: Observation_id is still fake. Source_id is from a Point, should belong to Sensemaker eventually
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
                point_dict["location"] = f"Point({round(lon, 5)} " f"{round(lat, 5)})"
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


def decompose_observation_geometry(oms_obs: ObservationObservation) -> list[TimedCoords]:
    if oms_obs.geometry["type"] == "Point":
        return [
            {
                "detection_time": isoparse(oms_obs.startTime).replace(tzinfo=timezone.utc),
                "coordinates": oms_obs.geometry["coordinates"],
            }
        ]
    if oms_obs.geometry["type"] == "LineString":
        start_time = isoparse(oms_obs.startTime).replace(tzinfo=timezone.utc)
        end_time = isoparse(oms_obs.endTime).replace(tzinfo=timezone.utc)
        # Always remember to convert lon/lat to lat/lon to use geopy distance calc
        total_distance: float = gd.geodesic(
            *(gd.lonlat(*obs_coords) for obs_coords in oms_obs.geometry["coordinates"])
        ).meters
        total_time = end_time - start_time
        # Handle 0 elapsed time by giving all points the same time
        if total_time.total_seconds() == 0:
            LOGGER.info("Handling 0 elapsed time...")
            return [
                {
                    "detection_time": start_time,
                    "coordinates": coordinates,
                }
                for coordinates in oms_obs.geometry["coordinates"]
            ]
        # Handle 0 movement by dividing the time evenly across points
        if total_distance == 0:
            LOGGER.info("Handling 0 distance...")
            timed_coords: list[TimedCoords] = [
                {
                    "detection_time": start_time + total_time * (idx / len(oms_obs.geometry["coordinates"])),
                    "coordinates": coordinates,
                }
                for idx, coordinates in enumerate(oms_obs.geometry["coordinates"], start=1)
            ]
            # Eliminate rounding errors on final coordinate time
            timed_coords[-1]["detection_time"] = end_time
            return timed_coords
        average_velocity_mps = total_distance / total_time.total_seconds()
        # Assuming constant velocity: coordinate times are proportional to distance travelled so far
        LOGGER.info("Handling non-zero time and distance")
        timed_coords = [
            {
                "detection_time": start_time,
                "coordinates": oms_obs.geometry["coordinates"][0],
            }
        ] + [
            {
                "detection_time": start_time
                + timedelta(
                    seconds=gd.geodesic(
                        *(gd.lonlat(*coords) for coords in oms_obs.geometry["coordinates"][: idx + 1])
                    ).meters
                    / average_velocity_mps
                ),
                "coordinates": oms_obs.geometry["coordinates"][idx],
            }
            for idx in range(1, len(oms_obs.geometry["coordinates"]))
        ]
        # Eliminate rounding errors on final coordinate time
        timed_coords[-1]["detection_time"] = end_time
        return timed_coords
    return []


def filter_teleportation(points: list[Point]) -> list[Point]:
    last_good_point = points[0]
    last_altitude_point: Point | None = None
    bad_points = []
    for cur_point in points[1:]:
        if last_good_point.altitude is not None:
            last_altitude_point = last_good_point
        time_delta = cur_point.detection_time - last_good_point.detection_time
        distance: float = gd.geodesic(
            (cur_point.coordinates[1], cur_point.coordinates[0]),
            (last_good_point.coordinates[1], last_good_point.coordinates[0]),
        ).meters
        relative_velocity = distance / time_delta.total_seconds() if time_delta.total_seconds() > 0 else 0
        if time_delta.total_seconds() < SETTINGS.time_threshold_seconds:
            # Too little time resolution to accurately compare points.
            # Allow current point but don't update last good point.
            LOGGER.info(
                "Skipping point due to time delta %s s less than threshold %s s.",
                round(time_delta.total_seconds(), 1),
                SETTINGS.time_threshold_seconds,
            )
            continue
        if relative_velocity > SETTINGS.relative_velocity_threshold_mps:
            # Too fast, kill the current point and don't update the last good point.
            LOGGER.info(
                "Filtered point_id (%s) due to relative velocity %s mps exceeding threshold %s mps.",
                cur_point.point_id,
                round(relative_velocity, 1),
                SETTINGS.relative_velocity_threshold_mps,
            )
            cur_point.weight = 0
            bad_points.append(cur_point)
            continue
        if last_altitude_point is not None and cur_point.altitude is not None:
            # Check if the vertical movement between this point and the previous is large.
            time_delta = cur_point.detection_time - last_altitude_point.detection_time
            altitude_rate = abs(cur_point.altitude - last_altitude_point.altitude) / time_delta.total_seconds()  # type: ignore[operator]
            if altitude_rate > SETTINGS.altitude_deviation_threshold_mps:
                LOGGER.info(
                    "Removing point %s due to altitude rate deviation: altitude diff=%s, time=%s, rate=%s",
                    cur_point.observation_id,
                    abs(cur_point.altitude - last_altitude_point.altitude),  # type: ignore[operator]
                    time_delta,
                    altitude_rate,
                )
                cur_point.weight = 0
                bad_points.append(cur_point)
                continue
        # Made it through all checks. Update last good point for next comparison.
        last_good_point = cur_point
    if bad_points:
        LOGGER.info(f"Removed {len(bad_points)} of {len(points)} points.")
    points = [p for p in points if p not in bad_points]
    return points


def filter_altitude_by_iri(points: list[Point], iri: str) -> list[Point]:
    """
    Filter out points that drastically deviate in elevation.

    :param points: The points to filter altitude discrepancies from.
    :param iri: The IRI of the object of the observations.
    :return: The filtered points.
    """
    if "aircraft" not in iri.lower():
        LOGGER.info("Skipping altitude filtering for non-aircraft track.")
        return points

    for point in points:
        # if current point doesn't have an altitude, skip this filter
        if point.altitude is None:
            # LOGGER.info("Skipping altitude filter for point %s", cur_point.observation_id)
            continue

        # Check if the altitude is negative or exceeds the maximum altitude threshold.
        if point.altitude < 0:
            LOGGER.info(
                "Removing point %s due to negative altitude: altitude=%s",
                point.observation_id,
                point.altitude,
            )
            point.weight = 0
            continue
        elif point.altitude > SETTINGS.altitude_threshold_meters:
            LOGGER.info(
                "Removing point %s due to altitude exceeding maximum: altitude=%s",
                point.observation_id,
                point.altitude,
            )
            point.weight = 0
            continue
    return points
