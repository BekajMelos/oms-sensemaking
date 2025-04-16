import json
from typing import Any

import shapely
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    Confidence,
    CreateObservationCreateObservation,
    CreateObservationInput,
)

from oms_sensemaking.clients.instances import oms_client
from oms_sensemaking.models.geo import Point

track_iri = "https://foundry.ai.mil/ontology/4901-001/TrackDisplay"
# "https://foundry.ai.mil/ontology/4901-001/ObjectTrack"


class APITrack:
    node_id: str
    points: list[Point]
    source_id: str
    acm: Any
    start_time: any
    # end_time: any # TODO store end time

    def __init__(self, node_id: str, points: list[Point]) -> None:
        self.acm = DEFAULT_ACM  # TODO add acm to the DB Tracks populated by their point rollup
        self.node_id = node_id
        self.points = points
        self.source_id = points[0].source_id  # TODO add source to DB Tracks
        self.start_time = points[0].detection_time

    def save(self) -> CreateObservationCreateObservation:
        # if self.oms_id is None: # fix, not initialized is != None
        return oms_client.create_observation(self._create_observation_input())

    def _create_observation_input(self) -> CreateObservationInput:
        return CreateObservationInput(
            acm=self.acm,
            tags=[],
            labels=["SM_GENERATED_TRACK"],
            classIri=track_iri,
            confidence=Confidence.UNKNOWN,
            sourceId=self.source_id,
            nodeId=self.node_id,
            geometry=json.loads(self._create_geometry()),
            startTime=f"{self.start_time.isoformat().replace('+00:00', 'Z')}",
            # endTime=self.end_time
        )

    def _create_geometry(self) -> str:
        points = [p.coordinates for p in self.points]
        return shapely.to_geojson(shapely.LineString(points))
