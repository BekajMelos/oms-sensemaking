"""Incursion Rule"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivitiesData,
    ActivityQuery,
    CreateActivityInput,
    GeoQuery,
    GeoQueryType,
    IncursionDataActivitiesData,
    IncursionDataActivitiesDataObservationsData,
    ObservationObservation,
    ObservationsObservationsData,
    PageParams,
    StringQuery,
    UpdateActivityInput,
    UpdateUuidList,
    UuidQueryByList,
)
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from oms_sensemaking.clients.instances import aac_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import FindingBase, Sensemaker
from oms_sensemaking.domain.area_of_interest.base import AOI, AOIExtractor
from oms_sensemaking.inference.rules.rule_helper_classes import GeoTimeframe, Timeframe
from oms_sensemaking.models.sensemaking import AtomsType, FindingType

LOGGER = logging.getLogger(__name__)


@dataclass
class Incursion(FindingBase):
    """Represents an Incursion."""

    FINDING_TYPE: FindingType = field(init=False, default=FindingType.INF_INCURSION)
    incurring_obj_id: UUID
    incursion_observation: ObservationObservation
    start_time: datetime
    end_time: datetime
    area_of_interest_dict: dict
    acm: dict

    def get_acm(self) -> dict:
        """ACM from observation(s) of Incursion"""
        return self.acm

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()

    def to_geojson(self) -> dict:
        """Geojson representation of the last location of the Incurring object"""

        return {"type": "Point", "coordinates": self.incursion_observation.geometry["coordinates"]}


class IncursionSensemaker(Sensemaker):
    """
    Determine if an Observation indicates an incursion for the node it's associated
    with and make the appropriate attribute/activity updates
    """

    def __init__(self, aoi_extractor: AOIExtractor, oms_crud_tool: OmsCrudTool):
        super().__init__()
        self.oms_crud_tool = oms_crud_tool
        self.name = self.__class__.__name__
        self.version = (1, 0, 0)
        self.features = aoi_extractor.get_areas_of_interest()

    def evaluate(self, obs: ObservationObservation) -> bool:
        """
        Valid inputs must contain observations that have geometry and point to a node

        :param obs: observation to evaluate for suitability for Incursion processing
        """
        if not obs or obs.startTime is None or obs.endTime is None:
            return False

        return obs and obs.nodeId and obs.geometry and obs.classIri != SETTINGS.track_iri

    def process_data(self, obs: ObservationObservation, config: dict | None = None) -> list[Incursion]:
        """
        Create or update relevant incursion attribute/activity if observation indicates an incursion

        :param obs: observation to determine if node is performing an Incursion
        """
        incursion_finding: list[Incursion] = []
        if not self.evaluate(obs):
            return []
        obs_geo: BaseGeometry = shape(obs.geometry)

        # Check if observation occurred in an area of interest
        feature_of_interest = None
        for feature in self.features:
            overlap = feature.has_overlap(obs_geo)
            if overlap:
                feature_of_interest = feature
                break

        if feature_of_interest:
            # can we include geo?
            LOGGER.debug("Incursion detected for Observation: %s", obs.id)
            incursion_obs_timeframe = Timeframe(obs)
            # Check for existing incursions in the relevant geo of interest
            existing_incursion_activities = self.get_all_incursion_data(incurring_object_id=obs.nodeId)
            matching_existing_incursion_found = False

            LOGGER.debug("%d Existing Incursion Activities", len(existing_incursion_activities))

            for existing_incursion_activity in existing_incursion_activities:
                if matching_existing_incursion_found:
                    break
                existing_incursion_observations = existing_incursion_activity.observations.data
                LOGGER.debug("%x Existing Incursion Observations", len(existing_incursion_observations))

                incursion_finding = self._check_existing_incursion_and_update(
                    obs,
                    feature_of_interest,
                    existing_incursion_activity,
                    existing_incursion_observations,
                    incursion_obs_timeframe,
                )
                matching_existing_incursion_found = bool(incursion_finding)

            # Observation not found as part of any existing incursions in relevant area of interest
            if not matching_existing_incursion_found:
                incursion_finding = self._handle_new_incursion(obs, feature_of_interest)
        return incursion_finding

    def _check_existing_incursion_and_update(
        self,
        observation: ObservationObservation,
        feat_of_int: AOI,
        existing_act: IncursionDataActivitiesData,
        existing_observations: list[IncursionDataActivitiesDataObservationsData],
        obs_timeframe: Timeframe,
    ):
        """
        function to check for existing incursions given an activity object
        and its connected attributes
        """
        inc_act_geo_timeframe = GeoTimeframe(existing_act.startTime, existing_act.endTime)
        # Update existing incursion if times overlap or if object stayed in area of
        # interest in the time between the observation and incursion
        time_overlap = inc_act_geo_timeframe.does_observation_overlap(obs_timeframe)
        geo_query = GeoQuery(queryGeoJson=feat_of_int.geometry_dict, queryType=GeoQueryType.DISJOINT)
        if time_overlap or inc_act_geo_timeframe.object_observed_between_generic_node_and_observation_times(
            observation.nodeId, observation, geo_query
        ):
            # Update existing incursion with union of observation and incursion time intervals
            inc_act_geo_timeframe.update_generic_node_times_with_observation(obs_timeframe)
            incursion_finding = self._update_existing_incursion(
                observation,
                feat_of_int,
                existing_act,
                existing_observations,
                inc_act_geo_timeframe,
            )
            return incursion_finding
        return None

    def get_all_incursion_data(self, incurring_object_id: UUID, pagesize: int = 200):
        incursion_activities: list[IncursionDataActivitiesData] = []
        page = 1
        has_more = True

        while has_more:
            activity_query = ActivityQuery(
                classIris=[SETTINGS.inference_incursion_class_iri],
                name=StringQuery(equals="Incursion"),
                states=[SETTINGS.inference_incursion_activity_state],
                nodeIds=UuidQueryByList(in_=[incurring_object_id]),
                pageParams=PageParams(page=page, pageSize=pagesize),
            )
            response = self.oms_crud_tool.oms_client.incursion_data(activity_query)
            activities_layer = response.data or []
            incursion_activities.extend(activities_layer)

            has_more = len(activities_layer) == pagesize
            page += 1
        return incursion_activities

    def _update_existing_incursion(
        self,
        observation: ObservationObservation,
        feat_of_int: AOI,
        existing_incursion_activity: ActivitiesActivitiesData,
        existing_incursion_observations: list[ObservationsObservationsData],
        inc_attr_geo_timeframe: GeoTimeframe,
    ):
        """
        Update an existing incursion attribute and corresponding activity
        with updated start/end times
        """

        # Update start/end times and add observation to incursion activity
        existing_incursion_observations.append(observation)
        rolled_up_acm = aac_client.get_acm_rollup(
            [{"ACM": observation.acm} for observation in existing_incursion_observations]
        )

        incursion_finding = Incursion(
            incurring_obj_id=observation.nodeId,
            incursion_observation=observation,
            start_time=inc_attr_geo_timeframe.start_time.isoformat(),
            end_time=inc_attr_geo_timeframe.end_time.isoformat(),
            acm=rolled_up_acm,
            area_of_interest_dict=feat_of_int.geometry_dict,
        )

        activity_labels = existing_incursion_activity.labels
        if activity_labels is None:
            activity_labels = []
        activity_labels.append(SETTINGS.sm_enriched_label)
        updated_activity_input = UpdateActivityInput(
            id=existing_incursion_activity.id,
            acm=incursion_finding.acm,
            startTime=incursion_finding.start_time,
            endTime=incursion_finding.end_time,
            observationIds=UpdateUuidList(add=[incursion_finding.incursion_observation.id]),
            labels=activity_labels,
        )

        self.oms_crud_tool.update_activity(updated_activity_input)

        incursion_finding.atoms_id = existing_incursion_activity.id
        incursion_finding.atoms_type = AtomsType.ACTIVITY
        incursion_finding.query_atoms_id = existing_incursion_activity.id
        incursion_finding.query_atoms_type = AtomsType.ACTIVITY

        return [incursion_finding]

    def _handle_new_incursion(self, observation: ObservationObservation, feature_of_interest: AOI):
        """
        Create new incursion activity pointing to observation
        """

        # Create new incursion activity pointing to observation
        description = f"Incursion Activity by object: {observation.nodeId}"

        incursion_finding = Incursion(
            incurring_obj_id=observation.nodeId,
            incursion_observation=observation,
            start_time=observation.startTime,
            end_time=observation.endTime,
            acm=observation.acm,
            area_of_interest_dict=feature_of_interest.geometry_dict,
        )

        incursion_activity = CreateActivityInput(
            acm=incursion_finding.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                self.version_string,
            ],
            classIri=SETTINGS.inference_incursion_class_iri,
            name="Incursion",
            description=self._truncate_activity_description(description),
            state=SETTINGS.inference_incursion_activity_state,
            sourceId=observation.sourceId,
            nodeId=incursion_finding.incurring_obj_id,
            observationIds=[observation.id],
            startTime=incursion_finding.start_time,
            endTime=incursion_finding.end_time,
        )
        new_incursion_activity = self.oms_crud_tool.create_activity(incursion_activity)

        incursion_finding.atoms_id = new_incursion_activity.id
        incursion_finding.atoms_type = AtomsType.ACTIVITY

        return [incursion_finding]

    def _truncate_activity_description(self, description: str):
        max_descr_length = 512
        return description[:max_descr_length]
