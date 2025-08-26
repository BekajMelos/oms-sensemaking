"""Module with geo helper functions"""

import json
import logging

from geopy.distance import geodesic
from geopy.point import Point

from oms_sensemaking.core.kml_reader import KMLReader

LOGGER: logging.Logger = logging.getLogger(__name__)


def gather_area_of_interest_data(paths_to_aoi_data: list[str]):
    """
    A function that gathers all of the data from the individual
    geoJSON files found in the specified directory.

    :return: An array containing a list of dictionarys
    """
    areas_of_interest: list[dict | None] = []
    kml_reader = KMLReader()
    for file_path in paths_to_aoi_data:
        try:
            if file_path.endswith(".json"):
                json_aois = get_aois_from_json(file_path)
                areas_of_interest.extend(json_aois)
            elif file_path.endswith(".kml"):
                features = kml_reader.parse_kml_file(file_path)
                areas_of_interest.extend(features)
            elif file_path.endswith(".kmz"):
                features = kml_reader.parse_kmz_file(file_path)
                areas_of_interest.extend(features)
            else:
                LOGGER.warning(f"Unsupported file type: {file_path}")
        except json.JSONDecodeError as e:
            LOGGER.error(f"Invalid json {file_path}: {e}")
    return areas_of_interest


def get_aois_from_json(file_path: str):
    aois = []
    with open(file_path, "r") as f:
        data = json.load(f)
        if data.get("type") == "FeatureCollection" and "features" in data:
            aois.extend([f for f in data["features"] if is_valid_geometry_type_json(f)])
        elif data.get("type") == "Feature" and is_valid_geometry_type_json(data):
            aois.append(data)
    return aois


def is_valid_geometry_type_json(feature: dict):
    geom = feature.get("geometry", {})
    return geom.get("type") in {"Polygon", "MultiPolygon"}


def generate_circle_points_geographical(center_lat, center_lon, radius_km, num_points=100):
    """
    Generates a list of (longitude, latitude) coordinates that form a circle
    around a given geographical point.

    Args:
        center_lat (float): The latitude of the circle's center.
        center_lon (float): The longitude of the circle's center.
        radius_km (float): The radius of the circle in kilometers.
        num_points (int): The number of points to generate for the circle.

    Returns:
        list: A list of tuples, where each tuple represents a (longitude, latitude)
              coordinate on the circle's circumference.
    """
    points = []
    center_point = Point(center_lat, center_lon)
    for i in range(num_points):
        bearing = 360 * i / num_points  # Bearing in degrees
        destination = geodesic(kilometers=radius_km).destination(center_point, bearing)
        points.append([destination.longitude, destination.latitude])
    if points:
        points.append(points[0])  # close the ring for a polygon
    return points
