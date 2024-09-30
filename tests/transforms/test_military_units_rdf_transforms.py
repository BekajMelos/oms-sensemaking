import json
from typing import Iterator, List

import pytest
import yaml
from rdflib import Graph, Namespace  ## add to toml

from src.oms_sensemaking.transforms.json2rdf import JSON2RDF


@pytest.fixture
def setUp() -> Iterator(dict):
    config_data = open('transform-test-config.yml', 'r')
    configs = yaml.safe_load(config_data.read())
    config_data.close()
    yield configs


def test_mil_unit_transform(input_fixture):
    # JSON object required for the transformer
    configs = next(input_fixture)

    test_obj_fin = open(f"{configs.get('test_data_path')}{configs.get('test_mil_unit_midb')}", 'r')
    test_obj = json.loads(test_obj_fin.read())
    test_obj_fin.close()

    assert (len(test_obj) > 0)

    # instantiate an empty rdflib Graph
    aligned_graph = Graph()

    # create/apply namespace bindings
    acmtemp = Namespace("http://blackcape.io/ontology/control-markings/")
    aligned_graph.bind("acmtemp", acmtemp)
    cco = Namespace("http://www.ontologyrepository.com/CommonCoreOntologies/")
    aligned_graph.bind("cco", cco)
    dico = Namespace("http://schema.dia.mil/DefenseIntelligenceCoreOntology/")
    aligned_graph.bind("dico", dico)
    src = Namespace("http://blackcape.io/ontology/node#")
    aligned_graph.bind("src", src)
    cnyobj = Namespace("http://blackcape.io/ontology/country_obj/")
    aligned_graph.bind("cnyobj", cnyobj)
    cnyid = Namespace("http://blackcape.io/ontology/country_id/")
    aligned_graph.bind("cnyid", cnyid)

    # create the transformer executable
    mil_unit_transformer = JSON2RDF(
        construct=configs.get('construct_query_path')
        , source_model=configs.get('source_model_path')
        , ns_uri=configs.get('namespace_uri'))

    # pass the json object to the transformer executable, which returns
    # (1) the triple generator
    # (2) flattened RDF data (at least temporarily for review / refactoring concerns)
    aligned_triples, g = mil_unit_transformer(test_obj)

    for stmt in aligned_triples:
        aligned_graph.add(stmt)
    assert (len(aligned_graph) > 0)

    # drop a copy of the RDF graph in test output

    ttl_output = open(f"{configs.get('output_path')}{configs.get('test_mil_unit_midb').replace('.json', 'ttl')}", 'w')
    ttl_output.write(aligned_graph.serialize(format='ttl'))
    ttl_output.close()
