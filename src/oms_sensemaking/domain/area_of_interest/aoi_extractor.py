from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.geo_helpers import gather_area_of_interest_data
from oms_sensemaking.domain.area_of_interest.aoi import AreaOfInterest
from oms_sensemaking.domain.area_of_interest.base import AOI, AOIExtractor


class RealAOIDataExtractor(AOIExtractor):
    def __init__(self):
        self.paths = SETTINGS.inference_incursion_areas_of_interest_paths

    def get_areas_of_interest(self) -> list[AOI]:
        raw_features = gather_area_of_interest_data(self.paths)
        return [AreaOfInterest(f) for f in raw_features]
