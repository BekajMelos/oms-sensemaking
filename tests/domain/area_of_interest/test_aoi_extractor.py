from oms_sensemaking.core.geo_helpers import gather_area_of_interest_data
from oms_sensemaking.domain.area_of_interest.aoi import AreaOfInterest
from oms_sensemaking.domain.area_of_interest.base import AOIExtractor


class FakeAOIExtractor(AOIExtractor):
    def __init__(self):
        self.path = [
            "tests/unit_test_data/aoi/test_aoi.kml",
            "tests/unit_test_data/aoi/test_aoi1.json",
            "tests/unit_test_data/aoi/test_aoi2.json",
            "tests/unit_test_data/aoi/test_zip_aoi.kmz",
        ]

    def get_areas_of_interest(self):
        raw_features = gather_area_of_interest_data(self.path)
        return [AreaOfInterest(f) for f in raw_features]
