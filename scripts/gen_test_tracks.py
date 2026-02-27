import json
import random


class AircraftPathGenerator:
    def __init__(self, num_points=100):
        self.num_points = num_points
        # Typical cruising altitude (in feet) for commercial airliners
        self.cruise_altitude = 35000

    def generate_realistic_path(self):
        """
        Generates a realistic aircraft path.

        :return: Dictionary with 'type' and 'coordinates'.
        """
        start_lon = random.uniform(-180.0, 180.0)  # Full range for longitude
        start_lat = random.uniform(-90.0, 90.0)  # Full range for latitude

        path = {"type": "LineString", "coordinates": []}

        current_lon, current_lat = start_lon, start_lat

        for _ in range(self.num_points):
            # Smoother movement: smaller increments with more frequent direction changes
            delta_lon = random.uniform(0.05, 0.2) * random.choice([-1, 1])
            delta_lat = random.uniform(0.05, 0.2) * random.choice([-1, 1])

            # Update coordinates
            current_lon += delta_lon
            current_lat += delta_lat

            # Append coordinate with altitude
            path["coordinates"].append([current_lon, current_lat, self.cruise_altitude])

        return path

    def create_aircraft_paths(self, num_sets):
        """
        Creates multiple sets of realistic aircraft paths.

        :param num_sets: Number of path sets to generate.
        :return: List of path dictionaries.
        """
        return [self.generate_realistic_path() for _ in range(num_sets)]

    @staticmethod
    def write_to_geojson_file(file_name, aircraft_paths):
        """
        Writes the aircraft paths to a GeoJSON file.

        :param file_name: Name of the output GeoJSON file.
        :param aircraft_paths: List of path dictionaries.
        """
        geojson_data = {"type": "FeatureCollection", "features": []}

        for i, path in enumerate(aircraft_paths):
            feature = {"type": "Feature", "properties": {"id": i}, "geometry": path}
            geojson_data["features"].append(feature)

        with open(file_name, "w") as f:
            json.dump(geojson_data, f, indent=2)

    def generate_and_save_paths(self, num_sets):
        """
        Generates and writes aircraft paths to a GeoJSON file.

        :param num_sets: Number of sets of paths to generate.
        """
        aircraft_paths = self.create_aircraft_paths(num_sets)
        self.write_to_geojson_file("aircraft_paths.geojson", aircraft_paths)
        print(f"Generated {num_sets} aircraft path sets in 'aircraft_paths.geojson'.")


# Example usage:
if __name__ == "__main__":
    generator = AircraftPathGenerator(num_points=15)  # Specify number of points per path
    num_sets = 3  # Number of sets to generate
    generator.generate_and_save_paths(num_sets)
