"""Geospatial Track Weavers."""

import itertools
from abc import ABC, abstractmethod
from datetime import UTC, datetime

import numpy
from filterpy.common.discretization import Q_discrete_white_noise
from filterpy.kalman import ExtendedKalmanFilter
from oms_sdk.generated.generated_graphql_client import Confidence

from oms_sensemaking.clients.instances import aac_client, db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.models.geo import Point, Track, weighted_average


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
            acm=aac_client.get_acm_rollup([point.acm for point in points]),
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
                acm_rollup = aac_client.get_acm_rollup([{"ACM": point.acm} for point in bin_points])
                point_dict = {
                    "node_id": bin_points[0].node_id,
                    "node_version": bin_points[0].node_version,
                    "source_id": bin_points[0].source_id,
                    "observation_id": bin_points[0].observation_id,
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
                point_dict["location"] = f"Point({round(lon, 5)} {round(lat, 5)})"
                # Find the Confidence enum member mapped to the lowest weight among parent Point confidences
                confidence_level = Confidence.UNKNOWN
                confidence_val = min(confidence_map[p.observation_confidence] for p in bin_points)
                for confidence, weight in confidence_map.items():
                    if weight == confidence_val:
                        confidence_level = confidence
                point_dict["observation_confidence"] = confidence_level
                # Average parent Point weights to get new Point weight [0.0 - 1.0]
                point_dict["weight"] = sum(point.weight for point in bin_points) / len(bin_points)
                weighted_point, _ = Point.get_or_create(db, defaults=None, **point_dict)
                weighted_points.append(weighted_point)
        return Track(
            points=weighted_points,
            node_id=weighted_points[0].node_id,
            algorithm=self.algorithm,
            observation_ids={p.observation_id for p in points},  # type: ignore
            acm=aac_client.get_acm_rollup([point.acm for point in weighted_points]),
        )


class ExtendedKalmanTrackWeaver(TrackWeaverBase):
    """
    A track weaver that uses an Extended Kalman Filter to smooth Points. Points are converted into ECEF
    coordinates for the Kalman Filter, then converted back to lat/lon for the final Point.
    """

    def __init__(self) -> None:
        """Create a new instance of ExtendedKalmanTrackWeaver."""
        super().__init__()

        self.version = (1, 1, 0)
        self.name = self.__class__.__name__
        self.process_noise = 0.01
        self.measurement_noise = 0.001
        self.dimensions = 2
        self.ekf = ExtendedKalmanFilter(dim_x=self.dimensions, dim_z=self.dimensions)
        self.dt: float = 0.0
        self.algorithm = "extended_kalman_filter"

    def _init_ekf(self, point: Point):
        """
        Initialize the Kalman filter with the first Point in the list.
        :param point: The first Point in the list.
        :return: A Kalman filter object. Used to smooth the Points.
        """
        self.ekf.x = numpy.array([[point.coordinates[0]], [point.coordinates[1]]])  # type: ignore
        self.ekf.F = numpy.eye(self.dimensions)  # State transition matrix
        self.ekf.P = numpy.eye(self.dimensions)
        self.ekf.R = numpy.eye(self.dimensions) * self.measurement_noise  # Measurement noise
        self.ekf.Q = Q_discrete_white_noise(dim=self.dimensions, dt=self.dt, var=self.process_noise)  # Process noise

    def process_point(self, point: Point) -> dict:
        """
        Process a Point through the Kalman filter.
        :param point: The Point to process.
        :return: A dictionary with the smoothed Point attributes.
        """
        weight = point.weight

        self.ekf.predict()
        measurement = numpy.array([[point.coordinates[0]], [point.coordinates[1]]])  # type: ignore

        # Update the Kalman filter with the measurement
        self.ekf.Q = Q_discrete_white_noise(dim=self.dimensions, dt=self.dt, var=self.process_noise)
        self.ekf.R = (
            (numpy.eye(self.dimensions) * self.measurement_noise) / weight
            if weight > 0
            else numpy.eye(self.dimensions) / self.measurement_noise**6
        )

        self.ekf.update(measurement, HJacobian=lambda _: numpy.eye(self.dimensions), Hx=lambda x: x[: self.dimensions])
        smoothed_position = self.ekf.x[: self.dimensions]

        return {
            "node_id": point.node_id,
            "node_version": point.node_version,
            "source_id": point.source_id,
            "observation_id": point.observation_id,
            "observation_version": point.observation_version,
            "altitude": point.altitude,
            "detection_time": point.detection_time,
            "location": f"Point({round(smoothed_position[0, 0], 5)} {round(smoothed_position[1, 0], 5)})",
            "acm": point.acm,
            "observation_confidence": point.observation_confidence,
            "weight": point.weight,
        }

    def execute(self, points: list[Point]) -> Track:
        points.sort(key=lambda x: x.detection_time)
        self._init_ekf(points[0])
        smoothed_points: list[Point] = [points[0]]

        with db_session() as db:
            db.expire_on_commit = False
            for point in points[1:]:
                self.dt = (point.detection_time - smoothed_points[-1].detection_time).total_seconds()
                smoothed_point, _ = Point.get_or_create(db, defaults=None, **self.process_point(point))
                smoothed_points.append(smoothed_point)

        grouped_by_confidence: dict[Confidence, list[Point]] = {}
        for point in points:
            if point.observation_confidence not in grouped_by_confidence:
                grouped_by_confidence[point.observation_confidence] = []
            grouped_by_confidence[point.observation_confidence].append(point)

        return Track(
            points=smoothed_points,
            node_id=smoothed_points[0].node_id,
            algorithm=self.algorithm,
            observation_ids={p.observation_id for p in points},  # type: ignore
            acm=aac_client.get_acm_rollup([point.acm for point in smoothed_points]),
        )
