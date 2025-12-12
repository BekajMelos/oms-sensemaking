"""Incursion Rule"""

import logging
from uuid import UUID

from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivitiesData,
    ActivityQuery,
    AttributesAttributesData,
    AttributeType,
    AttributeTypeQuery,
    CreateActivityInput,
    CreateAttributeInput,
    GeoQuery,
    GeoQueryType,
    IncursionDataActivitiesData,
    IncursionDataActivitiesDataAttributesData,
    ObservationObservation,
    PageParams,
    StringQuery,
    UpdateActivityInput,
    UpdateAttributeInput,
    UpdateUuidList,
    UuidQueryByList,
)
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.domain.area_of_interest.base import AOI, AOIExtractor
from oms_sensemaking.inference.rules.rule_helper_classes import GeoTimeframe, Timeframe

LOGGER = logging.getLogger(__name__)


class Incursion(Sensemaker):
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

        :param rule_context: Rule context object containing the observation to evaluate
        """
        if not obs or obs.startTime is None or obs.endTime is None:
            return False

        return obs and obs.nodeId and obs.geometry and obs.classIri != SETTINGS.track_iri

    def process_data(self, obs: ObservationObservation, config: dict | None = None):
        """
        Create or update relevant incursion attribute/activity if observation indicates an incursion

        :param rule_context: Rule context object containing the observation to evaluate
        """
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
            # Check if observation has already been run on after ensuring
            # the observation falls within a feature of interest, does not waste a request early on
            if self.has_action_already_ran(obs):
                return []
            # can we include geo?
            LOGGER.debug("Incursion detected for Observation: %s", obs.id)
            # Fetch node id that observation points to
            incurring_object_id = obs.nodeId
            incursion_obs_timeframe = Timeframe(obs)
            # Check for existing incursions in the relevant geo of interest
            existing_incursion_activities = self.get_all_incursion_data(
                incurring_object_id=incurring_object_id, feature_of_interest=feature_of_interest
            )
            matching_incursion_attribute_found = False

            LOGGER.debug("%d Existing Incursion Activities", len(existing_incursion_activities))

            for existing_incursion_activity in existing_incursion_activities:
                if matching_incursion_attribute_found:
                    break
                existing_incursion_attributes = existing_incursion_activity.attributes.data

                LOGGER.debug("%d Existing Incursion Attributes", len(existing_incursion_attributes))

                matching_incursion_attribute_found = self._check_existing_incursion_and_update(
                    obs,
                    incurring_object_id,
                    feature_of_interest,
                    existing_incursion_activity,
                    existing_incursion_attributes,
                    incursion_obs_timeframe,
                )

            # Observation not found as part of any existing incursions in relevant area of interest
            if not matching_incursion_attribute_found:
                self._handle_new_incursion(obs, incurring_object_id, feature_of_interest)
        return []

    def _check_existing_incursion_and_update(
        self,
        observation: ObservationObservation,
        incurring_obj_id: UUID,
        feat_of_int: AOI,
        existing_act: IncursionDataActivitiesData,
        existing_attributes: list[IncursionDataActivitiesDataAttributesData],
        obs_timeframe: Timeframe,
    ) -> bool:
        """
        function to check for existing incursions given an activity object
        and its connected attributes
        """
        for existing_incursion_attribute in existing_attributes:
            inc_attr_geo_timeframe = GeoTimeframe(
                existing_incursion_attribute.valueStart, existing_incursion_attribute.valueEnd
            )
            # Update existing incursion if times overlap or if object stayed in area of
            # interest in the time between the observation and incursion
            time_overlap = inc_attr_geo_timeframe.does_observation_overlap(obs_timeframe)
            geo_query = GeoQuery(queryGeoJson=(feat_of_int.geometry_dict), queryType=GeoQueryType.DISJOINT)
            if time_overlap or inc_attr_geo_timeframe.object_observed_between_generic_node_and_observation_times(
                incurring_obj_id, observation, geo_query
            ):
                # Update existing incursion with union of observation and incursion time intervals
                inc_attr_geo_timeframe.update_generic_node_times_with_observation(obs_timeframe)
                self._update_existing_incursion(
                    observation, existing_act, existing_incursion_attribute, inc_attr_geo_timeframe
                )
                return True
        return False

    def get_all_incursion_data(self, incurring_object_id: UUID, feature_of_interest: AOI, pagesize: int = 200):
        incursion_activities: list[IncursionDataActivitiesData] = []
        page = 1
        while True:
            activity_query = ActivityQuery(
                name=StringQuery(equals="Incursion"),
                nodeIds=UuidQueryByList(in_=[incurring_object_id]),
                pageParams=PageParams(page=page, pageSize=pagesize),
            )
            response = self.oms_crud_tool.oms_client.incursion_data(
                query=activity_query,
                incursionAttributeValue=StringQuery(equals="Incursion"),
                incursionAttributeIris=[SETTINGS.inference_incursion_attribute_iri],
                incursionAttributeType=AttributeTypeQuery(is_=AttributeType.GEOSPATIAL),
                attributeGeometry=GeoQuery(queryGeoJson=feature_of_interest.geometry_dict),
                incursionTags=SETTINGS.incursion_tags,
            )
            activities_layer = response.data
            if not activities_layer:
                break
            # Get all pages of incurison data
            incursion_activities.extend(activities_layer)
            if len(activities_layer) < pagesize:
                break
            page += 1
        return incursion_activities

    def _update_existing_incursion(
        self,
        observation: ObservationObservation,
        existing_incursion_activity: ActivitiesActivitiesData,
        existing_incursion_attribute: AttributesAttributesData,
        inc_attr_geo_timeframe: GeoTimeframe,
    ):
        """
        Update an existing incursion attribute and corresponding activity
        with updated start/end times
        """

        # Update start/end times and add observation to incursion activity
        activity_labels = existing_incursion_activity.labels
        if activity_labels is None:
            activity_labels = []
        activity_labels.append(SETTINGS.sm_enriched_label)
        updated_activity_input = UpdateActivityInput(
            id=existing_incursion_activity.id,
            startTime=inc_attr_geo_timeframe.start_time.isoformat(),
            endTime=inc_attr_geo_timeframe.end_time.isoformat(),
            observationIds=UpdateUuidList(add=[observation.id]),
            labels=activity_labels,
        )
        self.oms_crud_tool.update_activity(updated_activity_input)

        # Update start/end times of incursion attribute
        attribute_labels = existing_incursion_attribute.labels
        if attribute_labels is None:
            attribute_labels = []
        attribute_labels.append(SETTINGS.sm_enriched_label)
        updated_attribute_input = UpdateAttributeInput(
            id=existing_incursion_attribute.id,
            valueStart=inc_attr_geo_timeframe.start_time.isoformat(),
            valueEnd=inc_attr_geo_timeframe.end_time.isoformat(),
            labels=attribute_labels,
        )
        self.oms_crud_tool.update_attribute(updated_attribute_input)

    def _handle_new_incursion(
        self, observation: ObservationObservation, incurring_object_id: UUID, feature_of_interest: AOI
    ):
        """
        Create new incursion attribute pointing to incurring_object and activity pointing to observation
        """

        # Create new incursion activity pointing to observation
        description = feature_of_interest.name
        if description is None:
            description = f"Incursion Activity by {incurring_object_id}"
        incursion_activity = CreateActivityInput(
            acm=observation.acm,
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
            nodeId=observation.nodeId,
            observationIds=[observation.id],
            startTime=observation.startTime,
            endTime=observation.endTime,
        )
        new_incursion_activity = self.oms_crud_tool.create_activity(incursion_activity)

        # Create new incursion attribute pointing to activity describing incurring object
        incursion_attribute = CreateAttributeInput(
            attributeIri=SETTINGS.inference_incursion_attribute_iri,
            attributeValue="Incursion",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=observation.confidence,
            sourceId=observation.sourceId,
            activityId=new_incursion_activity.id,
            acm=observation.acm,
            tags=SETTINGS.incursion_tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.inference_sm_label,
                SETTINGS.incursion_sm_label,
                self.version_string,
            ],
            geometry=(feature_of_interest.geometry_dict),
            valueStart=observation.startTime,
            valueEnd=observation.endTime,
        )
        self.oms_crud_tool.create_attribute(incursion_attribute)

    def has_action_already_ran(self, obs: ObservationObservation):
        """
        Determine if an incursion activity pointing to the inputted observation has already been created
        """

        if not obs:
            return False

        activity_query = ActivityQuery(observationIds=[obs.id])
        activities = self.oms_crud_tool.get_activities(activity_query).data

        return any(activity.name == "Incursion" for activity in activities)

    def _truncate_activity_description(self, description: str):
        max_descr_length = 512
        return description[:max_descr_length]
