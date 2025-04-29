from oms_sdk.generated.generated_graphql_client import (
    ActivityQuery,
    AttributeQuery,
    AttributesAttributesData,
    AttributeType,
    CreateActivityInput,
    CreateAttributeInput,
    GeoQuery,
    NodeNode,
    NodesNodesData,
    ObservationObservation,
    StringQuery,
    TimeQuery,
    UpdateActivityInput,
    UpdateAttributeInput,
)
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from oms_sensemaking.clients.instances import oms_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.data.areas_of_interest.areas_of_interest import features_list_from_geojson
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext
from oms_sensemaking.inference.rules.rule_helper_classes import GenericNodeTimeframe, TimeParsedObservation


class Incursion(BaseRule):
    """
    Determine if an Observation indicates an incursion for the node it's associated
    with and make the appropriate attribute/activity updates
    """

    def __init__(self, name: str):
        self.name = name
        self.version = (1, 0, 0)
        self.features = features_list_from_geojson(SETTINGS.inference_incursion_areas_of_interest_path)

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
        Create or update relevant incursion attribute/activity if observation indicates an incursion

        :param rule_context: Rule context object containing the observation to evaluate
        """

        obs = rule_context.observation
        # Fetch node that observation points to
        incurring_object = oms_client.get_node(obs.nodeId)
        obs_geo: BaseGeometry = shape(obs.geometry)

        # Check if observation occurred in an area of interest
        geo_of_interest = None
        for feature in self.features:
            feature_region = shape(feature["geometry"])
            overlap = feature_region.intersection(obs_geo)
            if not overlap.is_empty:
                geo_of_interest = feature["geometry"]
                break

        if geo_of_interest:
            # Check for existing incursions in the relevant geo of interest
            attribute_query = AttributeQuery(
                attributeIris=[SETTINGS.inference_incursion_attribute_iri],
                attributeValue=StringQuery(equals="Incursion"),
                attributeType={"is": AttributeType.GEOSPATIAL},
                geometry=GeoQuery(queryGeoJson=geo_of_interest),
                nodeIds=[incurring_object.id],
                tags=SETTINGS.incursion_tags,
            )
            attr_response = oms_client.get_attributes(attribute_query)
            existing_incursion_attributes = attr_response.data

            matching_incursion_attribute_found = False

            incursion_obs = TimeParsedObservation(obs)
            for existing_incursion_attribute in existing_incursion_attributes:
                inc_attr = GenericNodeTimeframe(
                    existing_incursion_attribute.valueStart, existing_incursion_attribute.valueEnd
                )
                # Update existing incursion if times overlap or if object stayed in area of
                # interest in the time between the observation and incursion
                time_overlap = inc_attr.does_observation_overlap(incursion_obs)
                if time_overlap or inc_attr.object_observed_between_generic_node_and_observation_times(
                    incurring_object, obs
                ):
                    # Update existing incursion with union of observation and incursion time intervals
                    inc_attr.update_generic_node_times_with_observation(incursion_obs)
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
        inc_attr: GenericNodeTimeframe,
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
        activity_labels = incursion_activity.labels
        if activity_labels is None:
            activity_labels = []
        activity_labels.append(SETTINGS.sm_enriched_label)
        updated_activity_input = UpdateActivityInput(
            id=incursion_activity.id,
            startTime=inc_attr.start_time.isoformat(),
            endTime=inc_attr.end_time.isoformat(),
            addObservationIds=[observation.id],
            labels=activity_labels
        )
        oms_client.update_activity(updated_activity_input)

        # Update start/end times of incursion attribute
        attribute_labels = existing_incursion_attribute.labels
        if attribute_labels is None:
            attribute_labels = []
        attribute_labels.append(SETTINGS.sm_enriched_label)
        updated_attribute_input = UpdateAttributeInput(
            id=existing_incursion_attribute.id,
            valueStart=inc_attr.start_time.isoformat(),
            valueEnd=inc_attr.end_time.isoformat(),
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
            labels=[SETTINGS.sm_inferenced_label, SETTINGS.inference_sm_label,
                    SETTINGS.incursion_sm_label, self.version_string],
            geometry=geo_of_interest,
            valueStart=observation.startTime,
            valueEnd=observation.endTime,
        )
        oms_client.create_attribute(incursion_attribute)

        # Create new incursion activity pointing to observation
        incursion_activity = CreateActivityInput(
            acm=observation.acm,
            tags=SETTINGS.incursion_tags,
            labels=[SETTINGS.sm_inferenced_label, SETTINGS.inference_sm_label,
                    SETTINGS.incursion_sm_label, self.version_string],
            classIri=SETTINGS.inference_incursion_class_iri,
            name="Incursion",
            description=f"Incursion detected into {geo_of_interest}",  # edit based on actual geo of interests format
            state=SETTINGS.inference_incursion_activity_state,
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
