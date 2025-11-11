import random

from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import CreateRelationshipInput

from oms_sensemaking.config import SETTINGS

from ..atoms_client import atoms_client


def assign_garrisons(units, garrisons, sourcing, per_unit):
    rels = []
    client = atoms_client.client

    for unit in units:
        chosen = random.sample(garrisons, per_unit)
        for g in chosen:
            rel = client.create_relationship(
                CreateRelationshipInput(
                    name="garrison",
                    acm=DEFAULT_ACM,
                    startNodeId=unit.id,
                    endNodeId=g.facility.id,
                    sourceId=sourcing.source.id,
                    confidence="LOW",
                    objectPropertyIri=SETTINGS.inference_garrisoned_in_iri,
                )
            )
            rels.append(rel)

    return rels
