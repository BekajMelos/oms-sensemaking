"""Module for calculating whether a node observation is in or out of garrison"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from oms_sdk.generated.generated_graphql_client import (
    CreateActivityInput,
    GeoQuery,
    GeoQueryType,
    InOutGarrisonWithGeoActivitiesData,
    InOutGarrisonWithGeoActivitiesDataObservationsData,
    ObservationObservation,
    UpdateActivityInput,
    UpdateUuidList,
)

from oms_sensemaking.clients.instances import aac_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.geo_helpers import generate_circle_points_geographical
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import FindingBase, FindingType, Sensemaker
from oms_sensemaking.domain.in_or_out_garrison.utils import in_garrison
from oms_sensemaking.inference.rules.garrison_data_collection import GetGarrisonDataAllAtOnce
from oms_sensemaking.inference.rules.rule_helper_classes import GeoTimeframe, Timeframe

LOGGER = logging.getLogger(__name__)


@dataclass
class OutOfGarrison(FindingBase):
    """Represents a loiter event."""

    FINDING_TYPE: FindingType = field(init=False, default=FindingType.INF_OUT_OF_GARRISON)
    out_of_garrison_finding_id: UUID = field(init=False, default_factory=uuid4)
    action: str
    in_or_out: str
    vehicle_id: UUID
    garrison_observation: ObservationObservation
    start_time: datetime
    end_time: datetime
    acm: dict

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()

    def get_acm(self) -> dict:
        return self.acm

    def to_geojson(self) -> dict:
        """Geojson representation of the current location of the garrisoned object"""
        return {"type": "Point", "coordinates": self.garrison_observation.geometry["coordinates"]}


class InOrOutOfGarrison(Sensemaker):
    """
    Detect when a node is in or out of garrison and create/update the appropriate activity
    """

    def __init__(self, oms_crud_tool: OmsCrudTool):
        super().__init__()
        self.oms_crud_tool = oms_crud_tool
        self.name = self.__class__.__name__
        self.version = (1, 0, 0)
        self._data_retriever = GetGarrisonDataAllAtOnce(self.oms_crud_tool)

    def evaluate(self, obs: ObservationObservation) -> bool:
        """
        Valid inputs must contain observations that have geometry and point to a node

        :param rule_context: Rule context object containing the observation to evaluate
        """

        if not obs or obs.startTime is None or obs.endTime is None:
            return False

        return obs and obs.nodeId and obs.geometry and obs.classIri != SETTINGS.track_iri

    def process_data(self, obs: ObservationObservation, config: dict | None = None):
        """
        Determine if an observation indicates that a node is in or out of garrison

        :param rule_context: Rule context object containing the observation in question
        """
        if not self.evaluate(obs):
            return []

        garrison_data = self._data_retriever.get_all_garrison_data(obs)
        if not garrison_data:
            return []

        object_lat_lon = garrison_data.object_lat_lon
        garrison_lat_lon = garrison_data.garrison_lat_lon
        activities = garrison_data.activities

        in_garrison_check = in_garrison(object_lat_lon, garrison_lat_lon)
        garrison_buffer_points = generate_circle_points_geographical(
            garrison_lat_lon[0], garrison_lat_lon[1], SETTINGS.garrison_distance_kilometers
        )
        garrison_buffer_geojson = {"type": "Polygon", "coordinates": [garrison_buffer_points]}
        return self._create_or_update_garrison_activity(obs, in_garrison_check, garrison_buffer_geojson, activities)

    def _create_or_update_garrison_activity(
        self,
        obs: ObservationObservation,
        in_garrison: bool,
        garrison_buffer_geojson: dict,
        existing_activities: List[InOutGarrisonWithGeoActivitiesData],
    ):
        if in_garrison:
            activity_name = SETTINGS.inference_in_garrison_activity_name
            activity_state = SETTINGS.inference_in_garrison_activity_state
            geo_query = GeoQuery(queryGeoJson=garrison_buffer_geojson, queryType=GeoQueryType.DISJOINT)

        else:
            activity_name = SETTINGS.inference_out_of_garrison_activity_name
            activity_state = SETTINGS.inference_out_of_garrison_activity_state
            geo_query = GeoQuery(queryGeoJson=garrison_buffer_geojson, queryType=GeoQueryType.INTERSECTS)

        matching_activity_found = False

        enhanced_obs = Timeframe(obs)
        for existing_activity in existing_activities:
            # Query returns both in- and out-of-garrison activities; filter client-side
            if existing_activity.state != activity_state:
                continue
            if existing_activity.name != activity_name:
                continue

            enhanced_activity = GeoTimeframe(existing_activity.startTime, existing_activity.endTime)
            # Update existing activity if times overlap or if node_object stayed in/out of
            # garrison in the time between the observation and activity
            time_overlap = enhanced_activity.does_observation_overlap(enhanced_obs)
            if time_overlap or enhanced_activity.object_observed_between_generic_node_and_observation_times(
                obs.nodeId, obs, geo_query
            ):
                # Update existing activity with union of observation and activity time intervals
                enhanced_activity.update_generic_node_times_with_observation(enhanced_obs)
                existing_garrison_observations = existing_activity.observations.data
                return self._update_existing_activity(
                    obs, existing_activity, existing_garrison_observations, enhanced_activity
                )

        # Observation not found as part of any existing garrison activity
        if not matching_activity_found:
            return self._handle_new_activity(obs, activity_name, activity_state)

    def _update_existing_activity(
        self,
        observation: ObservationObservation,
        existing_activity: InOutGarrisonWithGeoActivitiesData,
        existing_garrison_observations: list[InOutGarrisonWithGeoActivitiesDataObservationsData],
        enhanced_activity: GeoTimeframe,
    ):
        """
        Update an existing activity with updated start/end times
        """
        existing_garrison_observations.append(observation)
        rolled_up_acm = aac_client.get_acm_rollup(
            [{"ACM": observation.acm} for observation in existing_garrison_observations]
        )
        # Update start/end times and add observation to garrison activity
        updated_activity_input = UpdateActivityInput(
            id=existing_activity.id,
            acm=rolled_up_acm,
            startTime=enhanced_activity.start_time.isoformat(),
            endTime=enhanced_activity.end_time.isoformat(),
            observationIds=UpdateUuidList(add=[observation.id]),
            nodeId=observation.nodeId,
        )
        updated_garrison_activity = self.oms_crud_tool.update_activity(updated_activity_input)
        return [
            OutOfGarrison(
                action="Garrison Activity Updated",
                in_or_out=updated_garrison_activity.name,
                vehicle_id=observation.nodeId,
                garrison_observation=observation,
                start_time=updated_garrison_activity.startTime,
                end_time=updated_garrison_activity.endTime,
                acm=rolled_up_acm,
            )
        ]

    def _handle_new_activity(self, observation: ObservationObservation, activity_name: str, activity_state: str):
        """
        Create new activity pointing to observation
        """

        # Create in/out of garrison activity pointing to observation
        garrison_activity = CreateActivityInput(
            acm=observation.acm,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.garrison_sm_label,
                self.version_string,
            ],
            classIri=SETTINGS.inference_garrison_class_iri,
            name=activity_name,
            state=activity_state,
            nodeId=observation.nodeId,
            observationIds=[observation.id],
            startTime=observation.startTime,
            endTime=observation.endTime,
        )
        new_garrison_activity = self.oms_crud_tool.create_activity(garrison_activity)
        return [
            OutOfGarrison(
                action="Garrison Activity Created",
                in_or_out=new_garrison_activity.name,
                vehicle_id=observation.nodeId,
                garrison_observation=observation,
                start_time=new_garrison_activity.startTime,
                end_time=new_garrison_activity.endTime,
                acm=new_garrison_activity.acm,
            )
        ]
