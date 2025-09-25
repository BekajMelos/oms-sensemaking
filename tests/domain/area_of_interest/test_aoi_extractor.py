from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.geo_helpers import gather_area_of_interest_data
from oms_sensemaking.domain.area_of_interest.aoi import AreaOfInterest
from oms_sensemaking.domain.area_of_interest.aoi_extractor import RealAOIDataExtractor
from oms_sensemaking.domain.area_of_interest.base import AOIExtractor


def test_real_aoi_extractor_init():
    extractor = RealAOIDataExtractor()
    assert extractor.path == SETTINGS.inference_incursion_areas_of_interest_path


def test_get_aois():
    extractor = RealAOIDataExtractor()
    result = extractor.get_areas_of_interest()
    assert all(isinstance(x, AreaOfInterest) for x in result)


class FakeAOIExtractor(AOIExtractor):
    def __init__(self):
        self.path = "tests/unit_test_data/aoi"

    def get_areas_of_interest(self):
        raw_features = gather_area_of_interest_data(self.path)
        return [AreaOfInterest(f) for f in raw_features]
