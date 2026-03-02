import argparse
import json
import math
import random

import numpy as np
from scipy.interpolate import CubicSpline


class AircraftPathGenerator:
    def __init__(self, min_points=25, max_points=250):
        """
        Initializes the path generator with a specified range for number of points.

        :param min_points: Minimum number of points in each generated path.
        :param max_points: Maximum number of points in each generated path.
        """
        # Set minimum and maximum number of points per path
        self.min_points = min_points
        self.max_points = max_points

        # Define a typical cruising altitude for commercial airliners (in feet)
        self.cruise_altitude = 35000

    def generate_realistic_path(self):
        """
        Generates a realistic aircraft path.

        :return: Dictionary representing the path in GeoJSON format.
        """
        # Determine a random number of points within the specified range
        num_points = random.randint(self.min_points, self.max_points)

        # Generate random starting coordinates for longitude and latitude
        start_lon = random.uniform(-180.0, 180.0)
        start_lat = random.uniform(-90.0, 90.0)

        # Initialize a path as a GeoJSON LineString object with an empty list of coordinates
        path = {"type": "LineString", "coordinates": []}

        current_lon, current_lat = start_lon, start_lat

        # Random initial heading in radians
        current_heading = random.uniform(0, 2 * math.pi)

        change_direction_probability = 0.1  # Initial probability of changing direction

        lons, lats = [current_lon], [current_lat]

        for i in range(num_points):
            progress_ratio = i / num_points
            # Gradually increase the probability of changing direction as path progresses
            change_direction_probability = 0.1 + 0.9 * progress_ratio

            if random.random() < change_direction_probability:
                # Adjust heading randomly within a certain range for more realistic paths
                current_heading += random.uniform(-math.pi / 2, math.pi / 2)

            delta_distance = random.uniform(0.5, 1.5)  # Random distance between points

            # Update longitude and latitude based on the current heading
            current_lon += delta_distance * math.cos(current_heading)
            current_lat += delta_distance * math.sin(current_heading)

            lons.append(current_lon)
            lats.append(current_lat)

            # Append the new coordinate with altitude to the path
            path["coordinates"].append([current_lon, current_lat, self.cruise_altitude])

        # Smooth the path using cubic spline interpolation before finalizing it
        path["coordinates"] = self.smooth_path(lons, lats)

        return path

    def smooth_path(self, lons, lats):
        """
        Applies cubic spline interpolation to create a smoother path.

        :param lons: List of longitudes.
        :param lats: List of latitudes.
        :return: Smoothed list of coordinates with altitude.
        """
        # Create an array of indices corresponding to each longitude and latitude
        indices = np.arange(len(lons))

        # Perform cubic spline interpolation on the longitude and latitude arrays
        cs_lon = CubicSpline(indices, lons)
        cs_lat = CubicSpline(indices, lats)

        # Define a finer grid for smoother interpolation results
        fine_indices = np.linspace(0, len(lons) - 1, num=5 * len(lons))

        # Generate smoothed longitude and latitude values
        smoothed_lons = cs_lon(fine_indices)
        smoothed_lats = cs_lat(fine_indices)

        # Combine the smoothed coordinates with altitude to form a complete path
        smoothed_coordinates = [
            [lon, lat, self.cruise_altitude] for lon, lat in zip(smoothed_lons, smoothed_lats, strict=True)
        ]

        return smoothed_coordinates

    def create_aircraft_paths(self, num_sets):
        """
        Creates multiple point sets of realistic aircraft paths.

        :param num_sets: Number of point sets to generate.
        :return: List of dictionaries representing each path.
        """
        # Generate the specified number of path sets
        return [self.generate_realistic_path() for _ in range(num_sets)]

    @staticmethod
    def write_to_geojson_file(file_name, aircraft_paths):
        """
        Writes the aircraft paths to a GeoJSON file.

        :param file_name: Name of the output GeoJSON file.
        :param aircraft_paths: List of path dictionaries.
        """
        # Initialize a GeoJSON FeatureCollection
        geojson_data = {"type": "FeatureCollection", "features": []}

        for i, path in enumerate(aircraft_paths):
            # Create a feature for each path with an ID and geometry
            feature = {"type": "Feature", "properties": {"id": i}, "geometry": path}
            geojson_data["features"].append(feature)

        # Write the GeoJSON data to a file with pretty printing
        with open(file_name, "w") as f:
            json.dump(geojson_data, f, indent=2)

    def generate_and_save_paths(self, num_sets):
        """
        Generates and writes aircraft paths to a GeoJSON file.

        :param num_sets: Number of sets of points to generate.
        """
        # Generate multiple path sets
        aircraft_paths = self.create_aircraft_paths(num_sets)

        # Write the generated paths to a specified file
        self.write_to_geojson_file("aircraft_paths.geojson", aircraft_paths)

        print(f"Generated {num_sets} aircraft path point sets in 'aircraft_paths.geojson'.")


def parse_arguments():
    """
    Parses command-line arguments.

    :return: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Generate realistic aircraft paths.")
    parser.add_argument(
        "--num_sets",
        type=int,
        default=1,  # Default value for num_sets
        help="Number of sets of points to generate.",
    )
    return parser.parse_args()


# Example usage:
if __name__ == "__main__":
    args = parse_arguments()  # Parse command-line arguments

    generator = AircraftPathGenerator(min_points=50, max_points=150)  # Range for number of points per path
    num_sets = args.num_sets  # Number of sets to generate from command line argument
    generator.generate_and_save_paths(num_sets)
