from typing import Protocol

from shapely.geometry.base import BaseGeometry


class AOI(Protocol):
    raw_dict: dict
    geometry_dict: dict
    geometry_shape: BaseGeometry

    def has_overlap(self, obs_geometry: BaseGeometry) -> bool: ...


class AOIExtractor(Protocol):
    def get_areas_of_interest(self) -> list[AOI]: ...
