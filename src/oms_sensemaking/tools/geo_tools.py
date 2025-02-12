from typing import Any

from shapely import Point
from shapely.geometry import shape


def is_point_in_region(point: dict[str, Any], region: dict[str, Any]):
    """
    Determines if a point is located in a region, both in geojson format
    """
    point_coordinates = point["coordinates"]
    shapely_region = shape(region)
    shapely_point = Point(point_coordinates)

    return shapely_region.contains(shapely_point)
