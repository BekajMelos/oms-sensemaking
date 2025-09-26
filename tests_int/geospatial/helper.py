from datetime import datetime
from uuid import UUID, uuid4

from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client.enums import Confidence

from oms_sensemaking.models.geo import Point
from tests_int.conftest import rollup_unclass_acm_3_0

ROLLUP_DEFAULT_ACM = rollup_unclass_acm_3_0()


class TimeLocation:
    def __init__(self, location: str, time: str) -> None:
        self.location = location
        self.time = time

    def create_node_point(self, node_id: UUID) -> Point:
        return Point(
            acm=DEFAULT_ACM,
            location=self.location,
            altitude=None,
            detection_time=datetime.fromisoformat(self.time),
            node_id=node_id,
            node_version=1,
            observation_id=uuid4(),
            observation_version=1,
            observation_confidence=Confidence.HIGH,
            source_id=uuid4(),
        )
