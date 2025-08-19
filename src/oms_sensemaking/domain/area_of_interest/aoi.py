from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from oms_sensemaking.domain.area_of_interest.base import AOI


class AreaOfInterest(AOI):
    def __init__(self, feature: dict):
        self._name = feature.get("properties", {}).get("name") if feature else None
        self._geometry_dict = feature["geometry"]
        self._geometry_shape = shape(feature["geometry"])

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def geometry_dict(self) -> dict:
        return self._geometry_dict

    @property
    def geometry_shape(self) -> BaseGeometry:
        return self._geometry_shape

    def has_overlap(self, obs_geometry: BaseGeometry) -> bool:
        overlap = self.geometry_shape.intersection(obs_geometry)
        return bool(not overlap.is_empty)
