import time

from oms_sensemaking.clients.instances import oms_crud_tool
from oms_sensemaking.clients.ontology_client import OntologyClient
from oms_sensemaking.config import SETTINGS


def test_get_ontology_class():
    """
    Simple check to make sure that our models are correct
    and that the request/response is cached
    """
    ontology_client = OntologyClient(oms_crud_tool)
    class_iri = SETTINGS.loiter_event_node_iri

    start_time = time.perf_counter()
    res = ontology_client.get_ontology_class(class_iri)
    end_time = time.perf_counter()
    uncached_time = end_time - start_time

    start_time = time.perf_counter()
    res = ontology_client.get_ontology_class(class_iri)
    end_time = time.perf_counter()
    cached_time = end_time - start_time

    assert res.name == "Planned Act"
    assert cached_time * 1000 < uncached_time
