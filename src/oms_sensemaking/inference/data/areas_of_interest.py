import json


def features_list_from_geojson(path_to_geojson_file: str):
    with open(path_to_geojson_file, 'r') as file:
        features = json.load(file)["features"]
    return features
