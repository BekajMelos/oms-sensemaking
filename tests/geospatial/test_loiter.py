"""Tests for loiter sensemaker."""

import random

import shapely

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
