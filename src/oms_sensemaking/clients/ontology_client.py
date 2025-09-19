from typing import Optional, Protocol

from oms_sdk.generated.generated_graphql_client import OntologyClassOntologyClass

from oms_sensemaking.core.oms_crud import OmsCrudTool


class OntologyService(Protocol):
    def get_ontology_class(self, iri: str) -> Optional[OntologyClassOntologyClass]:
        pass


class OntologyClient:
    def __init__(self, oms_client: OmsCrudTool):
        self.oms_client = oms_client

    def get_ontology_class(self, iri: str) -> Optional[OntologyClassOntologyClass]:
        return self.oms_client.get_ontology_class(iri)
