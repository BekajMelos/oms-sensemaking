import json

from dateutil.parser import isoparse
from shapely.geometry import Point, Polygon
from oms_sdk.generated.generated_graphql_client import (
    AttributeType,
    ActivityState,
    ObservationObservation,
    NodesNodesData,
    AttributesAttributesData,
    AttributeQuery,
    CreateAttributeInput,
    CreateActivityInput,
    NodeQuery,
    StringQuery,
    ActivityQuery,
    TimeQuery,
    UpdateActivityInput,
    ObservationQuery,
    GeoQuery,
    UpdateAttributeInput
)
from oms_sensemaking.clients import oms_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.inference.rules.base_rule import BaseRule
from oms_sensemaking.inference.rules.rule_context import RuleContext


class Incursion(BaseRule):
    """
    Determine if an Observation indicates an incursion for the node it's associated with and make the appropriate attribute/activity updates
    """

    def __init__(self, name: str):
        self.name = name

    def evaluate(self, input: RuleContext) -> bool:
        """
        Valid inputs must contain observations that have geometry and point to a node  
        """
        if input.observation: 
            obs = input.observation
            
        return (
            input.observation
            and obs.nodeId
            and obs.geometry 
        )

    def action(self, input: RuleContext):
        """
        Create or update relevant incursion attribute/activity if observation indicates an incursion 
        """

        obs = input.observation
        # Fetch node that observation points to
        node_response = oms_client.get_nodes(NodeQuery(
            ids=[obs.nodeId]
        ))
        parent_node = node_response.data[0]
        geo = obs.geometry

        # Check if observation occurred in an area of interest (temp, change after getting actual format)
        with open('./tests/inference/rules/test_data/areas_of_interest/geos_of_interest.json', 'r') as file:
            features = json.load(file)["features"]

        potential_geos_of_interest = [feature["geometry"] for feature in features]
        geo_of_interest = None
        for polygon in potential_geos_of_interest:
            if self._is_point_in_polygon(geo, polygon):
                geo_of_interest = polygon
                break

        if geo_of_interest:
            # Check for existing incursions in the relevant geo of interest
            attribute_query = AttributeQuery(
                attributeIri=SETTINGS.inference_add_has_name_attribute_meta_data_iri,
                attributeValue=StringQuery(equals="Incursion"),
                attributeType={"is": AttributeType.GEOSPATIAL},
                geometry=GeoQuery(queryGeoJson=json.dumps(geo_of_interest)),
                nodeIds=[parent_node.id],
                tags=SETTINGS.incursion_tags
            )
            attr_response = oms_client.get_attributes(attribute_query)
            existing_incursion_attributes = attr_response.data

            matching_incursion_attribute_found = False
            for existing_incursion_attribute in existing_incursion_attributes:
                # Check if times overlap
                obs_time = (obs.startTime, obs.endTime)
                existing_incursion_time = (existing_incursion_attribute.valueStart, existing_incursion_attribute.valueEnd)
                time_overlap, current_incursion_time = self._compare_times((obs.startTime, obs.endTime), existing_incursion_time)
                if time_overlap:
                    # Times overlap, updating existing incursion
                    self._update_existing_incursion(obs, parent_node, current_incursion_time, existing_incursion_attribute)
                    matching_incursion_attribute_found = True
                    break
                else:
                    # Times don't overlap, check if any observations occured between observation and existing incursion in question
                    part_of_existing_incursion, current_incursion_time = self._check_observations_between(parent_node, obs_time, existing_incursion_attribute)
                    if part_of_existing_incursion:
                        self._update_existing_incursion(obs, parent_node, current_incursion_time, existing_incursion_attribute)
                        matching_incursion_attribute_found = True
                        break
                    
            # Observation not found as part of any existing incursions in relevant area of interest
            if not matching_incursion_attribute_found:            
                self._handle_new_incursion(obs, parent_node, geo_of_interest)
    
    def _is_point_in_polygon(self, point, polygon):
        point_coordinates = point["coordinates"]
        polygon_coordinates = polygon["coordinates"][0]
        polygon = Polygon(polygon_coordinates)
        point = Point(point_coordinates)
        
        return polygon.contains(point)

    def _compare_times(self, observation_time, existing_incursion_time):
        observation_start_time = isoparse(observation_time[0])
        observation_end_time = isoparse(observation_time[1])
        attribute_start_time = isoparse(existing_incursion_time[0])
        attribute_end_time = isoparse(existing_incursion_time[1])

        # Return union of intervals if overlap, observation time otherwise
        overlap = observation_end_time >= attribute_start_time and attribute_end_time >= observation_start_time
        if overlap:
            return (True, (min(observation_start_time, attribute_start_time).isoformat(), max(observation_end_time, attribute_end_time).isoformat()))
        else:
            return (False, observation_time)

    def _check_observations_between(self, parent_node, observation_time, existing_incursion_attribute: AttributesAttributesData):
        # Check to see if nonoverlapping observation occurs before or after existing incursion
        observation_start_time = isoparse(observation_time[0])
        attribute_start_time = isoparse(existing_incursion_attribute.valueStart)

        if observation_start_time < attribute_start_time:
            # Check for observations between current observation end time and attribute start time
            observation_query = ObservationQuery(
                nodeId=[parent_node.id],
                startTime=TimeQuery(gte = observation_time[1]),
                endTime=TimeQuery(lte = existing_incursion_attribute.valueStart)
            )
            observation_response = oms_client.get_observations(observation_query)
            if len(observation_response.data) == 0:
                # No intermediate observations exist, current observation is part of existing incursion
                part_of_existing_incursion = True
                current_incursion_time = (observation_time[0], existing_incursion_attribute.valueEnd)
            else: 
                # Intermediate observations exist, current observation is part of a new incursion
                part_of_existing_incursion = False
                current_incursion_time = observation_time
        else:
            # Check for observations between attribute end time and current observation start time
            observation_query = ObservationQuery(
                nodeId=[parent_node.id],
                startTime=TimeQuery(gte = existing_incursion_attribute.valueEnd),
                endTime=TimeQuery(lte = observation_time[0])
            )
            observation_response = oms_client.get_observations(observation_query)
            if len(observation_response.data) == 0:
                # No intermediate observations exist, current observation is part of existing incursion
                part_of_existing_incursion = True
                current_incursion_time = (existing_incursion_attribute.valueStart, observation_time[1])
            else:
                # Intermediate observations exist, current observation is part of a new incursion
                part_of_existing_incursion = False
                current_incursion_time = observation_time 

        return (part_of_existing_incursion, current_incursion_time)  
  
    def _update_existing_incursion(self, observation: ObservationObservation, parent_node, current_incursion_time, existing_incursion_attribute: AttributesAttributesData):
        # Fetch corresponding incursion activity
        activity_query = ActivityQuery(
            name=StringQuery(equals="Incursion"),
            nodeIds=[parent_node.id],
            startTime=TimeQuery(gte = existing_incursion_attribute.valueStart),
            endTime=TimeQuery(lte = existing_incursion_attribute.valueEnd)
        )
        activity_response = oms_client.get_activities(activity_query)
        incursion_activity = activity_response.data[0]

        # Update start/end times and add observation to incursion activity
        updated_activity_input = UpdateActivityInput(
            id=incursion_activity.id,
            startTime=current_incursion_time[0],
            endTime=current_incursion_time[1],
            addObservationIds=[observation.id]
        )
        oms_client.update_activity(updated_activity_input)
        
        # Update start/end times of incursion attribute
        updated_attribute_input = UpdateAttributeInput(
            id=existing_incursion_attribute.id,
            startTime=current_incursion_time[0],
            endTime=current_incursion_time[1]
        )
        oms_client.update_attribute(updated_attribute_input)
    
    def _handle_new_incursion(self, observation: ObservationObservation, parent_node: NodesNodesData, geo_of_interest):
        # Create new incursion attribute for parent node
        incursion_attribute = CreateAttributeInput(
            attributeIri=SETTINGS.inference_incursion_attribute_iri,
            attributeValue="Incursion",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=observation.confidence,
            sourceId=observation.sourceId, #change to config value
            nodeId=parent_node.id,
            acm=observation.acm,
            tags=SETTINGS.incursion_tags,
            geometry=json.dumps(geo_of_interest),
            valueStart=observation.startTime,
            valueEnd=observation.endTime
        )
        oms_client.create_attribute(incursion_attribute)
    
        # Create new incursion activity for parent node and observation
        incursion_activity = CreateActivityInput(
            acm=observation.acm,
            tags=SETTINGS.incursion_tags,
            name="Incursion",
            description=f"Incursion detected into {geo_of_interest}", # edit based on actual geo of interests format
            state=ActivityState.UNKNOWN,
            nodeId=observation.nodeId,
            observationIds=[observation.id],
            startTime=observation.startTime,
            endTime=observation.endTime
        )
        oms_client.create_activity(incursion_activity)

    def has_action_already_ran(self, input: RuleContext):
        """
        Determine if an incursion activity pointing to the inputted observation has already been created 
        """

        obs = input.observation
        if not obs:
            return False

        activities = obs.activities.data
        for activity in activities:
            if activity.name == "Incursion":
                return True
        return False


