from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    AttributeType,
    CreateAttributeInput,
    CreateNodeInput,
    Domain,
    ObjectTier,
)

from oms_sensemaking.config import SETTINGS

from ..atoms_client import atoms_client
from ..utils import gen_random_location


class Garrison:
    def __init__(self, facility_node, primary_attr):
        self.facility = facility_node
        self.location = primary_attr


class GarrisonService:
    def create(self, name, sourcing):
        client = atoms_client.client

        facility = client.create_node(
            CreateNodeInput(
                name=name,
                acm=DEFAULT_ACM,
                tier=ObjectTier.PRIMARY,
                domain=Domain.GROUND,
                tags=["Load Test"],
                labels=[],
                classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
                allegiance="USA",
            )
        )

        primary_geo = client.create_attribute(
            CreateAttributeInput(
                nodeId=facility.id,
                acm=DEFAULT_ACM,
                attributeIri=SETTINGS.inference_geo_attribute_iri,
                attributeValue="location",
                attributeType=AttributeType.GEOSPATIAL,
                geometry=gen_random_location(),
                valueStart="2023-01-01T00:00:00Z",
                valueEnd="2028-01-01T00:00:00Z",
                confidence="LOW",
                sourceId=sourcing.source.id,
            )
        )

        return Garrison(facility, primary_geo)
