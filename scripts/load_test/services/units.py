from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import CreateNodeInput, Domain, ObjectTier

from ..atoms_client import atoms_client


class UnitService:
    def create(self, name):
        return atoms_client.client.create_node(
            CreateNodeInput(
                name=name,
                acm=DEFAULT_ACM,
                tier=ObjectTier.PRIMARY,
                domain=Domain.AIR,
                tags=["Load Test"],
                labels=[],
                classIri="http://www.ontologyrepository.com/CommonCoreOntologies/Aircraft",
                allegiance="USA",
            )
        )
