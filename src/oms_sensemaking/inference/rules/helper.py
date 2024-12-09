import math


class Helper():
    def compare_geo(self, geojson1, geojson2):
        geo_coordinates_1 = geojson1["features"][0]["geometry"]["coordinates"]
        geo_coordinates_2 = geojson2["features"][0]["geometry"]["coordinates"]

        # Radius of Earth in km
        radius = 6371.0

        # Convert latitude and longitude from degrees to radians
        lat1, lon1 = map(math.radians, geo_coordinates_1)
        lat2, lon2 = map(math.radians, geo_coordinates_2)

        # Differences in coordinates
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = radius * c

        # Could be an ENUM or something so it's not hardcoded
        if(distance < 2000):
            return "Yes"
        else:
            return "No"
