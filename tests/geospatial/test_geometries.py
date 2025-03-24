from uuid import uuid4

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
        startTime="2022-12-01T00:20:14.000Z",
        endTime="2022-12-01T00:20:14.000Z",
    )
    timed_coords = decompose_observation_geometry(oms_obs)
    assert len(timed_coords) == 1
