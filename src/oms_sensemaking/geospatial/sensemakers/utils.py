from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from geoalchemy2.shape import to_shape

from oms_sensemaking.models.geo import Point, Track


@dataclass
class Colocation:
    """For CotravelService use, a Colocation stores the data for two tracks' intersection."""

    track1_node_id: UUID
    track2_node_id: UUID
    track1_id: UUID
    track2_id: UUID
    point: Point
    db_point: Point

    def __str__(self):
        loc1 = to_shape(self.point.location)
        loc2 = to_shape(self.db_point.location)
        return f"Colocation: {loc1} at {self.point.detection_time} and {loc2} at {self.db_point.detection_time}"


def extract_coordinate_track(track: Track, start_time: datetime, end_time: datetime) -> list[Point]:
    """
    Return points within provided time bounds.

    :param track: Track to extract points from
    :param start_time: earliest point timestamp
    :param end_time: latest point timestamp
    :return: List of valid points
    """
    points = []
    for point in track.points:
        if start_time <= point.detection_time <= end_time:
            points.append(point)
    return points
