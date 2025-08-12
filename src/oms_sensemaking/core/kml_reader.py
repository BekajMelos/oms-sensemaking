import logging
import zipfile

from fastkml import kml
from fastkml.kml import Placemark
from fastkml.utils import find_all
from shapely.geometry import mapping

LOGGER: logging.Logger = logging.getLogger(__name__)


class KMLReader:
    """
    Helper class used to read .kml and .kmz type files for areas of interest
    """

    def extract_placemarks(self, kml_obj):
        """
        Recursive helper function to extract geo data to then be extracted into geoJSON type objects

        :param feature: The feature from which geo data will be extracted
        :return: extracted geo data
        """
        extracted = []
        placemarks = list(find_all(kml_obj, of_type=Placemark))
        for placemark in placemarks:
            geom = placemark.geometry
            try:
                mapped_geometry = mapping(geom)
            except Exception as e:
                LOGGER.warning(f"Skipping invalid geometry in placemark: {e}")
                continue
            geojson_feature = {
                "type": "Feature",
                "geometry": mapped_geometry,
                "properties": {"name": placemark.name, "description": placemark.description},
            }
            extracted.append(geojson_feature)
        return extracted

    def parse_kml_file(self, file_path: str):
        """
        Function used to parse through a .kml file and grab its necessary geo data

        :param file_path: The file path of a file which is being parsed to extract data
        :return: geojson type features
        """
        try:
            k = kml.KML.parse(file_path)
            return self.extract_placemarks(k)
        except Exception as e:
            LOGGER.error(f"Unexpected error when parsing KML file: {e}")
            return []

    def parse_kmz_file(self, file_path: str):
        """
        Function used to parse through a .kmz zip file and grab its necessary geo data
        from the kml file within it

        :param file_path: The file path of a file which is being parsed to extract data
        :return: geojson type features
        """
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                kml_filename = next((name for name in zf.namelist() if name.endswith(".kml")), None)
                if not kml_filename:
                    raise ValueError("No KML file found inside KMZ archive")

                with zf.open(kml_filename) as kml_file:
                    k = kml.KML.parse(kml_file)

            return self.extract_placemarks(k)
        except zipfile.BadZipFile as e:
            LOGGER.error(f"Invalid KMZ file {e}")
        except Exception as e:
            LOGGER.error(f"Unexpected error when parsing KMZ file: {e}")
        return []
