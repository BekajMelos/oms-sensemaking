"""Module for calculating whether a node observation is in or out of garrison"""

from typing import Any, List, Optional

from geopy.distance import geodesic
from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivitiesData,
    ActivityQuery,
    CreateActivityInput,
    GeoQuery,
    GeoQueryType,
    NodeNode,
    ObservationObservation,
    StringQuery,
    UpdateActivityInput,
    UpdateUuidList,
    UuidQueryByList,
)
from oms_sdk.generated.generated_graphql_client.custom_fields import (
    AttributeFields,
    AttributePageFields,
    NodeFields,
    RelationshipFields,
    RelationshipPageFields,
)
from oms_sdk.generated.generated_graphql_client.custom_queries import Query
from oms_sdk.generated.generated_graphql_client.input_types import (
    AttributeFilter,
    IdQuery,
    NodeRelationshipFilter,
)

from oms_sensemaking.clients.instances import oms_crud_tool
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.geo_helpers import generate_circle_points_geographical
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext
from oms_sensemaking.inference.rules.rule_helper_classes import GeoTimeframe, Timeframe


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

        garrison_coords_lonlat = self._fetch_garrison_coords(obs.nodeId)

        if garrison_coords_lonlat:
            # obs.geometry is GeoJSON: [lon, lat]; convert both to [lat, lon] for geodesic()
            object_coordinates = obs.geometry["coordinates"]
            object_latlon = [object_coordinates[1], object_coordinates[0]]
            garrison_latlon = [garrison_coords_lonlat[1], garrison_coords_lonlat[0]]

            distance = geodesic(object_latlon, garrison_latlon).kilometers
            in_garrison = distance < SETTINGS.garrison_distance_kilometers

            garrison_buffer_points = generate_circle_points_geographical(
                garrison_latlon[0], garrison_latlon[1], SETTINGS.garrison_distance_kilometers
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
            states=[activity_state],
            nodeIds=UuidQueryByList(in_=[obs.nodeId]),
        )
        activity_response = oms_crud_tool.get_activities(activity_query)
        existing_activities = activity_response.data

        matching_activity_found = False

        enhanced_obs = Timeframe(obs)
        for existing_activity in existing_activities:
            enhanced_activity = GeoTimeframe(existing_activity.startTime, existing_activity.endTime)
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
        enhanced_activity: GeoTimeframe,
    ):
        """
        Update an existing activity with updated start/end times
        """

        # Update start/end times and add observation to garrison activity
        updated_activity_input = UpdateActivityInput(
            id=existing_activity.id,
            startTime=enhanced_activity.start_time.isoformat(),
            endTime=enhanced_activity.end_time.isoformat(),
            observationIds=UpdateUuidList(add=[observation.id]),
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

    def _fetch_garrison_coords(self, obs_node_id: str) -> Optional[List[float]]:
        """
        Return [lon, lat] for the home base of the observed node, or None.
        Uses a single operation via the SDK's custom operation builder.

        :param obs_node_id: Observation's nodeId
        """
        q = Query.node(IdQuery(id=obs_node_id)).fields(
            NodeFields.relationships(
                filter=NodeRelationshipFilter(objectPropertyIris=[SETTINGS.inference_garrisoned_in_iri])
            ).fields(
                RelationshipPageFields.data.on(
                    "RelationshipFields",
                    RelationshipFields.end_node().fields(
                        NodeFields.attributes(
                            filter=AttributeFilter(attributeIris=[SETTINGS.inference_geo_attribute_iri])
                        ).fields(
                            AttributePageFields.data.on(
                                "AttributeFields",
                                AttributeFields.geometry,
                            )
                        ),
                    ),
                )
            )
        )
        result = oms_crud_tool.oms_client.query(q, operation_name="InOutGarrison_HomeBaseWithGeo")

        def get(obj: Any, name: str):
            return getattr(obj, name, None) if not isinstance(obj, dict) else obj.get(name)

        node = get(result, "node")
        rels = get(get(node, "relationships"), "data") or []
        if not rels:
            return None

        end_node = get(rels[0], "end_node")
        attrs = get(get(end_node, "attributes"), "data") or []
        if not attrs:
            return None

        geometry = get(attrs[0], "geometry") or {}
        coords = geometry.get("coordinates")  # [lon, lat]
        return coords if isinstance(coords, list) and len(coords) >= 2 else None
