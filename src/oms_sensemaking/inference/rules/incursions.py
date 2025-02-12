import json

from dateutil.parser import isoparse
from oms_sdk.generated.generated_graphql_client import (
    ActivityQuery,
    ActivityState,
    AttributeQuery,
    AttributesAttributesData,
    AttributeType,
    CreateActivityInput,
    CreateAttributeInput,
    GeoQuery,
    IdQuery,
    NodeNode,
    NodesNodesData,
    ObservationObservation,
    ObservationQuery,
    StringQuery,
    TimeQuery,
    UpdateActivityInput,
    UpdateAttributeInput,
)

from data.areas_of_interest import features_list_from_geojson
from oms_sensemaking.clients.instances import oms_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext
from oms_sensemaking.tools.geo_tools import is_point_in_region


class Incursion(BaseRule):
    """
    Determine if an Observation indicates an incursion for the node it's associated
    with and make the appropriate attribute/activity updates
    """

    def __init__(self, name: str):
        self.name = name

    def evaluate(self, rule_context: RuleContext) -> bool:
        """
        Valid inputs must contain observations that have geometry and point to a node
        """
        if rule_context.observation:
            obs = rule_context.observation

        return rule_context.observation and obs.nodeId and obs.geometry

    def action(self, rule_context: RuleContext):
        """
        Create or update relevant incursion attribute/activity if observation indicates an incursion

        :param rule_context: Rule context object containing the observation to evaluate
        """

        obs = rule_context.observation
        # Fetch node that observation points to
        incurring_object = oms_client.get_node(IdQuery(id=obs.nodeId))
        geo = obs.geometry

        # Check if observation occurred in an area of interest
        features = features_list_from_geojson(SETTINGS.inference_incursion_areas_of_interest_path)
        geo_of_interest = None
        for feature in features:
            if is_point_in_region(geo, feature["geometry"]):
                geo_of_interest = feature["geometry"]
                break

        if geo_of_interest:
            # Check for existing incursions in the relevant geo of interest
            attribute_query = AttributeQuery(
                attributeIri=SETTINGS.inference_incursion_attribute_iri,
                attributeValue=StringQuery(equals="Incursion"),
                attributeType={"is": AttributeType.GEOSPATIAL},
                geometry=GeoQuery(queryGeoJson=json.dumps(geo_of_interest)),
                nodeIds=[incurring_object.id],
                tags=SETTINGS.incursion_tags,
            )
            attr_response = oms_client.get_attributes(attribute_query)
            existing_incursion_attributes = attr_response.data

            matching_incursion_attribute_found = False
            for existing_incursion_attribute in existing_incursion_attributes:
                # Check if times overlap
                obs_start_time = isoparse(obs.startTime)
                obs_end_time = isoparse(obs.endTime)
                existing_inc_start_time = isoparse(existing_incursion_attribute.valueStart)
                existing_inc_end_time = isoparse(existing_incursion_attribute.valueEnd)
                times_overlap = obs_end_time >= existing_inc_start_time and existing_inc_end_time >= obs_start_time
                if times_overlap:
                    # Update existing incursion with union of observation and incursion time intervals
                    updated_incursion_start_time = min(obs_start_time, existing_inc_start_time).isoformat()
                    updated_incursion_end_time = max(obs_end_time, existing_inc_end_time).isoformat()
                    updated_incursion_time = (updated_incursion_start_time, updated_incursion_end_time)
                    self._update_existing_incursion(
                        obs, incurring_object, updated_incursion_time, existing_incursion_attribute
                    )
                    matching_incursion_attribute_found = True
                    break
                else:
                    # Times don't overlap, check if object stayed in area of interest between
                    # observation and existing incursion times
                    update_existing_incursion, current_incursion_time = self._is_observation_part_of_existing_incursion(
                        incurring_object, obs, existing_incursion_attribute
                    )
                    if update_existing_incursion:
                        self._update_existing_incursion(
                            obs, incurring_object, current_incursion_time, existing_incursion_attribute
                        )
                        matching_incursion_attribute_found = True
                        break

            # Observation not found as part of any existing incursions in relevant area of interest
            if not matching_incursion_attribute_found:
                self._handle_new_incursion(obs, incurring_object, geo_of_interest)


    def _is_observation_part_of_existing_incursion(
        self,
        incurring_object: NodesNodesData,
        observation: ObservationObservation,
        existing_incursion_attribute: AttributesAttributesData
    ):
        """
        Check to see if incurring_object stayed in the relevant area of interest in the time separating the existing
        incursion and observation, which indicates whether or not that the observation is part of the
        existing incursion. Returns boolean indicating if the observation is part of the incursion and the
        updated incursion time
        """

        observation_start_time = isoparse(observation.startTime)
        attribute_start_time = isoparse(existing_incursion_attribute.valueStart)

        if observation_start_time < attribute_start_time:
            # Check for observations between current observation end time and attribute start time
            observation_query = ObservationQuery(
                nodeId=[incurring_object.id],
                startTime=TimeQuery(gte=observation.endTime),
                endTime=TimeQuery(lte=existing_incursion_attribute.valueStart),
            )
            observation_response = oms_client.get_observations(observation_query)
            if not observation_response.data:
                # No intermediate observations exist, current observation is part of existing incursion
                part_of_existing_incursion = True
                current_incursion_time = (observation.startTime, existing_incursion_attribute.valueEnd)
            else:
                # Intermediate observations exist, current observation is part of a new incursion
                part_of_existing_incursion = False
                current_incursion_time = (observation.startTime, observation.endTime)
        else:
            # Check for observations between attribute end time and current observation start time
            observation_query = ObservationQuery(
                nodeId=[incurring_object.id],
                startTime=TimeQuery(gte=existing_incursion_attribute.valueEnd),
                endTime=TimeQuery(lte=observation.startTime),
            )
            observation_response = oms_client.get_observations(observation_query)
            if not observation_response.data:
                # No intermediate observations exist, current observation is part of existing incursion
                part_of_existing_incursion = True
                current_incursion_time = (existing_incursion_attribute.valueStart, observation.endTime)
            else:
                # Intermediate observations exist, current observation is part of a new incursion
                part_of_existing_incursion = False
                current_incursion_time = (observation.startTime, observation.endTime)

        return (part_of_existing_incursion, current_incursion_time)

    def _update_existing_incursion(
        self,
        observation: ObservationObservation,
        incurring_object: NodesNodesData,
        current_incursion_time: tuple[str, str],
        existing_incursion_attribute: AttributesAttributesData,
    ):
        """
        Update an existing incursion attribute and corresponding activity
        with updated start/end times
        """

        # Fetch corresponding incursion activity
        activity_query = ActivityQuery(
            name=StringQuery(equals="Incursion"),
            nodeIds=[incurring_object.id],
            startTime=TimeQuery(gte=existing_incursion_attribute.valueStart),
            endTime=TimeQuery(lte=existing_incursion_attribute.valueEnd),
        )
        activity_response = oms_client.get_activities(activity_query)
        incursion_activity = activity_response.data[0]

        # Update start/end times and add observation to incursion activity
        updated_activity_input = UpdateActivityInput(
            id=incursion_activity.id,
            startTime=current_incursion_time[0],
            endTime=current_incursion_time[1],
            addObservationIds=[observation.id],
        )
        oms_client.update_activity(updated_activity_input)

        # Update start/end times of incursion attribute
        updated_attribute_input = UpdateAttributeInput(
            id=existing_incursion_attribute.id, startTime=current_incursion_time[0], endTime=current_incursion_time[1]
        )
        oms_client.update_attribute(updated_attribute_input)

    def _handle_new_incursion(self, observation: ObservationObservation, incurring_object: NodeNode, geo_of_interest):
        """
        Create new incursion attribute pointing to incurring_object and activity pointing to observation
        """

        # Create new incursion attribute pointing to incurring_object
        incursion_attribute = CreateAttributeInput(
            attributeIri=SETTINGS.inference_incursion_attribute_iri,
            attributeValue="Incursion",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=observation.confidence,
            sourceId=observation.sourceId,
            nodeId=incurring_object.id,
            acm=observation.acm,
            tags=SETTINGS.incursion_tags,
            geometry=json.dumps(geo_of_interest),
            valueStart=observation.startTime,
            valueEnd=observation.endTime,
        )
        oms_client.create_attribute(incursion_attribute)

        # Create new incursion activity pointing to observation
        incursion_activity = CreateActivityInput(
            acm=observation.acm,
            tags=SETTINGS.incursion_tags,
            name="Incursion",
            description=f"Incursion detected into {geo_of_interest}",  # edit based on actual geo of interests format
            state=ActivityState.UNKNOWN,
            nodeId=observation.nodeId,
            observationIds=[observation.id],
            startTime=observation.startTime,
            endTime=observation.endTime,
        )
        oms_client.create_activity(incursion_activity)

    def has_action_already_ran(self, rule_context: RuleContext):
        """
        Determine if an incursion activity pointing to the inputted observation has already been created
        """

        obs = rule_context.observation
        if not obs:
            return False

        activities = obs.activities.data
        return any(activity.name == "Incursion" for activity in activities)
