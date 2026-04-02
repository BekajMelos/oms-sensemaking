import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Union

from geoalchemy2.shape import from_shape
from shapely.geometry import Point, shape

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.models.port_ingest import AggressorPort

LOGGER: logging.Logger = logging.getLogger(__name__)


@dataclass
class Geometry:
    type: str
    geometry: Dict[str, Union[str, List[float]]]


class AggressorPortType:
    id: str
    capco: str
    tags: str
    labels: str
    class_iri: str
    display_value: str
    confidence: str
    source_id: str
    node_id: str
    geometry: Geometry
    start_time: str
    end_time: str


def check_ports() -> bool:
    """
    Helper function to check to see if COCOM data in the table exists.

    :return: True if data already exists in the database, False otherwise.
    """

    with db_session() as db:
        rows_with_points = db.query(AggressorPort).filter(AggressorPort.node_id.is_not(None)).count()

        return rows_with_points != 0


def import_aggressor_port_data() -> bool:
    """
    Import a GEOJSON file that represents the COCOM polygons on a map

    :return: True if the import was successful or the data already exists in the database, False otherwise.
    """

    # Check to see if data exists in the COCOMs table
    if check_ports():
        LOGGER.info("Detected COCOM data in database.")
        return True

    with db_session() as db:
        try:
            with open(SETTINGS.aggressor_ports_json_file_path, "r") as f:
                data: list[AggressorPortType] = json.load(f)

            for feature in data:
                geom_obj = shape(json.loads(feature["geometry"]))
                capco = feature["capco"]
                class_iri = feature["classIri"]
                confidence = feature["confidence"]
                node_id = feature["nodeId"]
                start_time = datetime.fromisoformat(feature["startTime"])
                end_time = datetime.fromisoformat(feature["endTime"])
                if not isinstance(geom_obj, Point):
                    geom_obj = Point([geom_obj])

                new_port = AggressorPort(
                    location=from_shape(geom_obj, srid=SETTINGS.srid),
                    capco=capco,
                    class_iri=class_iri,
                    confidence=confidence,
                    node_id=node_id,
                    start_time=start_time,
                    end_time=end_time,
                )
                db.add(new_port)

            db.commit()
            LOGGER.info("Importing of Aggressor Port data successful.")
            return True

        except Exception as e:
            db.rollback()
            LOGGER.error(f"Importing of Aggressor Port data failed: {e}")
            return False
