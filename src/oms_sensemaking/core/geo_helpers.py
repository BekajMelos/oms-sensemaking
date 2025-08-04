"""Module with geo helper functions"""

import json
import os

from geopy.distance import geodesic
from geopy.point import Point

from oms_sensemaking.core.kml_reader import KMLReader


def gather_area_of_interest_data(path_to_aoi_data: str):
    """
    A function that gathers all of the data from the individual
    geoJSON files found in the specified directory.

    :return: An array containing a list of dictionarys
    """
    areas_of_interest = []
    kml_reader = KMLReader()

    for file in os.listdir(path_to_aoi_data):
        file_path = os.path.join(path_to_aoi_data, file)

        if os.path.isfile(file_path):
            file_lower = file.lower()
            if file_lower.endswith(".json"):
                with open(file_path, "r") as f:
                    data = json.load(f)
                    areas_of_interest.append(data)
            elif file_lower.endswith(".kml"):
                features = kml_reader.parse_kml_file(file_path)
                areas_of_interest.extend(features)
            elif file_lower.endswith(".kmz"):
                features = kml_reader.parse_kmz_file(file_path)
                areas_of_interest.extend(features)

    return areas_of_interest


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
