
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
    NodeNode,
    NodesNodesData,
    ObservationObservation,
    ObservationQuery,
    StringQuery,
    TimeQuery,
    UpdateActivityInput,
    UpdateAttributeInput,
)
from shapely import Point
from shapely.geometry import shape

from oms_sensemaking.clients.instances import oms_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.data.areas_of_interest.areas_of_interest import features_list_from_geojson
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext


class IncursionObservation:
    def __init__(self, obs: ObservationObservation):
        self._obs = obs

        self.start_time = isoparse(obs.startTime)
        self.end_time = isoparse(obs.endTime)


class IncursionTimeframe:
    def __init__(self, attr: AttributesAttributesData):
        self.start_time = isoparse(attr.valueStart)
        self.end_time = isoparse(attr.valueEnd)

    def does_observation_overlap(self, obs: IncursionObservation) -> bool:
        return obs.end_time >= self.start_time and self.end_time >= obs.start_time

    def update_incursion_times_with_observation(self, obs: IncursionObservation):
        self.start_time = min(obs.start_time, self.start_time)
        self.end_time = max(obs.end_time, self.end_time)

    def object_observed_between_incursion_and_observation_times(
        self,
        incurring_object: NodesNodesData,
        observation: ObservationObservation,
    ) -> bool:
        """
        Check to see if incurring_object stayed in the relevant area of interest in the time separating the existing
        incursion and observation, which indicates whether or not that the observation is part of the
        existing incursion. Returns boolean indicating if the observation is part of the incursion and the
        updated incursion time
        """

        observation_start_time = isoparse(observation.startTime)

        if observation_start_time < self.start_time:
            # Check for observations between current observation end time and attribute start time
            observation_query = ObservationQuery(
                nodeId=[incurring_object.id],
                startTime=TimeQuery(gt=observation.endTime),
                endTime=TimeQuery(lt=self.start_time.isoformat()),
            )
        else:
            # Check for observations between attribute end time and current observation start time
            observation_query = ObservationQuery(
                nodeId=[incurring_object.id],
                startTime=TimeQuery(gt=self.end_time.isoformat()),
                endTime=TimeQuery(lt=observation.startTime),
            )
        observation_response = oms_client.get_observations(observation_query)
        part_of_existing_incursion = bool(not observation_response.data)

        return part_of_existing_incursion


class Incursion(BaseRule):
    """
    Determine if an Observation indicates an incursion for the node it's associated
    with and make the appropriate attribute/activity updates
    """

    def __init__(self, name: str):
        self.name = name
        self.features = features_list_from_geojson(SETTINGS.inference_incursion_areas_of_interest_path)

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
        incurring_object = oms_client.get_node(obs.nodeId)
        geo = obs.geometry

        # Check if observation occurred in an area of interest
        geo_of_interest = None
        for feature in self.features:
            point_coordinates = geo["coordinates"]
            shapely_region = shape(feature["geometry"])
            shapely_point = Point(point_coordinates)
            if shapely_region.contains(shapely_point):
                geo_of_interest = feature["geometry"]
                break

        if geo_of_interest:
            # Check for existing incursions in the relevant geo of interest
            attribute_query = AttributeQuery(
                attributeIri=SETTINGS.inference_incursion_attribute_iri,
                attributeValue=StringQuery(equals="Incursion"),
                attributeType={"is": AttributeType.GEOSPATIAL},
                geometry=GeoQuery(queryGeoJson=geo_of_interest),
                nodeIds=[incurring_object.id],
                tags=SETTINGS.incursion_tags,
            )
            attr_response = oms_client.get_attributes(attribute_query)
            existing_incursion_attributes = attr_response.data

            matching_incursion_attribute_found = False

            incursion_obs = IncursionObservation(obs)
            for existing_incursion_attribute in existing_incursion_attributes:
                inc_attr = IncursionTimeframe(existing_incursion_attribute)
                # Update existing incursion if times overlap or if object stayed in area of
                # interest in the time between the observation and incursion
                time_overlap = inc_attr.does_observation_overlap(incursion_obs)
                if time_overlap or inc_attr.object_observed_between_incursion_and_observation_times(incurring_object,
                                                                                                    obs):
                    # Update existing incursion with union of observation and incursion time intervals
                    inc_attr.update_incursion_times_with_observation(incursion_obs)
                    self._update_existing_incursion(obs, incurring_object, existing_incursion_attribute, inc_attr)
                    matching_incursion_attribute_found = True
                    break

            # Observation not found as part of any existing incursions in relevant area of interest
            if not matching_incursion_attribute_found:
                self._handle_new_incursion(obs, incurring_object, geo_of_interest)

    def _update_existing_incursion(
        self,
        observation: ObservationObservation,
        incurring_object: NodesNodesData,
        existing_incursion_attribute: AttributesAttributesData,
        inc_attr: IncursionTimeframe,
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
            startTime=inc_attr.start_time.isoformat(),
            endTime=inc_attr.end_time.isoformat(),
            addObservationIds=[observation.id],
        )
        oms_client.update_activity(updated_activity_input)

        # Update start/end times of incursion attribute
        updated_attribute_input = UpdateAttributeInput(
            id=existing_incursion_attribute.id,
            valueStart=inc_attr.start_time.isoformat(),
            valueEnd=inc_attr.end_time.isoformat()
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
            geometry=geo_of_interest,
            valueStart=observation.startTime,
            valueEnd=observation.endTime,
        )
        oms_client.create_attribute(incursion_attribute)

        # Create new incursion activity pointing to observation
        incursion_activity = CreateActivityInput(
            acm=observation.acm,
            tags=SETTINGS.incursion_tags,
            classIri=SETTINGS.inference_incursion_class_iri,
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

        activity_query = ActivityQuery(observationIds=[obs.id])
        activities = oms_client.get_activities(activity_query).data

        return any(activity.name == "Incursion" for activity in activities)
