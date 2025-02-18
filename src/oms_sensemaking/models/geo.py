"""Geospatial Sensemaker models."""

import itertools
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
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

from oms_sensemaking.clients.instances import aac_client, db_session
from oms_sensemaking.config import SETTINGS

from .base import AuditMixin, BaseORM, OmsObservationMixin, SecurityMarkingMixin, TrackMixin, UtcDateTime

LOGGER: logging.Logger = logging.getLogger(__name__)


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
        """Create a new instance of TimeBinTrackWeaver."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = {
            "time_bin_size_seconds": SETTINGS.time_bin_size_seconds,
        }

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
                            "properties": {"stroke": "#002aff", "stroke-width": 2, "stroke-opacity": 1},
                            "geometry": LineString([point.coordinates for point in points]).__geo_interface__,
                            "id": 0,
                        },
                        {
                            "type": "Feature",
                            "properties": {"stroke": "#ff8800", "stroke-width": 2, "stroke-opacity": 1},
                            "geometry": LineString([point.coordinates for point in weighted_points]).__geo_interface__,
                            "id": 1,
                        },
                    ],
                }
            )
        )
        return Track(points=weighted_points, node_id=weighted_points[0].node_id)


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


def apply_common_sense_filters(track: Track, iri: str) -> Track | None:
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
        return None

    filtered_track = _filter_altitude_by_iri(_filter_teleportation(track), iri)
    return filtered_track


def _filter_teleportation(track: Track) -> Track:
    """
    Filter points that are likely the result of teleportation.

    :param track: The track to filter teleport anomalies from.
    :return: The filtered track. Points that are likely the result of teleportation have their weights assigned to 0.
    """
    from logging import getLogger

    from geoalchemy2.functions import ST_Distance

    logger = getLogger(__name__)

    for i in range(1, len(track.points)):
        # get the current and previous points
        current_point = track.points[i]
        prev_point = track.points[i - 1]

        time_delta = current_point.detection_time - prev_point.detection_time
        distance: float = ST_Distance(current_point.location, prev_point.location).scalar()
        relative_velocity = distance / time_delta.total_seconds() if time_delta.total_seconds() > 0 else 0

        # If the distance between two points is very large and the time between them is very small, it's likely that the
        # object teleported. We don't want to include these points in the track, but we'll still keep them in the
        # sensemaking db.
        distance_exceeded = distance > SETTINGS.distance_threshold_meters
        time_within_threshold = time_delta.total_seconds() < SETTINGS.time_threshold_seconds
        velocity_within_threshold = 0 < relative_velocity < SETTINGS.relative_velocity_threshold_meters_per_second
        if (distance_exceeded and time_within_threshold) or velocity_within_threshold:
            logger.debug(
                "Removing point %s from track %s due to teleportation: distance=%s, time_delta=%s",
                current_point.observation_id,
                track.node_id,
                distance,
                time_delta,
            )
            track.points[i].weight *= 0
    return track


def _filter_altitude_by_iri(track: Track, iri: str) -> Track:
    """
    Filter out points that drastically deviate in elevation.

    :param track: The track to filter altitude discrepancies from.
    :return: The filtered track.
    """
    from logging import getLogger
    logger = getLogger(__name__)

    if 'aircraft' not in iri.lower():
        logger.debug("Skipping altitude filtering for non-aircraft track.")
        return track

    for i in range(1, len(track.points)):
        # get the current and previous points
        current_point = track.points[i]
        prev_point = track.points[i - 1]
        # if either point doesn't have an altitude, skip this filter
        if current_point.altitude is None or prev_point.altitude is None:
            logger.debug("Skipping altitude filter for point %s", current_point.observation_id)
            continue

        # Check if the altitude is negative, zero, or exceeds the maximum altitude threshold.
        if current_point.altitude < 0:
            logger.debug("Removing point %s from track %s due to negative altitude: altitude=%s",
                         current_point.observation_id, track.node_id, current_point.altitude)
            track.points[i].weight *= 0
            continue
        elif current_point.altitude > SETTINGS.max_altitude_meters:
            logger.debug("Removing point %s from track %s due to altitude exceeding maximum: altitude=%s",
                         current_point.observation_id, track.node_id, current_point.altitude)
            track.points[i].weight *= 0

        # Check if the change in altitude between this point and the previous is large.
        if abs(current_point.altitude - prev_point.altitude) > SETTINGS.altitude_deviation_threshold_meters:
            logger.debug(
                "Removing point %s from track %s due to altitude discrepancy: altitude=%s, prev_altitude=%s",
                current_point.observation_id,
                track.node_id,
                current_point.altitude,
                prev_point.altitude,
            )
            track.points[i].weight *= 0

    return track
