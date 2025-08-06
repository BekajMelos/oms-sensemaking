from oms_sdk.generated.generated_graphql_client import (
    Confidence,
    CreateObservationCreateObservation,
    CreateObservationInput,
)

from oms_sensemaking.clients.instances import oms_crud_tool
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.models.geo import Track


class APITrack:
    track: Track

    def __init__(self, track: Track) -> None:
        self.track = track

    def create_oms_track(self) -> CreateObservationCreateObservation:
        # if self.oms_id is None: # fix, not initialized is != None
        return oms_crud_tool.create_observation(self._create_observation_input())

    def _create_observation_input(self) -> CreateObservationInput:
        return CreateObservationInput(
            acm=self.track.acm,
            tags=[SETTINGS.geo_sensemaker_event_tag],
            labels=[SETTINGS.sm_inferenced_label, SETTINGS.sm_connected_track],
            classIri=SETTINGS.track_iri,
            confidence=Confidence.UNKNOWN,
            sourceId=self.track.points[0].source_id,
            nodeId=self.track.node_id,
            geometry=self.track.to_geometry(),
            startTime=self.track.start_time,
            endTime=self.track.end_time,
        )
