from oms_sdk import DEFAULT_ACM, get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client import (
    AttributeType,
    Client,
    Confidence,
    CreateAttributeInput,
    CreateNodeInput,
    CreateOriginatorInput,
    CreateProviderInput,
    CreateSourceInput,
    Domain,
    NodeNode,
    ObjectTier,
    OriginatorOriginator,
    OriginatorQuery,
    ProviderProvider,
    ProviderQuery,
    SourceQuery,
    SourceSource,
)
from oms_sdk.generated.generated_graphql_client.exceptions import GraphQLClientGraphQLMultiError

from oms_sensemaking.config import SETTINGS

omsb_url = "https://localhost:8020/graphql"


class AtomsClient:
    def __init__(self, user_dn=""):
        self.client: Client = get_generated_graphql_client(
            url=omsb_url,
            user_dn=user_dn or SETTINGS.user_dn,
            cert_path=SETTINGS.cert_path,
            key_path=SETTINGS.key_path,
            pkcs12_path=SETTINGS.pkcs12_path,
            pkcs12_password=SETTINGS.pkcs12_password,
        )


atoms_client = AtomsClient()


class Sourcing:
    originator: OriginatorOriginator
    provider: ProviderProvider
    source: SourceSource

    def __init__(self, originator, provider, source) -> None:
        self.originator = originator
        self.provider = provider
        self.source = source


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


class Unit(NodeNode):
    def __init__(self):
        pass


class UnitService(DTO):
    def create(self, name):
        node_input = CreateNodeInput(
            name=name,
            acm=DEFAULT_ACM,
            tier=ObjectTier.PRIMARY,
            domain=Domain.AIR,
            tags=["Load Test"],
            labels=[],
            classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
            allegiance="USA",
        )
        return self.client.client.create_node(node_input)


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


class GarrisonService(DTO):
    def create(self, name, location: Location, sourcing: Sourcing):
        node_input = CreateNodeInput(
            name=name,
            acm=DEFAULT_ACM,
            tier=ObjectTier.PRIMARY,
            domain=Domain.GROUND,
            tags=["Load Test"],
            labels=[],
            classIri="https://foundry.ai.mil/ontology/4901-001/Facility",
        )

        self._node_data = self.client.client.create_node(node_input)

        attr_input = CreateAttributeInput(
            nodeId=self._node_data.id,
            attributeIri=SETTINGS.inference_geo_attribute_iri,
            attributeType=AttributeType.GEOSPATIAL,
            geometry=location.geometry(),
            valueStart="2023-01-01T00:00:00+00:00",
            valueEnd="2028-01-01T00:00:00+00:00",
            confidence=Confidence.LOW,
            sourceId=sourcing.source.id,
        )
        self.client.client.create_attribute(attr_input)


class DetermineOutOfGarrison:
    def __init__(self, distance_km) -> None:
        self.distance_km = distance_km


def create_units(limit):
    unit_names = []
    unit_service = UnitService(atoms_client)
    for index in range(limit):
        unit_names.append(f"Unit no. {index}")

    units = []
    for unit_name in unit_names:
        unit = unit_service.create(unit_name)
        units.append(unit)
        print(f"created unit {unit.id}: {unit.name}")


def create_sourcing() -> Sourcing:
    try:
        originator_input = CreateOriginatorInput(name="originator", description="descr", tags=[], acm=DEFAULT_ACM)
        orig = atoms_client.client.create_originator(originator_input)
    except GraphQLClientGraphQLMultiError as e:
        if len(e.errors) == 1 and e.errors[0].message == "An object already exists with the given unique key":
            orig = atoms_client.client.originators(OriginatorQuery()).data[0]
        else:
            raise e
    try:
        provider_input = CreateProviderInput(
            name="provider", description="descr", originatorId=orig.id, acm=DEFAULT_ACM
        )
        prov = atoms_client.client.create_provider(provider_input)
    except GraphQLClientGraphQLMultiError as e:
        if len(e.errors) == 1 and e.errors[0].message == "An object already exists with the given unique key":
            prov = atoms_client.client.providers(ProviderQuery()).data[0]
        else:
            raise e
    try:
        source_input = CreateSourceInput(
            name="source",
            providerId=prov.id,
            acm=DEFAULT_ACM,
            identifier="https://dev.com",
            dataAcm=DEFAULT_ACM,
            dateOfReport="2023-01-01T00:00:00+00:00",
            dateOfInformation="2023-01-01T00:00:00+00:00",
        )
        src = atoms_client.client.create_source(source_input)
    except GraphQLClientGraphQLMultiError as e:
        if len(e.errors) == 1 and e.errors[0].message == "An object already exists with the given unique key":
            src = atoms_client.client.originators(SourceQuery()).data[0]
        else:
            raise e

    print(f"Using source {src.id}")

    return Sourcing(orig, prov, src)


if __name__ == "__main__":
    print("running load test")
    create_units(10)
    sourcing: Sourcing = create_sourcing()
