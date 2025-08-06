import pytest
from shapely.geometry import Polygon, mapping, shape

from oms_sensemaking.domain.area_of_interest.aoi import AreaOfInterest
from tests.domain.area_of_interest.test_aoi_extractor import TestAOIExtractor  # adjust import path as needed


def test_get_areas_of_interest_returns_list():
    extractor = TestAOIExtractor()
    aois = extractor.get_areas_of_interest()

    assert isinstance(aois, list)
    assert len(aois) > 0
    assert all(isinstance(aoi, AreaOfInterest) for aoi in aois)


@pytest.fixture
def sample_feature():
    polygon = Polygon([(0, 0), (0, 10), (10, 10), (10, 0)])
    return {"type": "Feature", "geometry": mapping(polygon), "properties": {"id": "test-aoi"}}


def test_area_of_interest_initialization(sample_feature):
    aoi = AreaOfInterest(sample_feature)

    assert aoi.raw_dict == sample_feature
    assert aoi.geometry_dict == sample_feature["geometry"]
    assert aoi.geometry_shape.equals(Polygon([(0, 0), (0, 10), (10, 10), (10, 0)]))


def test_has_overlap_returns_true(sample_feature):
    aoi = AreaOfInterest(sample_feature)
    geometry = {"coordinates": [5, 5], "type": "Point"}

    assert aoi.has_overlap(shape(geometry)) is True


def test_has_overlap_returns_false(sample_feature):
    aoi = AreaOfInterest(sample_feature)
    non_overlapping_geom = Polygon([(20, 20), (20, 30), (30, 30), (30, 20)])

    assert aoi.has_overlap(non_overlapping_geom) is False
