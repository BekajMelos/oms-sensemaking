"""Module for calculating whether a node observation is in or out of garrison"""

from geopy.distance import geodesic
from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivitiesData,
    ActivityQuery,
    AttributeQuery,
    CreateActivityInput,
    GeoQuery,
    GeoQueryType,
    NodeNode,
    ObservationObservation,
    RelationshipNodeQuery,
    RelationshipQuery,
    StringQuery,
    UpdateActivityInput,
    UuidQueryByList,
)

from oms_sensemaking.clients.instances import oms_crud_tool
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.geo_helpers import generate_circle_points_geographical
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext
from oms_sensemaking.inference.rules.rule_helper_classes import GenericNodeTimeframe, TimeParsedObservation


class InOrOutOfGarrison(BaseRule):
    """
    Detect when a node is in or out of garrison and create/update the appropriate activity
    """

    def __init__(self, name: str):
        self.name = name
        self.version = (1, 0, 0)

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
        Determine if an observation indicates that a node is in or out of garrison

        :param rule_context: Rule context object containing the observation in question
        """

        obs = rule_context.observation
        node_object = oms_crud_tool.get_node(obs.nodeId)
        geo = obs.geometry

        # Find garrison node id through garrison relationship
        garrison_relationship_query = RelationshipQuery(
            objectPropertyIris=[SETTINGS.inference_garrisoned_in_iri],
            nodes=RelationshipNodeQuery(startNodeIds=[obs.nodeId]),
        )
        garrison_relationship_res = oms_crud_tool.get_relationships(garrison_relationship_query)

        if len(garrison_relationship_res.data):
            relationship = garrison_relationship_res.data[0]
            garrison_object_id = relationship.endNodeId

            # Find garrison coordinates through location attribute
            garrison_attribute_query = AttributeQuery(
                nodeIds=[garrison_object_id], attributeIris=[SETTINGS.inference_geo_attribute_iri]
            )
            garrison_attribute_res = oms_crud_tool.get_attributes(garrison_attribute_query)
            if len(garrison_attribute_res.data):
                garrison_object_coordinates = garrison_attribute_res.data[0].geometry["coordinates"]

                # Determine if object is in garrison
                object_coordinates = geo["coordinates"]
                object_coordinates = [object_coordinates[1], object_coordinates[0]]
                garrison_object_coordinates = [garrison_object_coordinates[1], garrison_object_coordinates[0]]
                distance = geodesic(object_coordinates, garrison_object_coordinates).kilometers
                in_garrison = distance < SETTINGS.garrison_distance_kilometers
                garrison_buffer_points = generate_circle_points_geographical(
                    garrison_object_coordinates[0],
                    garrison_object_coordinates[1],
                    SETTINGS.garrison_distance_kilometers,
                )

                garrison_buffer_geojson = {"type": "Polygon", "coordinates": [garrison_buffer_points]}

                self._create_or_update_garrison_activity(obs, node_object, in_garrison, garrison_buffer_geojson)

    def _create_or_update_garrison_activity(
        self, obs: ObservationObservation, node_object: NodeNode, in_garrison: bool, garrison_buffer_geojson: dict
    ):
        if in_garrison:
            activity_name = SETTINGS.inference_in_garrison_activity_name
            activity_state = SETTINGS.inference_in_garrison_activity_state
            geo_query = GeoQuery(queryGeoJson=garrison_buffer_geojson, queryType=GeoQueryType.DISJOINT)

        else:
            activity_name = SETTINGS.inference_out_of_garrison_activity_name
            activity_state = SETTINGS.inference_out_of_garrison_activity_state
            geo_query = GeoQuery(queryGeoJson=garrison_buffer_geojson, queryType=GeoQueryType.INTERSECTS)

        activity_query = ActivityQuery(
            name=StringQuery(equals=activity_name),
            state=StringQuery(equals=activity_state),
            nodeIds=UuidQueryByList(in_=[obs.nodeId]),
        )
        activity_response = oms_crud_tool.get_activities(activity_query)
        existing_activities = activity_response.data

        matching_activity_found = False

        enhanced_obs = TimeParsedObservation(obs)
        for existing_activity in existing_activities:
            enhanced_activity = GenericNodeTimeframe(existing_activity.startTime, existing_activity.endTime)
            # Update existing activity if times overlap or if node_object stayed in/out of
            # garrison in the time between the observation and activity
            time_overlap = enhanced_activity.does_observation_overlap(enhanced_obs)
            if time_overlap or enhanced_activity.object_observed_between_generic_node_and_observation_times(
                node_object, obs, geo_query
            ):
                # Update existing activity with union of observation and activity time intervals
                enhanced_activity.update_generic_node_times_with_observation(enhanced_obs)
                self._update_existing_activity(obs, existing_activity, enhanced_activity)
                matching_activity_found = True
                break

        # Observation not found as part of any existing garrison activity
        if not matching_activity_found:
            self._handle_new_activity(obs, activity_name, activity_state)

    def _update_existing_activity(
        self,
        observation: ObservationObservation,
        existing_activity: ActivitiesActivitiesData,
        enhanced_activity: GenericNodeTimeframe,
    ):
        """
        Update an existing activity with updated start/end times
        """

        # Update start/end times and add observation to garrison activity
        updated_activity_input = UpdateActivityInput(
            id=existing_activity.id,
            startTime=enhanced_activity.start_time.isoformat(),
            endTime=enhanced_activity.end_time.isoformat(),
            addObservationIds=[observation.id],
            nodeId=observation.nodeId,
        )
        oms_crud_tool.update_activity(updated_activity_input)

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
        oms_crud_tool.create_activity(garrison_activity)

    def has_action_already_ran(self, rule_context: RuleContext):
        """
        Determine if an in/out of garrison activity pointing to the inputted observation has already been created
        """

        obs = rule_context.observation
        if not obs:
            return False

        activity_query = ActivityQuery(observationIds=[obs.id])
        activities = oms_crud_tool.get_activities(activity_query).data

        return any(
            act.name == SETTINGS.inference_in_garrison_activity_name
            or act.name == SETTINGS.inference_out_of_garrison_activity_name
            for act in activities
        )
