from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.geo_helpers import gather_area_of_interest_data
from oms_sensemaking.domain.area_of_interest.base import AOIExtractor


class RealAOIDataExtractor(AOIExtractor):
    def __init__(self):
        self.path = SETTINGS.inference_incursion_areas_of_interest_path

    def get_areas_of_interest(self):
        return gather_area_of_interest_data(self.path)
