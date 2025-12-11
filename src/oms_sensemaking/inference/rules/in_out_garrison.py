"""Module for calculating whether a node observation is in or out of garrison"""

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

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.geo_helpers import generate_circle_points_geographical
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.domain.in_or_out_garrison.utils import in_garrison
from oms_sensemaking.inference.rules.garrison_data_collection import GetGarrisonDataRetrieverFactory
from oms_sensemaking.inference.rules.rule_helper_classes import GeoTimeframe, Timeframe


class InOrOutOfGarrison(Sensemaker):
    """
    Detect when a node is in or out of garrison and create/update the appropriate activity
    """

    def __init__(self, oms_crud_tool: OmsCrudTool):
        super().__init__()
        self.oms_crud_tool = oms_crud_tool
        self.name = self.__class__.__name__
        self.version = (1, 0, 0)
        self._data_retriever = GetGarrisonDataRetrieverFactory(self.oms_crud_tool).get_garrison_data_retriever(
            SETTINGS.garrison_data_retriever
        )

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
        Determine if an observation indicates that a node is in or out of garrison

        :param rule_context: Rule context object containing the observation in question
        """

        if not self.evaluate(obs) or self.has_action_already_ran(obs):
            return []
        node_object = self.oms_crud_tool.get_node(obs.nodeId)
        object_and_garrison_coords = self._data_retriever.get_all_garrison_data(obs)
        if not object_and_garrison_coords:
            return []
        object_lat_lon, garrison_lat_lon = object_and_garrison_coords
        in_garrison_check = in_garrison(object_lat_lon, garrison_lat_lon)
        garrison_buffer_points = generate_circle_points_geographical(
            garrison_lat_lon[0], garrison_lat_lon[1], SETTINGS.garrison_distance_kilometers
        )
        garrison_buffer_geojson = {"type": "Polygon", "coordinates": [garrison_buffer_points]}

        self._create_or_update_garrison_activity(obs, node_object, in_garrison_check, garrison_buffer_geojson)
        return []

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
        activity_response = self.oms_crud_tool.get_activities(activity_query)
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
        self.oms_crud_tool.update_activity(updated_activity_input)

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
        self.oms_crud_tool.create_activity(garrison_activity)

    def has_action_already_ran(self, obs: ObservationObservation):
        """
        Determine if an in/out of garrison activity pointing to the inputted observation has already been created
        """

        if not obs:
            return False

        activity_query = ActivityQuery(observationIds=[obs.id])
        activities = self.oms_crud_tool.get_activities(activity_query).data

        return any(
            act.name == SETTINGS.inference_in_garrison_activity_name
            or act.name == SETTINGS.inference_out_of_garrison_activity_name
            for act in activities
        )
