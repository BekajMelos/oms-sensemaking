from typing import Protocol

from shapely.geometry.base import BaseGeometry


class AOI(Protocol):
    def get_geometry_dict(self, feature: dict) -> dict: ...

    def get_geometry_shape(self, feature: dict) -> BaseGeometry: ...

    def has_overlap(self, geometry: BaseGeometry, obs_geometry: BaseGeometry) -> bool: ...


class AOIExtractor(Protocol):
    def get_areas_of_interest(self) -> list[dict]: ...
