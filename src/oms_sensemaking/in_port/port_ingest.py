import json
import logging
from datetime import datetime

from geoalchemy2.shape import from_shape
from shapely.geometry import shape

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.models.port_ingest import AggressorPort

LOGGER: logging.Logger = logging.getLogger(__name__)


def check_ports() -> bool:
    """
    Check to see if Aggressor port data in the table exists.

    :return: True if data already exists in the database, False otherwise.
    """

    with db_session() as db:
        rows_with_points = db.query(AggressorPort).filter(AggressorPort.node_id.is_not(None)).count()

        return rows_with_points != 0


def import_aggressor_port_data() -> bool:
    """
    Run through the observations stored in ./data/observations.json representing the set of ports in the world and
    store those data points as new AggressorPort entries in the appropriate table in the database

    :return: True if the import was successful or the data already exists in the database, False otherwise.
    """

    # True if already exists in the database
    if check_ports():
        LOGGER.info("Detected aggressor port data in database.")
        return True

    with db_session() as db:
        try:
            with open(SETTINGS.aggressor_ports_json_file_path, "r") as f:
                data = json.load(f)

            for feature in data:
                geom_obj = shape(json.loads(feature["geometry"]))
                capco = feature["capco"]
                class_iri = feature["classIri"]
                confidence = feature["confidence"]
                node_id = feature["nodeId"]
                start_time = datetime.fromisoformat(feature["startTime"])
                end_time = datetime.fromisoformat(feature["endTime"])
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
