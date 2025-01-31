from typing import Any

from shapely import Point, Polygon


def is_point_in_polygon(point: dict[str, Any], polygon: dict[str, Any]):
    """
    Determines if inputted point is located in polygon
    """  # add type annot
    point_coordinates = point["coordinates"]
    polygon_coordinates = polygon["coordinates"][0]
    polygon = Polygon(polygon_coordinates)
    point = Point(point_coordinates)

    return polygon.contains(point)
