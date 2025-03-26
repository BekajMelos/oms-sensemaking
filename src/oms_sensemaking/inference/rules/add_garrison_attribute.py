
from dateutil.parser import isoparse
from geopy.distance import geodesic
from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivitiesData,
    ActivityQuery,
    ActivityState,
    ActivityStateQuery,
    AttributeQuery,
    CreateActivityInput,
    NodeNode,
    ObservationObservation,
    ObservationQuery,
    RelationshipNodeQuery,
    RelationshipQuery,
    StringQuery,
    TimeQuery,
    UpdateActivityInput,
)

from oms_sensemaking.clients.instances import oms_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext

IN_GARRISON_NAME = "In garrison"
OUT_OF_GARRISON_NAME = "Out of garrison"

class GarrisonObservation:
    def __init__(self, obs: ObservationObservation):
        self._obs = obs

        self.start_time = isoparse(obs.startTime)
        self.end_time = isoparse(obs.endTime)


class ActivityTimeframe:
    def __init__(self, activity: ActivitiesActivitiesData):
        self.start_time = isoparse(activity.startTime)
        self.end_time = isoparse(activity.endTime)

    def does_observation_overlap(self, obs: GarrisonObservation) -> bool:
        return obs.end_time >= self.start_time and self.end_time >= obs.start_time

    def update_activity_times_with_observation(self, obs: GarrisonObservation):
        self.start_time = min(obs.start_time, self.start_time)
        self.end_time = max(obs.end_time, self.end_time)

    def object_observed_between_activity_and_observation_times(
        self,
        object: NodeNode,
        observation: ObservationObservation,
    ) -> bool:
        """
        Check to see if object stayed in/out of garrison in the time separating the existing
        activity and observation, which indicates whether or not that the observation is part of the
        existing activity. Returns boolean indicating if the observation is part of the activity and the
        updated activity time
        """

        observation_start_time = isoparse(observation.startTime)

        if observation_start_time < self.start_time:
            # Check for observations between current observation end time and activity start time
            observation_query = ObservationQuery(
                nodeId=[object.id],
                startTime=TimeQuery(gt=observation.endTime),
                endTime=TimeQuery(lt=self.start_time.isoformat()),
            )
        else:
            # Check for observations between activity end time and current observation start time
            observation_query = ObservationQuery(
                nodeId=[object.id],
                startTime=TimeQuery(gt=self.end_time.isoformat()),
                endTime=TimeQuery(lt=observation.startTime),
            )
        observation_response = oms_client.get_observations(observation_query)
        part_of_existing_activity = bool(not observation_response.data)

        return part_of_existing_activity

class AddOutOfGarrisonAttribute(BaseRule):
    """
    Detect when a node is in or out of garrison and create/update the appropriate activity
    """

    def __init__(self, name: str):
        self.name = name

    def evaluate(self, rule_context: RuleContext) -> bool:
        """
        Valid inputs must contain observations that have geometry and point to a node

        :param rule_context: Rule context object containing the observation to evaluate
        """
        if rule_context.observation:
            obs = rule_context.observation

        return rule_context.observation and obs.nodeId and obs.geometry

    def action(self, rule_context: RuleContext):
        """
        Determine if an observation indicates that a node is in or out of garrison

        :param rule_context: Rule context object containing the observation in question
        """

        obs = rule_context.observation
        object = oms_client.get_node(obs.nodeId)
        geo = obs.geometry

        # Find garrison node id through garrison relationship
        garrison_relationship_query = RelationshipQuery(
            objectPropertyIris=[SETTINGS.inference_garrisoned_in_iri],
            nodes=RelationshipNodeQuery(
                startNodeIds=[obs.nodeId]
            )
        )
        garrison_relationship_res = oms_client.get_relationships(garrison_relationship_query)
        relationship = garrison_relationship_res.data[0]
        garrison_object_id = relationship.endNodeId

        # Find garrison coordinates through location attribute
        garrison_attribute_query = AttributeQuery(
            nodeIds=[garrison_object_id],
            attributeIris=[SETTINGS.inference_geo_attribute_iri]
        )
        garrison_attribute_res = oms_client.get_attributes(garrison_attribute_query)
        garrison_object_coordinates = garrison_attribute_res.data[0].geometry["coordinates"]

        # Determine if object is in garrison
        object_coordinates = geo["coordinates"]
        object_coordinates = [object_coordinates[1], object_coordinates[0]]
        garrison_object_coordinates = [garrison_object_coordinates[1], garrison_object_coordinates[0]]
        distance = geodesic(object_coordinates, garrison_object_coordinates).kilometers
        in_garrison = distance < SETTINGS.garrison_distance_kilometers

        self._create_or_update_garrison_activity(obs, object, in_garrison)

    def _create_or_update_garrison_activity(
        self,
        obs: ObservationObservation,
        object: NodeNode,
        in_garrison: bool
    ):
        if in_garrison:
            activity_name = SETTINGS.inference_in_garrison_activity_name
            activity_state = ActivityState.IN_GARRISON
        else:
            activity_name = SETTINGS.inference_out_of_garrison_activity_name
            activity_state = ActivityState.OUT_OF_GARRISON

        activity_query = ActivityQuery(
            name=StringQuery(equals=activity_name),
            state=ActivityStateQuery(is_=activity_state),
            nodeIds=[obs.nodeId]
        )
        activity_response = oms_client.get_activities(activity_query)
        existing_activities = activity_response.data

        matching_activity_found = False

        enhanced_obs = GarrisonObservation(obs)
        for existing_activity in existing_activities:
            enhanced_activity = ActivityTimeframe(existing_activity)
            # Update existing activity if times overlap or if object stayed in/out of
            # garrison in the time between the observation and activity
            time_overlap = enhanced_activity.does_observation_overlap(enhanced_obs)
            if time_overlap or enhanced_activity.object_observed_between_activity_and_observation_times(object, obs):
                # Update existing activity with union of observation and activity time intervals
                enhanced_activity.update_activity_times_with_observation(enhanced_obs)
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
        enhanced_activity: ActivityTimeframe
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
            nodeId=observation.nodeId
        )
        oms_client.update_activity(updated_activity_input)

    def _handle_new_activity(
        self,
        observation: ObservationObservation,
        activity_name: str,
        activity_state: ActivityState):
        """
        Create new activity pointing to observation
        """

        # Create in/out of garrison activity pointing to observation
        garrison_activity = CreateActivityInput(
            acm=observation.acm,
            classIri=SETTINGS.inference_garrison_class_iri,
            name=activity_name,
            state=activity_state,
            nodeId=observation.nodeId,
            observationIds=[observation.id],
            startTime=observation.startTime,
            endTime=observation.endTime,
        )
        oms_client.create_activity(garrison_activity)

    def has_action_already_ran(self, rule_context: RuleContext):
        """
        Determine if an in/out of garrison activity pointing to the inputted observation has already been created
        """

        obs = rule_context.observation
        if not obs:
            return False

        activity_query = ActivityQuery(observationIds=[obs.id])
        activities = oms_client.get_activities(activity_query).data

        return any(act.name == SETTINGS.inference_in_garrison_activity_name
                    or act.name == SETTINGS.inference_out_of_garrison_activity_name for act in activities)
