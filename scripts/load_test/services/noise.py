import random
import uuid

from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import AttributeType, CreateAttributeInput, CreateRelationshipInput

from oms_sensemaking.config import SETTINGS

from ..atoms_client import atoms_client


def add_noise_attributes(garrisons, sourcing, count):
    if count <= 0:
        return

    client = atoms_client.client
    iri = "http://www.ontologyrepository.com/CommonCoreOntologies/has_text_value"

    for g in garrisons:
        for _ in range(count):
            client.create_attribute(
                CreateAttributeInput(
                    nodeId=g.facility.id,
                    acm=DEFAULT_ACM,
                    attributeIri=iri,
                    attributeValue=str(uuid.uuid4()),
                    attributeType=AttributeType.STRING,
                    valueStart="2020-01-01T00:00:00Z",
                    valueEnd="2030-01-01T00:00:00Z",
                    confidence="LOW",
                    sourceId=sourcing.source.id,
                )
            )


def add_noise_relationships(units, garrisons, sourcing, count):
    if count <= 0:
        return

    client = atoms_client.client
    all_nodes = [u for u in units] + [g.facility for g in garrisons]
    iri = SETTINGS.resolution_relationship_iri

    for unit in units:
        for _ in range(count):
            rand = random.choice(all_nodes)
            if rand.id == unit.id:
                continue
            client.create_relationship(
                CreateRelationshipInput(
                    name="noise",
                    acm=DEFAULT_ACM,
                    startNodeId=unit.id,
                    endNodeId=rand.id,
                    sourceId=sourcing.source.id,
                    confidence="LOW",
                    objectPropertyIri=iri,
                )
            )
