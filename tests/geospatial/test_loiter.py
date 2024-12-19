"""Tests for loiter sensemaker."""

import random
from datetime import datetime
from uuid import uuid4

import shapely
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.geospatial.sensemakers.loiters import LoiterSensemaker
from oms_sensemaking.models.geo import Point, Track

ROLLUP_DEFAULT_ACM = {
    "version": "3.0",
    "classif_type": "US",
    "classif": "U",
    "owner_prod": ["USA"],
    "non_us_ctrls": [],
    "sci_ctrls": [],
    "disponly_to": [""],
    "dissem_ctrls": [],
    "non_ic": [],
    "rel_to": [],
    "fgi_open": [],
    "fgi_protect": [],
    "portion": "U//DISPLAY ONLY",
    "banner": "UNCLASSIFIED//DISPLAY ONLY",
    "dissem_countries": [],
    "accms": [],
    "macs": [],
    "oc_attribs": [{"orgs": [], "missions": [], "regions": []}],
    "share": {"users": [], "projects": {}},
    "f_clearance": ["u"],
    "f_sci_ctrls": [],
    "f_accms": [],
    "f_oc_org": [],
    "f_regions": [],
    "f_missions": [],
    "f_share": [],
    "f_macs": [],
}


def get_random_stamford_bridge_point() -> str:
    #  Get point near Stamford Bridge - all within geohash5 gcpug
    lon_max = -0.189286
    lon_min = -0.192512
    lat_max = 51.482857
    lat_min = 51.480729

    return shapely.Point(random.uniform(lon_min, lon_max), random.uniform(lat_min, lat_max)).wkt


def test_loiter_fails_valid_observed_threshold(mock_oms_client, mock_oms_crud_tool):
    """Failure. Unobserved for too long."""
    node_id = uuid4()
    # East London
    p1 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-0.030890, 51.509420).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
        node_id=node_id,
        node_version=1,
        attribute_id=uuid4(),
        attribute_version=1,
        source_id=uuid4(),
    )
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(
        acm=DEFAULT_ACM,
        location=p2_point,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"),
        node_id=node_id,
        node_version=1,
        attribute_id=uuid4(),
        attribute_version=1,
        source_id=uuid4(),
    )
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(
        acm=DEFAULT_ACM,
        location=p3_point,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T12:40:00-04:00"),
        node_id=node_id,
        node_version=1,
        attribute_id=uuid4(),
        attribute_version=1,
        source_id=uuid4(),
    )
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(
        acm=DEFAULT_ACM,
        location=p4_point,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T13:00:00-04:00"),
        node_id=node_id,
        node_version=1,
        attribute_id=uuid4(),
        attribute_version=1,
        source_id=uuid4(),
    )
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(
        acm=DEFAULT_ACM,
        location=p5_point,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T13:20:00-04:00"),
        node_id=node_id,
        node_version=1,
        attribute_id=uuid4(),
        attribute_version=1,
        source_id=uuid4(),
    )
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(
        acm=DEFAULT_ACM,
        location=p6_point,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T13:40:00-04:00"),
        node_id=node_id,
        node_version=1,
        attribute_id=uuid4(),
        attribute_version=1,
        source_id=uuid4(),
    )
    # West London
    p7 = Point(
        acm=DEFAULT_ACM,
        location=shapely.Point(-0.413890, 51.474942).wkt,
        altitude=None,
        detection_time=datetime.fromisoformat("2024-03-20T14:00:00-04:00"),
        node_id=node_id,
        node_version=1,
        attribute_id=uuid4(),
        attribute_version=1,
        source_id=uuid4(),
    )

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7], node_id=uuid4())

    loiters = LoiterSensemaker(mock_oms_crud_tool).execute(track)
    assert len(loiters) == 0
