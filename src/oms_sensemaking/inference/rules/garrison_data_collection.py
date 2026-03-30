import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from oms_sdk.generated.generated_graphql_client import (
    InOutGarrisonAllDataNodeActivitiesData,
    InOutGarrisonAllDataNodeRelationshipsData,
    InOutGarrisonAllDataNodeRelationshipsDataEndNode,
    ObservationObservation,
    StringQuery,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool

LOGGER = logging.getLogger(__name__)


@dataclass
class GarrisonData:
    """All graph data needed by the In/Out of Garrison rule for a single observation."""

    object_lat_lon: list[float]
    garrison_lat_lon: list[float]
    activities: List[InOutGarrisonAllDataNodeActivitiesData]
    garrison_data_acms: list[dict]


class GetGarrisonData(ABC):
    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        self.oms_crud_tool = oms_crud_tool

    @abstractmethod
    def get_all_garrison_data(self, obs: ObservationObservation):
        raise NotImplementedError


class GetGarrisonDataAllAtOnce(GetGarrisonData):
    def get_all_garrison_data(self, obs: ObservationObservation) -> Optional[GarrisonData]:
        observed_node = self._execute_query(obs)

        relationship_data: InOutGarrisonAllDataNodeRelationshipsData = (
            observed_node.relationships.data[0] if observed_node and observed_node.relationships.data else None
        )
        facility_node: InOutGarrisonAllDataNodeRelationshipsDataEndNode = (
            relationship_data.endNode if relationship_data else None
        )
        facility_location_attribute_data = (
            facility_node.attributes.data[0]
            if facility_node and hasattr(facility_node, "attributes") and facility_node.attributes.data
            else None
        )

        if not facility_location_attribute_data or "coordinates" not in facility_location_attribute_data.geometry:
            return None

        garrison_lon_lat = facility_location_attribute_data.geometry["coordinates"]
        object_lon_lat = obs.geometry["coordinates"]

        return GarrisonData(
            object_lat_lon=[object_lon_lat[1], object_lon_lat[0]],
            garrison_lat_lon=[garrison_lon_lat[1], garrison_lon_lat[0]],
            activities=observed_node.activities.data,
            garrison_data_acms=[
                observed_node.acm,
                relationship_data.acm,
                facility_node.acm,
                facility_location_attribute_data.acm,
            ],
        )

    def _execute_query(self, obs: ObservationObservation):
        return self.oms_crud_tool.oms_client.in_out_garrison_all_data(
            id=obs.nodeId,
            garrisonIris=[SETTINGS.out_of_garrison_settings.garrisoned_in_relationship_iri],
            geoIris=[SETTINGS.geo_attribute_iri],
            activityName=StringQuery(
                or_=[
                    StringQuery(equals=SETTINGS.out_of_garrison_settings.in_garrison_activity_name),
                    StringQuery(equals=SETTINGS.out_of_garrison_settings.out_of_garrison_activity_name),
                ]
            ),
            activityStates=StringQuery(
                or_=[
                    StringQuery(equals=SETTINGS.out_of_garrison_settings.in_garrison_activity_state),
                    StringQuery(equals=SETTINGS.out_of_garrison_settings.out_of_garrison_activity_state),
                ]
            ),
        )
