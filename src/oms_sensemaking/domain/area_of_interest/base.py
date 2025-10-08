from typing import Protocol

from shapely.geometry.base import BaseGeometry


class AOI(Protocol):
    @property
    def name(self) -> str | None: ...

    @property
    def geometry_dict(self) -> dict: ...

    @property
    def geometry_shape(self) -> BaseGeometry: ...

    def has_overlap(self, obs_geometry: BaseGeometry) -> bool: ...


class AOIExtractor(Protocol):
    def get_areas_of_interest(self) -> list[AOI]: ...
