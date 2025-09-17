from oms_sdk import DEFAULT_ACM, get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client import (
    AttributeType,
    Client,
    Confidence,
    CreateAttributeInput,
    CreateNodeInput,
    Domain,
    ObjectTier,
)

from oms_sensemaking.config import SETTINGS


class AtomsClient:
    def __init__(self, user_dn=""):
        self.client: Client = get_generated_graphql_client(
            url=SETTINGS.omsb_url,
            user_dn=user_dn or SETTINGS.user_dn,
            cert_path=SETTINGS.cert_path,
            key_path=SETTINGS.key_path,
            pkcs12_path=SETTINGS.pkcs12_path,
            pkcs12_password=SETTINGS.pkcs12_password,
        )


class Location:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def geometry(self):
        return {"type": "Point", "coordinates": [self.lon, self.lat]}


class DateRange:
    def __init__(self, start, end):
        self.start = start
        self.end = end


class DTO:
    def __init__(self, client: AtomsClient):
        self.client = client


class Unit:
    def __init__(self, name, id=""):
        self.name = name
        self.id = id


class UnitDTO:
    def create(self, unit):
        node_input = CreateNodeInput(
            name=unit.name,
            acm=DEFAULT_ACM,
            tier=ObjectTier.primary,
            domain=Domain.AIR,
            tags=["Load Test"],
            labels=["Load Test"],
            classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
        )
        unit = self.client.client.create_node(node_input)


class Relationship:
    def __init__(self, start_node, end_node, relationship_iri) -> None:
        self.start_node = start_node
        self.end_node = end_node
        self.relationship_iri = relationship_iri


class GarrisonedUnit:
    def __init__(self, unit, garrison) -> None:
        garrison_iri = "https://foundry.ai.mil/ontology/4901-001/garrisonedIn"
        self.unit = unit
        self.garrison = garrison
        self.relationship = Relationship(unit, garrison, garrison_iri)


class Garrison:
    def __init__(self, name, location: Location, id="") -> None:
        self.name = name
        self.location = location
        self.id = id


class GarrisonDTO(DTO):
    def create(self, garrison: Garrison):
        node_input = CreateNodeInput(
            name=garrison.name,
            acm=DEFAULT_ACM,
            tier=ObjectTier.primary,
            domain=Domain.GROUND,
            tags=["Load Test"],
            labels=["Load Test"],
            classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
        )

        self._node_data = self.client.client.create_node(node_input)

        attr_input = CreateAttributeInput(
            nodeId=self._node_data.id,
            attributeIri=SETTINGS.inference_geo_attribute_iri,
            attributeType=AttributeType.GEOSPATIAL,
            geometry=garrison.location.geometry(),
            valueStart="2023-01-01T00:00:00+00:00",
            valueEnd="2028-01-01T00:00:00+00:00",
            confidence=Confidence.LOW,
        )
        self.client.client.create_attribute(attr_input)


class DetermineOutOfGarrison:
    def __init__(self, distance_km) -> None:
        self.distance_km = distance_km


def create_units(limit):
    units = []
    for index in range(limit):
        units.append(Unit(f"Unit no. {index}"))


if __name__ == "__main__":
    print("running load test")
