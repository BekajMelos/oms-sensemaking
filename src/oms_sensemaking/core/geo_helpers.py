"""Module with geo helper functions"""

import json

from geopy.distance import geodesic
from geopy.point import Point


def features_list_from_geojson(path_to_geojson_file: str):
    """Load features from a geojson file"""
    with open(path_to_geojson_file, "r") as file:
        features = json.load(file)["features"]
    return features


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
        points.append((destination.longitude, destination.latitude))
    return points
