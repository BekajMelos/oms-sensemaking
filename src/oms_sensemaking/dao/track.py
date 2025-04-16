from typing import Any

from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    Confidence,
    CreateObservationCreateObservation,
    CreateObservationInput,
)

from oms_sensemaking.clients.instances import oms_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.models.geo import Track


class APITrack:
    acm: Any
    track: Track

    def __init__(self, track: Track) -> None:
        self.acm = DEFAULT_ACM  # TODO add acm to the DB Tracks populated by their point rollup
        self.track = track

    def create_oms_track(self) -> CreateObservationCreateObservation:
        # if self.oms_id is None: # fix, not initialized is != None
        return oms_client.create_observation(self._create_observation_input())

    def _create_observation_input(self) -> CreateObservationInput:
        return CreateObservationInput(
            acm=self.acm,
            tags=[],
            labels=[SETTINGS.sm_connected_track],
            classIri=SETTINGS.track_iri,
            confidence=Confidence.UNKNOWN,
            sourceId=self.track.points[0].source_id,
            nodeId=self.track.node_id,
            geometry=self.track.to_geometry(),
            startTime=self.track.start_time,
            endTime=self.track.end_time,
        )
