from queue import SimpleQueue
from typing import Optional, Protocol

from oms_sdk.generated.generated_graphql_client import NodeNode, OntologyClassOntologyClass

from oms_sensemaking.core.oms_crud import OmsCrudTool


class OntologyService(Protocol):
    def get_ontology_class(self, iri: str) -> Optional[OntologyClassOntologyClass]:
        pass

    def geospatial_get_node_ancestors_iris(self, oms_node: NodeNode) -> set[str]:
        pass

    def mil_symbol_get_node_ancestors_iris(self, oms_node: NodeNode) -> list[str]:
        pass

    def get_default_symbol_id_code(self, iri: str) -> Optional[str]:
        pass


class OntologyClient(OntologyService):
    def __init__(self, oms_client: OmsCrudTool):
        self._oms_client = oms_client

    def get_ontology_class(self, iri: str) -> Optional[OntologyClassOntologyClass]:
        return self._oms_client.get_ontology_class(iri)

    def geospatial_get_node_ancestors_iris(self, oms_node: NodeNode) -> set[str]:
        """Get ancestor's iris.

        :param oms_node: Node to grab the status for
        :return: The Node's ancestor's iri list
        """

        iris = set()
        iris_to_check: SimpleQueue = SimpleQueue()
        iris_to_check.put_nowait(oms_node.classIri)
        while not iris_to_check.empty():
            current_iri = iris_to_check.get_nowait()
            ontology_class: OntologyClassOntologyClass | None = self.get_ontology_class(iri=current_iri)

            if not ontology_class or not ontology_class.parentOntologyClasses:
                continue

            for parent_ontology_class in ontology_class.parentOntologyClasses:
                iris.add(parent_ontology_class.iri)
                iris_to_check.put_nowait(parent_ontology_class.iri)

        return iris

    def mil_symbol_get_node_ancestors_iris(self, oms_node: NodeNode) -> list[str]:
        """Get ancestor's iris.

        :param oms_node: Node to grab the status for
        :return: The Node's ancestor's iri list
        """

        # OMSB currently does not return the ancestorOntologyClasses in order so we have to query manually for now

        iris = []
        has_parent = True
        current_iri = oms_node.classIri
        while has_parent:
            ontology_class: Optional[OntologyClassOntologyClass] = self.get_ontology_class(iri=current_iri)

            if not ontology_class or not ontology_class.parentOntologyClasses:
                break

            # If multiple parent Iris, just get the first one
            parent_iri = ontology_class.parentOntologyClasses[0].iri
            iris.append(parent_iri)
            current_iri = parent_iri

        return iris

    def get_default_symbol_id_code(self, iri: str) -> Optional[str]:
        """Given an iri, return the closest parent with a defaultSymbolIdCode

        :param iri: Iri to search for
        :return: Closest parent iri with a defaultSymbolIdCode
        """

        ontology_class: Optional[OntologyClassOntologyClass] = self.get_ontology_class(iri=iri)
        if not ontology_class:
            return None

        current_symbol_id_code = ontology_class.defaultSymbolIdCode
        if current_symbol_id_code:
            return current_symbol_id_code

        if not ontology_class.parentOntologyClasses:
            return None

        # If multiple parent Iris, just get the first one
        super_class_iri: str = ontology_class.parentOntologyClasses[0].iri

        return self.get_default_symbol_id_code(super_class_iri)
