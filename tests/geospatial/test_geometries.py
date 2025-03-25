from datetime import datetime, timedelta, timezone
from uuid import uuid4

from dateutil.parser import isoparse
from oms_sdk.generated.generated_graphql_client import Confidence, ObservationObservation

from oms_sensemaking.models.geo import decompose_observation_geometry

#: The default ACM markings.
DEFAULT_ACM = {
    "version": "2.1.0",
    "classif": "U",
    "owner_prod": ["USA"],
    "atom_energy": [],
    "sar_id": [],
    "sci_ctrls": [],
    "disponly_to": [""],
    "dissem_ctrls": [],
    "non_ic": [],
    "rel_to": [],
    "fgi_open": [],
    "fgi_protect": [],
    "portion": "U",
    "banner": "UNCLASSIFIED",
    "dissem_countries": ["USA"],
    "accms": [],
    "macs": [],
    "oc_attribs": [{"orgs": [], "missions": [], "regions": []}],
    "f_clearance": ["u"],
    "f_sci_ctrls": [],
    "f_accms": [],
    "f_oc_org": [],
    "f_regions": [],
    "f_missions": [],
    "f_share": [],
    "f_sar_id": [],
    "f_atom_energy": [],
    "f_macs": [],
    "disp_only": "",
}


def test_single_point():
    start_time = isoparse("2022-12-01T00:20:14.000Z").replace(tzinfo=timezone.utc)
    end_time = start_time
    oms_obs = ObservationObservation(
        id=uuid4(),
        version=0,
        acm=DEFAULT_ACM,
        tags=["Aircraft", "UAL1598 ", "Location"],
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/GeospatialLocation",
        className="Geospatial Location",
        displayValue="ADSB-test-data-UAL1598",
        confidence=Confidence.HIGH,
        sourceId=uuid4(),
        nodeId=uuid4(),
        geometry={
            "type": "Point",
            "coordinates": [-77.04007, 38.85109],
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        },
        startTime=start_time.isoformat(),
        endTime=end_time.isoformat(),
    )
    timed_coords = decompose_observation_geometry(oms_obs)
    assert len(timed_coords) == 1
    assert timed_coords[0]["detection_time"] == start_time


def test_zero_time():
    start_time = isoparse("2022-12-01T00:20:14.000Z").replace(tzinfo=timezone.utc)
    end_time = start_time
    coordinates = [[-77.00000, 38.00000], [-77.00000, 38.50000], [-77.00000, 39.00000]]
    oms_obs = ObservationObservation(
        id=uuid4(),
        version=0,
        acm=DEFAULT_ACM,
        tags=["Aircraft", "UAL1598 ", "Location"],
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/GeospatialLocation",
        className="Geospatial Location",
        displayValue="ADSB-test-data-UAL1598",
        confidence=Confidence.HIGH,
        sourceId=uuid4(),
        nodeId=uuid4(),
        geometry={
            "type": "LineString",
            "coordinates": coordinates,
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        },
        startTime=start_time.isoformat(),
        endTime=end_time.isoformat(),
    )
    timed_coords = decompose_observation_geometry(oms_obs)
    assert [tc["coordinates"] for tc in timed_coords] == coordinates
    assert all(tc["detection_time"] == start_time for tc in timed_coords)


def test_zero_distance():
    start_time = isoparse("2022-12-01T00:20:14.000Z").replace(tzinfo=timezone.utc)
    end_time = start_time + timedelta(hours=1)
    coordinates = [[-77.00000, 38.00000], [-77.00000, 38.00000], [-77.00000, 38.00000]]
    oms_obs = ObservationObservation(
        id=uuid4(),
        version=0,
        acm=DEFAULT_ACM,
        tags=["Aircraft", "UAL1598 ", "Location"],
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/GeospatialLocation",
        className="Geospatial Location",
        displayValue="ADSB-test-data-UAL1598",
        confidence=Confidence.HIGH,
        sourceId=uuid4(),
        nodeId=uuid4(),
        geometry={
            "type": "LineString",
            "coordinates": coordinates,
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        },
        startTime=start_time.isoformat(),
        endTime=end_time.isoformat(),
    )
    timed_coords = decompose_observation_geometry(oms_obs)
    assert [tc["coordinates"] for tc in timed_coords] == coordinates
    assert [tc["detection_time"] for tc in timed_coords] == [start_time, start_time + timedelta(minutes=30), end_time]


def test_normal_linestring():
    start_time = isoparse("2022-12-01T00:20:14.000Z").replace(tzinfo=timezone.utc)
    end_time = start_time + timedelta(hours=1, minutes=30)
    coordinates = [[-77.00000, 38.00000], [-77.00000, 39.00000], [-77.00000, 39.50000]]
    oms_obs = ObservationObservation(
        id=uuid4(),
        version=0,
        acm=DEFAULT_ACM,
        tags=["Aircraft", "UAL1598 ", "Location"],
        classIri="http://www.ontologyrepository.com/CommonCoreOntologies/GeospatialLocation",
        className="Geospatial Location",
        displayValue="ADSB-test-data-UAL1598",
        confidence=Confidence.HIGH,
        sourceId=uuid4(),
        nodeId=uuid4(),
        geometry={
            "type": "LineString",
            "coordinates": coordinates,
            "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        },
        startTime=start_time.isoformat(),
        endTime=end_time.isoformat(),
    )
    timed_coords = decompose_observation_geometry(oms_obs)

    def round_time_seconds(dt: datetime) -> datetime:
        dt = dt.replace(second=int(round(dt.second + dt.microsecond / 1000000)), microsecond=0)
        return dt

    assert [tc["coordinates"] for tc in timed_coords] == coordinates
    assert [round_time_seconds(tc["detection_time"]) for tc in timed_coords] == [
        start_time,
        start_time + timedelta(hours=1),
        end_time,
    ]
