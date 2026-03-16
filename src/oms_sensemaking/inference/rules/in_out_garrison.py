"""Module for calculating whether a node observation is in or out of garrison"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID

from oms_sdk.generated.generated_graphql_client import (
    CreateActivityInput,
    GeoQuery,
    GeoQueryType,
    InOutGarrisonAllDataNodeActivitiesData,
    InOutGarrisonAllDataNodeActivitiesDataObservationsData,
    ObservationObservation,
    UpdateActivityInput,
    UpdateUuidList,
)

from oms_sensemaking.clients.instances import aac_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.geo_helpers import generate_circle_points_geographical
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import FindingBase, Sensemaker
from oms_sensemaking.domain.in_or_out_garrison.utils import in_garrison
from oms_sensemaking.inference.rules.garrison_data_collection import GetGarrisonDataAllAtOnce
from oms_sensemaking.inference.rules.rule_helper_classes import GeoTimeframe, Timeframe
from oms_sensemaking.models.sensemaking import AtomsType, FindingType

LOGGER = logging.getLogger(__name__)


@dataclass
class InOutGarrison(FindingBase):
    """Represents an In or Out of Garrison activity"""

    FINDING_TYPE: FindingType = field(init=False, default=FindingType.INF_OUT_OF_GARRISON)
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

        :param obs: observation to evaluate for suitability for In/Out Garrison processing
        """

        if not obs or obs.startTime is None or obs.endTime is None:
            return False

        return obs and obs.nodeId and obs.geometry and obs.classIri != SETTINGS.track_iri

    def process_data(self, obs: ObservationObservation, config: dict | None = None):
        """
        Determine if an observation indicates that a node is in or out of garrison

        :param obs: observation to determine if node is In/Out of Garrison
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
        is_in_garrison: bool,
        garrison_buffer_geojson: dict,
        existing_activities: List[InOutGarrisonAllDataNodeActivitiesData],
    ):
        if is_in_garrison:
            activity_name = SETTINGS.inference_in_garrison_activity_name
            activity_state = SETTINGS.inference_in_garrison_activity_state
            geo_query = GeoQuery(queryGeoJson=garrison_buffer_geojson, queryType=GeoQueryType.DISJOINT)

        else:
            activity_name = SETTINGS.inference_out_of_garrison_activity_name
            activity_state = SETTINGS.inference_out_of_garrison_activity_state
            geo_query = GeoQuery(queryGeoJson=garrison_buffer_geojson, queryType=GeoQueryType.INTERSECTS)

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
        return self._handle_new_activity(obs, activity_name, activity_state)

    def _update_existing_activity(
        self,
        observation: ObservationObservation,
        existing_activity: InOutGarrisonAllDataNodeActivitiesData,
        existing_garrison_observations: list[InOutGarrisonAllDataNodeActivitiesDataObservationsData],
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

        garrison_finding = InOutGarrison(
            in_or_out=existing_activity.name,
            vehicle_id=observation.nodeId,
            garrison_observation=observation,
            start_time=enhanced_activity.start_time.isoformat(),
            end_time=enhanced_activity.end_time.isoformat(),
            acm=rolled_up_acm,
        )

        updated_activity_input = UpdateActivityInput(
            id=existing_activity.id,
            acm=garrison_finding.acm,
            startTime=garrison_finding.start_time,
            endTime=garrison_finding.end_time,
            observationIds=UpdateUuidList(add=[observation.id]),
            nodeId=garrison_finding.vehicle_id,
        )

        self.oms_crud_tool.update_activity(updated_activity_input)

        garrison_finding.atoms_id = existing_activity.id
        garrison_finding.atoms_type = AtomsType.ACTIVITY
        garrison_finding.query_atoms_id = existing_activity.id
        garrison_finding.query_atoms_type = AtomsType.ACTIVITY

        return [garrison_finding]

    def _handle_new_activity(self, observation: ObservationObservation, activity_name: str, activity_state: str):
        """
        Create new activity pointing to observation
        """

        # Create in/out of garrison activity pointing to observation
        # we create the model after we send an update to Core here
        garrison_finding = InOutGarrison(
            in_or_out=activity_name,
            vehicle_id=observation.nodeId,
            garrison_observation=observation,
            start_time=observation.startTime,
            end_time=observation.endTime,
            acm=observation.acm,
        )

        garrison_activity = CreateActivityInput(
            acm=garrison_finding.acm,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.garrison_sm_label,
                self.version_string,
            ],
            classIri=SETTINGS.inference_garrison_class_iri,
            name=activity_name,
            state=activity_state,
            nodeId=garrison_finding.vehicle_id,
            observationIds=[observation.id],
            startTime=garrison_finding.start_time,
            endTime=garrison_finding.end_time,
        )

        new_garrison_activity = self.oms_crud_tool.create_activity(garrison_activity)

        garrison_finding.atoms_id = new_garrison_activity.id
        garrison_finding.atoms_type = AtomsType.ACTIVITY

        return [garrison_finding]
