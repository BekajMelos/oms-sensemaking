"""Incursion Rule"""

import logging

from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivitiesData,
    ActivityQuery,
    AttributeQuery,
    AttributesAttributesData,
    AttributeType,
    CreateActivityInput,
    CreateAttributeInput,
    GeoQuery,
    GeoQueryType,
    NodeNode,
    ObservationObservation,
    StringQuery,
    UpdateActivityInput,
    UpdateAttributeInput,
    UpdateUuidList,
)
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from oms_sensemaking.clients.instances import oms_crud_tool
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.domain.area_of_interest.base import AOI, AOIExtractor
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext
from oms_sensemaking.inference.rules.rule_helper_classes import GeoTimeframe, Timeframe

LOGGER = logging.getLogger(__name__)


class Incursion(BaseRule):
    """
    Determine if an Observation indicates an incursion for the node it's associated
    with and make the appropriate attribute/activity updates
    """

    def __init__(self, name: str, aoi_extractor: AOIExtractor):
        self.name = name
        self.version = (1, 0, 0)
        self.features = aoi_extractor.get_areas_of_interest()

    def evaluate(self, rule_context: RuleContext) -> bool:
        """
        Valid inputs must contain observations that have geometry and point to a node

        :param rule_context: Rule context object containing the observation to evaluate
        """
        if (
            not rule_context.observation
            or rule_context.observation.startTime is None
            or rule_context.observation.endTime is None
        ):
            return False

        obs = rule_context.observation

        return obs and obs.nodeId and obs.geometry and obs.classIri != SETTINGS.track_iri

    def action(self, rule_context: RuleContext):
        """
        Create or update relevant incursion attribute/activity if observation indicates an incursion

        :param rule_context: Rule context object containing the observation to evaluate
        """

        obs = rule_context.observation
        # Fetch node that observation points to
        incurring_object = oms_crud_tool.get_node(obs.nodeId)
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
            existing_incursion_activities = oms_crud_tool.get_pages_of_activities("Incursion", incurring_object)
            matching_incursion_attribute_found = False

            LOGGER.debug("%d Existing Incursion Activities", len(existing_incursion_activities))

            for existing_incursion_activity in existing_incursion_activities:
                if matching_incursion_attribute_found:
                    break
                attribute_query = AttributeQuery(
                    attributeIris=[SETTINGS.inference_incursion_attribute_iri],
                    attributeValue=StringQuery(equals="Incursion"),
                    attributeType={"is": AttributeType.GEOSPATIAL},
                    geometry=GeoQuery(queryGeoJson=feature_of_interest.geometry_dict),
                    activityIds=[existing_incursion_activity.id],
                    tags=SETTINGS.incursion_tags,
                )
                attr_response = oms_crud_tool.get_attributes(attribute_query)
                existing_incursion_attributes = attr_response.data

                LOGGER.debug("%d Existing Incursion Attributes", len(existing_incursion_attributes))

                matching_incursion_attribute_found = self._check_existing_incursion_and_update(
                    obs,
                    incurring_object,
                    feature_of_interest,
                    existing_incursion_activity,
                    existing_incursion_attributes,
                    incursion_obs_timeframe,
                )

            # Observation not found as part of any existing incursions in relevant area of interest
            if not matching_incursion_attribute_found:
                self._handle_new_incursion(obs, incurring_object, feature_of_interest)

    def get_graph_data(self, rule_context: RuleContext):
        """
        Retrieve all data from Atoms API required for this rule.

        :param rule_context: Rule context object containing the observation in question
        """
        return

    def _check_existing_incursion_and_update(
        self,
        observation: ObservationObservation,
        incurring_obj: NodeNode,
        feat_of_int: AOI,
        existing_act: ActivitiesActivitiesData,
        existing_attributes: list[AttributesAttributesData],
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
                incurring_obj, observation, geo_query
            ):
                # Update existing incursion with union of observation and incursion time intervals
                inc_attr_geo_timeframe.update_generic_node_times_with_observation(obs_timeframe)
                self._update_existing_incursion(
                    observation, existing_act, existing_incursion_attribute, inc_attr_geo_timeframe
                )
                return True
        return False

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

        oms_crud_tool.update_incursion_activity_and_attributes(updated_activity_input, updated_attribute_input)

    def _handle_new_incursion(
        self, observation: ObservationObservation, incurring_object: NodeNode, feature_of_interest: AOI
    ):
        """
        Create new incursion attribute pointing to incurring_object and activity pointing to observation
        """

        # Create new incursion activity pointing to observation
        description = feature_of_interest.name
        if description is None:
            description = f"Incursion Activity by {incurring_object.name}"
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
        new_incursion_activity = oms_crud_tool.create_activity(incursion_activity)

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
        oms_crud_tool.create_attribute(incursion_attribute)

    def has_action_already_ran(self, rule_context: RuleContext):
        """
        Determine if an incursion activity pointing to the inputted observation has already been created
        """

        obs = rule_context.observation
        if not obs:
            return False

        activity_query = ActivityQuery(observationIds=[obs.id])
        activities = oms_crud_tool.get_activities(activity_query).data

        return any(activity.name == "Incursion" for activity in activities)

    def _truncate_activity_description(self, description: str):
        max_descr_length = 512
        return description[:max_descr_length]
