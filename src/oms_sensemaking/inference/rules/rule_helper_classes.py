from uuid import UUID

from dateutil.parser import isoparse
from oms_sdk.generated.generated_graphql_client import (
    GeoQuery,
    ObservationObservation,
    ObservationQuery,
    TimeQuery,
    UuidQueryByList,
)

from oms_sensemaking.clients.instances import oms_crud_tool


class Timeframe:
    def __init__(self, obs: ObservationObservation):
        self._obs = obs

        self.start_time = isoparse(obs.startTime)
        self.end_time = isoparse(obs.endTime)


class GeoTimeframe:
    def __init__(self, start_time, end_time):
        self.start_time = isoparse(start_time)
        self.end_time = isoparse(end_time)

    def does_observation_overlap(self, obs: Timeframe) -> bool:
        return obs.end_time >= self.start_time and self.end_time >= obs.start_time

    def update_generic_node_times_with_observation(self, obs: Timeframe):
        self.start_time = min(obs.start_time, self.start_time)
        self.end_time = max(obs.end_time, self.end_time)

    def object_observed_between_generic_node_and_observation_times(
        self,
        node_object_id: UUID,
        observation: ObservationObservation,
        geo_query: GeoQuery = None,
    ) -> bool:
        """
        Check to see if an observation occurred in the time separating the generic nodes's timeframe and
        observation's timeframe, which indicates whether or not that the observation should be pointing
        to the existing generic node. Returns boolean indicating if the observation should be pointing to
        the existing generic node
        """

        observation_start_time = isoparse(observation.startTime)

        if observation_start_time < self.start_time:
            # Check for observations between current observation end time and generic node start time
            observation_query = ObservationQuery(
                nodeIds=UuidQueryByList(in_=[node_object_id]),
                startTime=TimeQuery(gte=observation.endTime),
                endTime=TimeQuery(lt=self.start_time.isoformat()),
                geometry=geo_query,
            )
        else:
            # Check for observations between generic end time and current observation start time
            observation_query = ObservationQuery(
                nodeIds=UuidQueryByList(in_=[node_object_id]),
                startTime=TimeQuery(gt=self.end_time.isoformat()),
                endTime=TimeQuery(lte=observation.startTime),
                geometry=geo_query,
            )
        observation_response = oms_crud_tool.get_observations(observation_query)
        part_of_existing_generic_node = bool(not observation_response.data)

        return part_of_existing_generic_node
