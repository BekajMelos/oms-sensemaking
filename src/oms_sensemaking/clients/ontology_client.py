from queue import SimpleQueue
from typing import Optional, Protocol

from cachetools import TTLCache, cached
from oms_sdk.generated.generated_graphql_client import NodeNode, OntologyClassOntologyClass

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool


class OntologyService(Protocol):
    def get_ontology_class(self, iri: str) -> Optional[OntologyClassOntologyClass]:
        """Return an OntologyClass for the given IRI"""
        pass

    def geospatial_get_node_ancestors_iris(self, oms_node: NodeNode) -> set[str]:
        """Return a unique set of ancestor IRIs"""
        pass

    def mil_symbol_get_node_ancestors_iris(self, oms_node: NodeNode) -> list[str]:
        """Return a list of ancestor IRIs"""
        pass

    def get_default_symbol_id_code(self, iri: str) -> Optional[str]:
        """Return the closest parent with a defaultSymbolIdCode in a hierarchy of OntologyClasses"""
        pass


class OntologyClient(OntologyService):
    """
    Provide cohesive Ontology related requests
    """

    def __init__(self, oms_client: OmsCrudTool):
        self._oms_client = oms_client

    @cached(TTLCache(SETTINGS.ttl_cache_size, SETTINGS.ttl_cache_seconds))
    def get_ontology_class(self, iri: str) -> Optional[OntologyClassOntologyClass]:
        return self._oms_client.get_ontology_class(iri)

    def geospatial_get_node_ancestors_iris(self, oms_node: NodeNode) -> set[str]:
        """Get ancestor's iris.

        :param oms_node: Node to grab the status for
        :return: The Node's ancestor's iri list
        """

        iris: set[str] = set()
        visited: set[str] = {oms_node.classIri}  # include start so we detect cycle back to it
        iris_to_check: SimpleQueue = SimpleQueue()
        iris_to_check.put_nowait(oms_node.classIri)
        while not iris_to_check.empty():
            current_iri = iris_to_check.get_nowait()
            ontology_class: OntologyClassOntologyClass | None = self.get_ontology_class(iri=current_iri)

            if not ontology_class or not ontology_class.parentOntologyClasses:
                continue

            for parent_ontology_class in ontology_class.parentOntologyClasses:
                parent_iri = parent_ontology_class.iri
                if parent_iri in visited:
                    continue
                visited.add(parent_iri)
                iris.add(parent_iri)
                iris_to_check.put_nowait(parent_iri)

        return iris

    def mil_symbol_get_node_ancestors_iris(self, oms_node: NodeNode) -> list[str]:
        """Get ancestor's iris.

        :param oms_node: Node to grab the status for
        :return: The Node's ancestor's iri list
        """

        # OMSB currently does not return the ancestorOntologyClasses in order so we have to query manually for now

        iris: list[str] = []
        visited: set[str] = {oms_node.classIri}
        current_iri = oms_node.classIri
        while True:
            ontology_class: Optional[OntologyClassOntologyClass] = self.get_ontology_class(iri=current_iri)

            if not ontology_class or not ontology_class.parentOntologyClasses:
                break

            # If multiple parent Iris, just get the first one
            parent_iri = ontology_class.parentOntologyClasses[0].iri
            if parent_iri in visited:
                break
            visited.add(parent_iri)
            iris.append(parent_iri)
            current_iri = parent_iri

        return iris

    def get_default_symbol_id_code(self, iri: str) -> Optional[str]:
        """Given an iri, return the closest parent with a defaultSymbolIdCode

        :param iri: Iri to search for
        :return: Closest parent iri with a defaultSymbolIdCode
        """
        return self._get_default_symbol_id_code(iri, None)

    def _get_default_symbol_id_code(self, iri: str, _visited: Optional[set[str]]) -> Optional[str]:
        """Given an iri, return the closest parent with a defaultSymbolIdCode

        :param iri: Iri to search for
        :param _visited: Internal set of visited IRIs used to detect circular references; callers should omit.
        :return: Closest parent iri with a defaultSymbolIdCode
        """
        if _visited is None:
            _visited = set()
        if iri in _visited:
            return None
        _visited.add(iri)

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

        return self._get_default_symbol_id_code(super_class_iri, _visited)
