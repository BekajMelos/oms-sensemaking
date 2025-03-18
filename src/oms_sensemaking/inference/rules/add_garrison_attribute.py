from dateutil.parser import isoparse
from geopy.distance import geodesic
from oms_sdk.generated.generated_graphql_client import (
    ActivityQuery,
    ActivityState,
    AttributeQuery,
    AttributesAttributesData,
    AttributeType,
    CreateActivityInput,
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

from oms_sensemaking.clients.instances import oms_client
from oms_sensemaking.config import SETTINGS
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

class AddOutOfGarrisonAttribute(BaseRule):
    """
    Detect when a node has a geolocation attribute,
    when a node has a geolocation attribute, compare it to garrison and add/update a new OutOfGarrison attribute
    pointing to the node
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

        :param rule_context: Rule context object containing the observation to evaluate
        """

        obs = rule_context.observation
        # Fetch node that observation points to
        garrison_object = oms_client.get_node(obs.nodeId)
        # Ensure object is right type ###### COME BACK TO THIS
        geo = obs.geometry

        # Check if object is garrisoned ######COME BACK TO THIS
        geo_of_interest = None
        point_coordinates = geo["coordinates"]

        if geo_of_interest:
            self._create_or_update_garrison_activity(obs, garrison_object, geo)
            # Check for existing garrison activities in the relevant geo of interest
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
        # Library to calculate distances between coordinates in kilometers
        # distance = geodesic(geo_coordinates_1, geo_coordinates_2).kilometers

        # # Checks if the distance between coordinates is smaller than the requested distance
        # final_attribute_value = "Yes" if distance < SETTINGS.garrison_distance_kilometers else "No"

        # # Creates a new attribute with the correct Attribute Value
        # attribute_out_of_garrison = CreateAttributeInput(
        #     attributeIri=SETTINGS.inference_add_in_garrison_iri,
        #     attributeValue=final_attribute_value,
        #     attributeType=AttributeType.STRING,
        #     confidence=attr.confidence,
        #     sourceId=attr.sourceId,
        #     acm=attr.acm,
        #     isMutable=False,
        #     tags=SETTINGS.inference_tags,
        # )
        # oms_client.create_attribute(attribute_out_of_garrison)

    def _create_garrison_activity(self,
                                  observation: ObservationObservation,
                                  incurring_object: NodeNode,
                                  geo_of_interest):
        """
        Create new incursion attribute pointing to incurring_object and activity pointing to observation
        """

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
        Determine if a metadata attribute has already been created for a node
        """

        attr = rule_context.attribute
        if not attr:
            return False

        attribute_query = AttributeQuery(
            attributeIri=SETTINGS.inference_add_in_garrison_iri,
            attributeValue=StringQuery(equals="Yes"),  # Yes or No, will check if this works
            attributeType={
                "is": AttributeType.STRING,
            },
            confidence={"is": (attr.confidence)},
            sourceId=attr.sourceId,
            nodeIds=[attr.nodeId],
            tags=SETTINGS.inference_tags,
        )

        res = oms_client.get_attributes(attribute_query)

        return len(res.data) > 0
