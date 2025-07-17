from typing import List, Literal

from pydantic import BaseModel, Field

from .base_observable import BaseObservable


class GeoJSONPoint(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [lon, lat]


class MinDistanceObservable(BaseObservable):
    location: GeoJSONPoint
    min_distance: float = Field(..., alias="minDistance")

    def update_data(self):
        """Update data for minimum distance observable."""
        # TODO: implement min distance query
        pass
