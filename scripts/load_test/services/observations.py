from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import CreateObservationInput

from ..atoms_client import atoms_client
from ..utils import gen_random_location

OBS_IRI = "http://www.ontologyrepository.com/CommonCoreOntologies/GeospatialLocation"


def observe_all(units, sourcing):
    client = atoms_client.client
    for unit in units:
        client.create_observation(
            CreateObservationInput(
                nodeId=unit.id,
                acm=DEFAULT_ACM,
                sourceId=sourcing.source.id,
                geometry=gen_random_location(),
                classIri=OBS_IRI,
                startTime="2023-01-01T00:00:00Z",
                endTime="2028-01-01T00:00:00Z",
            )
        )
