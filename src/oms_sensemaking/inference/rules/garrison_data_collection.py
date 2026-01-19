import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from oms_sdk.generated.generated_graphql_client import (
    ActivityQuery,
    InOutGarrisonWithGeoActivitiesData,
    ObservationObservation,
    StringQuery,
    UuidQueryByList,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER = logging.getLogger(__name__)


@dataclass
class GarrisonData:
    """All graph data needed by the In/Out of Garrison rule for a single observation."""

    object_lat_lon: list[float]
    garrison_lat_lon: list[float]
    activities: List[InOutGarrisonWithGeoActivitiesData]


class GetGarrisonData(ABC):
    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        self.oms_crud_tool = oms_crud_tool

    @abstractmethod
    def get_all_garrison_data(self, obs: ObservationObservation):
        raise NotImplementedError


class GetGarrisonDataAllAtOnce(GetGarrisonData):
    def get_all_garrison_data(self, obs: ObservationObservation) -> Optional[GarrisonData]:
        result = self.oms_crud_tool.oms_client.in_out_garrison_with_geo(
            id=obs.nodeId,
            garrisonIris=[SETTINGS.inference_garrisoned_in_iri],
            geoIris=[SETTINGS.inference_geo_attribute_iri],
            activityQuery=ActivityQuery(
                nodeIds=UuidQueryByList(in_=[obs.nodeId]),
                name=StringQuery(
                    in_=[
                        SETTINGS.inference_in_garrison_activity_name,
                        SETTINGS.inference_out_of_garrison_activity_name,
                    ]
                ),
                states=[
                    SETTINGS.inference_in_garrison_activity_state,
                    SETTINGS.inference_out_of_garrison_activity_state,
                ],
            ),
        )

        end_node = result.node.relationships.data[0].endNode if result.node and result.node.relationships.data else None
        attribute_data = (
            end_node.attributes.data[0]
            if end_node and hasattr(end_node, "attributes") and end_node.attributes.data
            else None
        )

        if not attribute_data or "coordinates" not in attribute_data.geometry:
            return None

        garrison_lon_lat = attribute_data.geometry["coordinates"]
        object_lon_lat = obs.geometry["coordinates"]

        return GarrisonData(
            object_lat_lon=[object_lon_lat[1], object_lon_lat[0]],
            garrison_lat_lon=[garrison_lon_lat[1], garrison_lon_lat[0]],
            activities=result.activities.data,
        )
