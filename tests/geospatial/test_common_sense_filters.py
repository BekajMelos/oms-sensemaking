from datetime import datetime
from uuid import uuid4

import pytest
from oms_sdk.generated.generated_graphql_client import Confidence

from oms_sensemaking.models.geo import CommonSenseFilter, Point

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


@pytest.fixture
def common_sense_filter() -> CommonSenseFilter:
    return CommonSenseFilter(
        name="Test Filter",
        iri_search_pattern="aircraft",
        altitude_threshold_meters=200,
        altitude_deviation_threshold_mps=10,
        time_threshold_seconds=5,
        relative_velocity_threshold_mps=500,
    )


def test_filter(common_sense_filter: CommonSenseFilter):
    node_id = uuid4()
    obs_ids = (uuid4(), uuid4(), uuid4())
    source_ids = (uuid4(), uuid4(), uuid4())

    def create_test_points():
        p1 = Point(
            acm=DEFAULT_ACM,
            location="POINT (-87.63520 41.85677)",
            altitude=5,
            detection_time=datetime.fromisoformat("2024-03-20T12:35:00-04:00"),
            node_id=node_id,
            node_version=1,
            observation_id=obs_ids[0],
            observation_version=1,
            source_id=source_ids[0],
            observation_confidence=Confidence.HIGH,
        )

        p2 = Point(
            acm=DEFAULT_ACM,
            location="POINT (-87.67096 41.85733)",
            altitude=100,
            detection_time=datetime.fromisoformat("2024-03-20T12:35:10-04:00"),
            node_id=node_id,
            node_version=1,
            observation_id=obs_ids[1],
            observation_version=1,
            source_id=source_ids[1],
            observation_confidence=Confidence.HIGH,
        )

        p3 = Point(
            acm=DEFAULT_ACM,
            location="POINT (-87.69683 41.85790)",
            altitude=50,
            detection_time=datetime.fromisoformat("2024-03-20T12:35:20-04:00"),
            node_id=node_id,
            node_version=1,
            observation_id=obs_ids[2],
            observation_version=1,
            source_id=source_ids[2],
            observation_confidence=Confidence.HIGH,
        )
        return [p1, p2, p3]

    # No filtering
    points = create_test_points()
    points = common_sense_filter.filter_points_altitude(points=points, iri="iri_aircraft")
    assert tuple(p.weight for p in points) == (1.0, 1.0, 1.0)

    # No matching IRI
    points[1].altitude = 205
    points = common_sense_filter.filter_points_altitude(points=points, iri="iri_vessel")
    assert tuple(p.weight for p in points) == (1.0, 1.0, 1.0)

    # Altitude too high
    points = common_sense_filter.filter_points_altitude(points=points, iri="iri_aircraft")
    assert tuple(p.weight for p in points) == (1.0, 0.0, 1.0)

    # Altitude too low
    points = create_test_points()
    points[0].altitude = -5
    points = common_sense_filter.filter_points_altitude(points=points, iri="iri_aircraft")
    assert tuple(p.weight for p in points) == (0.0, 1.0, 1.0)

    # No teleportations
    original_points = create_test_points()
    original_points = common_sense_filter.filter_points_teleportation(points=original_points, iri="iri_aircraft")
    assert len(original_points) == 3

    # Altitude rate exceeded
    new_points = create_test_points()
    new_points[1].altitude = 195
    new_points = common_sense_filter.filter_points_teleportation(points=new_points, iri="iri_aircraft")
    assert new_points == [original_points[0], original_points[2]]

    # Time delta too small
    new_points = create_test_points()
    new_points[1].altitude = 195
    new_points[1].detection_time = datetime.fromisoformat("2024-03-20T12:35:01-04:00")
    new_points = common_sense_filter.filter_points_teleportation(points=new_points, iri="iri_aircraft")
    assert len(new_points) == 3

    # Horizontal teleportation
    new_points = create_test_points()
    new_points[2] = Point(
        acm=DEFAULT_ACM,
        location="POINT (-87.88133 41.85905)",
        altitude=50,
        detection_time=datetime.fromisoformat("2024-03-20T12:35:20-04:00"),
        node_id=node_id,
        node_version=1,
        observation_id=obs_ids[2],
        observation_version=1,
        source_id=source_ids[2],
        observation_confidence=Confidence.HIGH,
    )
    new_points = common_sense_filter.filter_points_teleportation(points=new_points, iri="iri_aircraft")
    assert new_points == [original_points[0], original_points[1]]
