from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from oms_sensemaking.domain.area_of_interest.base import AOI


class AreaOfInterest(AOI):
    def get_geometry_dict(self, feature: dict) -> dict:
        return feature["geometry"]

    def get_geometry_shape(self, feature: dict) -> BaseGeometry:
        return shape(self.get_geometry_dict(feature))

    def has_overlap(self, geometry: BaseGeometry, obs_geometry: BaseGeometry) -> bool:
        overlap = geometry.intersection(obs_geometry)
        return bool(not overlap.is_empty)
