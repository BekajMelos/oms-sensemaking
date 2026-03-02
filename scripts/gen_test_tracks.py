import json
import math
import random

import numpy as np
from scipy.interpolate import CubicSpline


class AircraftPathGenerator:
    def __init__(self, num_points=100):
        """
        Initializes the path generator.

        :param num_points: Number of points in each generated path.
        """
        self.num_points = num_points
        # Typical cruising altitude (in feet) for commercial airliners
        self.cruise_altitude = 35000

    def generate_realistic_path(self):
        """
        Generates a realistic aircraft path with smoother transitions.

        :return: Dictionary representing the path in GeoJSON format.
        """
        start_lon = random.uniform(-180.0, 180.0)
        start_lat = random.uniform(-90.0, 90.0)

        path = {"type": "LineString", "coordinates": []}

        current_lon, current_lat = start_lon, start_lat
        current_heading = random.uniform(0, 2 * math.pi)  # Initial heading in radians

        change_direction_probability = 0.1
        lons, lats = [current_lon], [current_lat]

        for _ in range(self.num_points):
            if random.random() < change_direction_probability:
                current_heading += random.uniform(-math.pi / 2, math.pi / 2)  # Small change to heading

            delta_distance = random.uniform(0.5, 1.5)  # Distance between points
            current_lon += delta_distance * math.cos(current_heading)
            current_lat += delta_distance * math.sin(current_heading)

            lons.append(current_lon)
            lats.append(current_lat)
            path["coordinates"].append([current_lon, current_lat, self.cruise_altitude])

        path["coordinates"] = self.smooth_path(lons, lats)
        return path

    def smooth_path(self, lons, lats):
        """
        Applies cubic spline interpolation to create a smoother path.

        :param lons: List of longitudes.
        :param lats: List of latitudes.
        :return: Smoothed list of coordinates with altitude.
        """
        # Indices corresponding to each point
        indices = np.arange(len(lons))

        # Create cubic spline interpolators for longitude and latitude
        cs_lon = CubicSpline(indices, lons)
        cs_lat = CubicSpline(indices, lats)

        # Generate a finer set of indices for smoother interpolation
        fine_indices = np.linspace(0, len(lons) - 1, num=5 * len(lons))

        # Apply the spline interpolators to get smoothed coordinates
        smoothed_lons = cs_lon(fine_indices)
        smoothed_lats = cs_lat(fine_indices)

        # Construct the list of smoothed coordinates with constant altitude
        smoothed_coordinates = [
            [lon, lat, self.cruise_altitude] for lon, lat in zip(smoothed_lons, smoothed_lats, strict=True)
        ]

        return smoothed_coordinates

    def create_aircraft_paths(self, num_sets):
        """
        Creates multiple sets of realistic aircraft paths.

        :param num_sets: Number of path sets to generate.
        :return: List of dictionaries representing each path.
        """
        # Generate specified number of path sets
        return [self.generate_realistic_path() for _ in range(num_sets)]

    @staticmethod
    def write_to_geojson_file(file_name, aircraft_paths):
        """
        Writes the aircraft paths to a GeoJSON file.

        :param file_name: Name of the output GeoJSON file.
        :param aircraft_paths: List of path dictionaries.
        """
        # Initialize GeoJSON structure for feature collection
        geojson_data = {"type": "FeatureCollection", "features": []}

        # Create a GeoJSON feature for each aircraft path
        for i, path in enumerate(aircraft_paths):
            feature = {"type": "Feature", "properties": {"id": i}, "geometry": path}
            geojson_data["features"].append(feature)

        # Write the GeoJSON data to a file with indentation for readability
        with open(file_name, "w") as f:
            json.dump(geojson_data, f, indent=2)

    def generate_and_save_paths(self, num_sets):
        """
        Generates and writes aircraft paths to a GeoJSON file.

        :param num_sets: Number of sets of paths to generate.
        """
        # Generate specified number of path sets
        aircraft_paths = self.create_aircraft_paths(num_sets)

        # Save generated paths to a GeoJSON file
        self.write_to_geojson_file("aircraft_paths.geojson", aircraft_paths)

        # Print confirmation message
        print(f"Generated {num_sets} aircraft path sets in 'aircraft_paths.geojson'.")


# Example usage:
if __name__ == "__main__":
    generator = AircraftPathGenerator(num_points=50)  # Specify number of points per path
    num_sets = 1  # Number of sets to generate
    generator.generate_and_save_paths(num_sets)
