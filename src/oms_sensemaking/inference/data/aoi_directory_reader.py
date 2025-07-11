import json
import os
from typing import Any

from oms_sensemaking.config import SETTINGS


class AreasOfInterestReader:
    """
    Gather all files from the areas of interest data directory which will be used
    to check if observations fall within the coordinates
    """

    def __init__(self):
        self.aoi_directory = SETTINGS.inference_incursion_areas_of_interest_path

    # maybe just add to the geo_helpers.py file dont need a new class probably.
    # Refactor the features_list_.... method and rename it for better readability

    def gather_geo_json_data(self) -> list[dict[str, Any]]:
        geojson_objects = []

        for file in os.listdir(self.aoi_directory):
            file_path = os.path.join(self.aoi_directory, file)

            if os.path.isfile(file_path) and file.lower().endswith(".json"):
                with open(file_path, "r") as f:
                    data = json.load(f)
                    geojson_objects.append(data)

        return geojson_objects
