from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from oms_sensemaking.domain.area_of_interest.base import AOI


class AreaOfInterest(AOI):
    def __init__(self, feature: dict):
        self.raw_dict = feature
        self.geometry_dict = feature["geometry"]
        self.geometry_shape = shape(feature["geometry"])

    def has_overlap(self, obs_geometry: BaseGeometry) -> bool:
        overlap = self.geometry_shape.intersection(obs_geometry)
        return bool(not overlap.is_empty)
