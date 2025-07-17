import zipfile

from fastkml import kml
from fastkml.kml import Document, Folder, Placemark
from shapely.geometry import mapping


class KMLReader:
    """
    Helper class used to read .kml and .kmz type files for areas of interest
    """

    def extract_placemarks(self, feature):
        """
        Recursive helper function to extract geo data to then be extracted into geoJSON type objects

        :param feature: The feature from which geo data will be extracted
        :return: extracted geo data
        """
        extracted = []
        if isinstance(feature, Placemark):
            geom = feature.geometry
            geojson_feature = {
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": {"name": feature.name, "description": feature.description},
            }
            extracted.append(geojson_feature)

        elif isinstance(feature, (Document, Folder)):
            for sub_feature in feature.features:
                extracted.extend(self.extract_placemarks(sub_feature))

        return extracted

    def parse_kml_file(self, file_path: str):
        """
        Function used to parse through a .kml file and grab its necessary geo data

        :param file_path: The file path of a file which is being parsed to extract data
        :return: geojson type features
        """
        with open(file_path, "rb") as f:
            doc = f.read()

        k = kml.KML()
        k.from_string(doc.decode("utf-8"))
        features = []

        for feature in k.features:
            features.extend(self.extract_placemarks(feature))

        return features

    def parse_kmz_file(self, file_path: str):
        """
        Function used to parse through a .kmz zip file and grab its necessary geo data
        from the kml file within it

        :param file_path: The file path of a file which is being parsed to extract data
        :return: geojson type features
        """
        with zipfile.ZipFile(file_path, "r") as zf:
            kml_filename = next((name for name in zf.namelist() if name.endswith(".kml")), None)
            if not kml_filename:
                raise ValueError("No KML file found inside KMZ archive")

            with zf.open(kml_filename) as kml_file:
                doc = kml_file.read()

        k = kml.KML()
        k.from_string(doc.decode("utf-8"))
        features = []

        for feature in k.features:
            features.extend(self.extract_placemarks(feature))

        return features
