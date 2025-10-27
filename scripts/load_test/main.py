import argparse
import random
import uuid
from abc import ABC, abstractmethod
from typing import Protocol

from oms_sdk import DEFAULT_ACM, get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client import (
    AttributeAttribute,
    AttributeType,
    Client,
    Confidence,
    CreateAttributeInput,
    CreateNodeInput,
    CreateObservationInput,
    CreateOriginatorInput,
    CreateProviderInput,
    CreateRelationshipInput,
    CreateSourceInput,
    Domain,
    NodeNode,
    ObjectTier,
    OriginatorOriginator,
    OriginatorQuery,
    ProviderProvider,
    ProviderQuery,
    RelationshipRelationship,
    SourceQuery,
    SourceSource,
)
from oms_sdk.generated.generated_graphql_client.exceptions import GraphQLClientGraphQLMultiError

from oms_sensemaking.config import SETTINGS

omsb_url = "https://localhost:8020/graphql"
obs_iri = "http://www.ontologyrepository.com/CommonCoreOntologies/GeospatialLocation"


class AtomsClient:
    def __init__(self, user_dn=""):
        self.client: Client = get_generated_graphql_client(
            url=omsb_url,
            user_dn=user_dn or SETTINGS.user_dn,
            cert_path=SETTINGS.cert_path,
            key_path=SETTINGS.key_path,
            pkcs12_path=SETTINGS.pkcs12_path,
            pkcs12_password=SETTINGS.pkcs12_password,
            ssl_cert_file_path=SETTINGS.atoms_cacert_path,
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
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    def get_geometry(self):
        return {"type": "Point", "coordinates": [self.lon, self.lat]}


class DateRange:
    def __init__(self, start, end):
        self.start = start
        self.end = end


class DTO:
    def __init__(self, client: AtomsClient):
        self.client = client


class Unit(NodeNode):
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


class RelationshipService(DTO):
    def create(
        self, start_node: NodeNode, end_node: NodeNode, relationship_iri: str, sourcing: Sourcing
    ) -> RelationshipRelationship:
        input = CreateRelationshipInput(
            name=f"{start_node.id} to {end_node.id} rel {relationship_iri}",
            acm=DEFAULT_ACM,
            startNodeId=start_node.id,
            endNodeId=end_node.id,
            sourceId=sourcing.source.id,
            confidence=Confidence.LOW,
            objectPropertyIri=relationship_iri,
        )
        return self.client.client.create_relationship(input)


class GarrisonedUnit:
    def __init__(self, unit, garrison) -> None:
        self.unit = unit
        self.garrison = garrison
        # self.relationship = Relationship(unit, garrison, garrison_iri)


class Locatable(Protocol):
    def get_location() -> Location: ...


class Garrison:
    def __init__(self, facility: NodeNode, location: AttributeAttribute):
        self.facility = facility
        self.location = location

    def get_facility_id(self):
        return self.facility.id

    def get_facility_name(self):
        return self.facility.name

    def get_facility_geo(self):
        return self.location.geometry

    def get_location(self) -> Location:
        raise NotImplementedError


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
            allegiance="USA",
        )

        node_data = self.client.client.create_node(node_input)

        attr_input = CreateAttributeInput(
            nodeId=node_data.id,
            acm=DEFAULT_ACM,
            attributeIri=SETTINGS.inference_geo_attribute_iri,
            attributeValue="a location",
            attributeType=AttributeType.GEOSPATIAL,
            geometry=location.get_geometry(),
            valueStart="2023-01-01T00:00:00+00:00",
            valueEnd="2028-01-01T00:00:00+00:00",
            confidence=Confidence.LOW,
            sourceId=sourcing.source.id,
        )
        location_attr = self.client.client.create_attribute(attr_input)

        return Garrison(node_data, location_attr)


def gen_random_location() -> Location:
    # cut off the ends to ease up on distance math and quick and (probably)
    # make it harder to go out of bounds
    lat = random.randint(-70, 70)
    lon = random.randint(-170, 170)
    return Location(lat, lon)


class LocationCreationStrategy(ABC):
    @abstractmethod
    def get_location(self, locatable: Locatable) -> Location:
        raise NotImplementedError


class RandomLocation(LocationCreationStrategy):
    def get_location(self, locatable: Locatable):
        return gen_random_location()


class GetNearLocation(LocationCreationStrategy):
    def get_location(self, locatable: Locatable):
        input_location = locatable.get_location()
        return Location(input_location.lat + 1, input_location.lon + 1)


class DetermineOutOfGarrison:
    def __init__(self, distance_km) -> None:
        self.distance_km = distance_km


def create_units(limit) -> list[Unit]:
    unit_names = []
    unit_service = UnitService(atoms_client)
    for index in range(limit):
        unit_names.append(f"Unit no. {index}")

    units = []
    for unit_name in unit_names:
        unit = unit_service.create(unit_name)
        units.append(unit)
        print(f"created unit {unit.id}: {unit.name}")

    return units


def create_sourcing() -> Sourcing:
    unique_suffix = uuid.uuid4().hex[:8]
    try:
        originator_input = CreateOriginatorInput(
            name=f"originator-{unique_suffix}", description="descr", tags=[], acm=DEFAULT_ACM
        )
        orig = atoms_client.client.create_originator(originator_input)
    except GraphQLClientGraphQLMultiError as e:
        if len(e.errors) == 1 and e.errors[0].message == "An object already exists with the given unique key":
            orig = atoms_client.client.originators(OriginatorQuery()).data[0]
        else:
            raise e
    try:
        provider_input = CreateProviderInput(
            name=f"provider-{unique_suffix}", description="descr", originatorId=orig.id, acm=DEFAULT_ACM
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
            identifier=f"https://dev.com/loadtest/{unique_suffix}",
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


def create_garrisons(limit, sourcing) -> list[Garrison]:
    garrison_service = GarrisonService(atoms_client)

    garrison_names = []
    for index in range(limit):
        garrison_names.append(f"Garrison no. {index}")

    garrisons = []
    for garrison_name in garrison_names:
        garrison = garrison_service.create(garrison_name, gen_random_location(), sourcing)
        garrisons.append(garrison)
        print(f"created garrison {garrison.get_facility_id()}: {garrison.get_facility_name()}")
    return garrisons


def assign_units_to_garrisons(units: list[Unit], garrisons: list[Garrison], sourcing: Sourcing) -> list[GarrisonedUnit]:
    relationship_service = RelationshipService(atoms_client)
    unit_garrisons = zip(units, garrisons, strict=False)
    garrisoned_units = []
    for unit_garrison in unit_garrisons:
        unit, garrison = unit_garrison
        relationship = relationship_service.create(
            unit, garrison.facility, SETTINGS.inference_garrisoned_in_iri, sourcing
        )
        garrisoned_unit = GarrisonedUnit(unit, garrison)
        garrisoned_units.append(garrisoned_unit)
        print(f"unit: {unit.id}, garrison_facility: {garrison.facility.id}, relationship: {relationship.id}")

    return garrisoned_units


def observe_unit(unit: Unit, sourcing: Sourcing, location_strategy: LocationCreationStrategy):
    junk_location = gen_random_location()
    input = CreateObservationInput(
        nodeId=unit.id,
        acm=DEFAULT_ACM,
        sourceId=sourcing.source.id,
        # should've passed garrisoned unit
        geometry=location_strategy.get_location(junk_location).get_geometry(),
        classIri=obs_iri,
        startTime="2023-01-01T00:00:00+00:00",
        endTime="2028-01-01T00:00:00+00:00",
    )
    obs = atoms_client.client.create_observation(input)
    print(f"unit: {unit.id}, observation: {obs.id}")


def observe_units(units: list[Unit], sourcing: Sourcing):
    for unit in units:
        observe_unit(unit, sourcing, RandomLocation())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load test script for creating units, garrisons, and observations in ATOMS Sensemaking."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of units/garrisons/observations to create (default: 100)",
    )

    args = parser.parse_args()
    limit = args.limit

    print(f"Running load test with limit={limit}")
    units = create_units(limit)
    sourcing: Sourcing = create_sourcing()
    garrisons = create_garrisons(limit, sourcing)
    garrisoned_units = assign_units_to_garrisons(units, garrisons, sourcing)
    observe_units(units, sourcing)
