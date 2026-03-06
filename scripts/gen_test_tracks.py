import argparse
import json
import math
import random
from datetime import datetime, timedelta

import numpy as np
from scipy.interpolate import CubicSpline


class AircraftPathGenerator:
    def __init__(self, min_points=25, max_points=250):
        # Set minimum and maximum number of path points
        self.min_points = min_points
        self.max_points = max_points
        # Define a constant cruise altitude for the aircraft paths
        self.cruise_altitude = 35000
        # Initialize starting detection time to January 1, 2026 at midnight
        self.initial_detection_time = datetime(2026, 1, 1)

    def generate_realistic_path(self):
        # Randomly determine number of points in the path
        num_points = random.randint(self.min_points, self.max_points)
        # Generate a random starting longitude and latitude for the aircraft
        start_lon = random.uniform(-180.0, 180.0)
        start_lat = random.uniform(-90.0, 90.0)

        # Initialize an empty path with type 'LineString'
        path = {"type": "LineString", "coordinates": []}
        current_lon, current_lat = start_lon, start_lat
        # Random initial heading for the aircraft in radians
        current_heading = random.uniform(0, 2 * math.pi)

        # Lists to store longitude and latitude values
        lons, lats = [current_lon], [current_lat]

        # Start detection time from initial_detection_time
        detection_time = self.initial_detection_time

        for i in range(num_points):
            # Calculate progress ratio to adjust change direction probability over the path
            progress_ratio = i / num_points
            change_direction_probability = 0.1 + 0.9 * progress_ratio

            # Randomly decide if the aircraft changes heading
            if random.random() < change_direction_probability:
                current_heading += random.uniform(-math.pi / 2, math.pi / 2)

            # Determine the distance to move in the current direction
            delta_distance = random.uniform(0.5, 1.5)
            current_lon += delta_distance * math.cos(current_heading)
            current_lat += delta_distance * math.sin(current_heading)

            lons.append(current_lon)
            lats.append(current_lat)

            # Append coordinates with altitude to the path
            path["coordinates"].append([current_lon, current_lat, self.cruise_altitude])

            # Increment detection_time by 30 seconds for each point
            detection_time += timedelta(seconds=30)

        # Smooth the generated path using cubic spline interpolation
        smoothed_coords = self.smooth_path(lons, lats)

        # Assign times directly to the smoothed coordinates
        path["coordinates"] = [
            (lon, lat, dt.isoformat())
            for (lon, lat), dt in zip(smoothed_coords, self.generate_detection_times(num_points * 5), strict=False)
        ]

        return path

    def smooth_path(self, lons, lats):
        # Create an array of indices representing the original points
        indices = np.arange(len(lons))
        # Perform cubic spline interpolation for longitude and latitude
        cs_lon = CubicSpline(indices, lons)
        cs_lat = CubicSpline(indices, lats)
        # Generate fine-grained indices to create a smoother path
        fine_indices = np.linspace(0, len(lons) - 1, num=5 * len(lons))

        # Interpolate using the cubic splines
        smoothed_lons = cs_lon(fine_indices)
        smoothed_lats = cs_lat(fine_indices)

        return list(zip(smoothed_lons, smoothed_lats, strict=True))

    def generate_detection_times(self, num_points):
        # Generate a series of detection times starting from initial time
        initial_time = self.initial_detection_time + timedelta(seconds=int(0 * 30))
        return [initial_time + timedelta(seconds=i * 30) for i in range(num_points)]

    def create_aircraft_paths(self, num_paths):
        # Create multiple sets of aircraft paths
        return [self.generate_realistic_path() for _ in range(num_paths)]

    @staticmethod
    def write_to_geojson_file(file_name, aircraft_paths):
        # Prepare the GeoJSON structure for the generated paths
        geojson_data = {"type": "FeatureCollection", "features": []}

        for i, path in enumerate(aircraft_paths):
            feature = {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [coord[:2] for coord in path["coordinates"]]},
                "properties": {"id": i, "timestamps": [coord[2] for coord in path["coordinates"]]},
            }
            geojson_data["features"].append(feature)

        # Write the GeoJSON data to a file
        with open(file_name, "w") as f:
            json.dump(geojson_data, f, indent=2)

    def generate_and_save_paths(self, num_paths):
        # Generate and save specified number of aircraft path sets
        aircraft_paths = self.create_aircraft_paths(num_paths)
        self.write_to_geojson_file("aircraft_paths.geojson", aircraft_paths)
        print(f"Generated {num_paths} aircraft path point sets in 'aircraft_paths.geojson'.")


def parse_arguments():
    # Parse command line arguments to determine number of path sets
    parser = argparse.ArgumentParser(description="Generate aircraft paths.")
    parser.add_argument(
        "--num_paths",
        type=int,
        default=1,
        help="Number of paths to generate",
    )
    parser.add_argument(
        "--min_points_pre_smooth",
        type=int,
        default=10,
        help="Minimum number of points in paths before smoothing",
    )
    parser.add_argument(
        "--max_points_pre_smooth",
        type=int,
        default=100,
        help="Maximum number of points in paths before smoothing",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    generator = AircraftPathGenerator(min_points=args.min_points_pre_smooth, max_points=args.max_points_pre_smooth)
    generator.generate_and_save_paths(args.num_paths)
