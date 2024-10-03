import json
from typing import Iterator, List

import pytest
import yaml
from rdflib import Graph, Namespace, XSD

from oms_sensemaking.transforms.json2rdf import JSON2RDF, DateEncoder


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


def test_dateparser():
    encode_date = DateEncoder()

    # postive test cases
    value_out, datatype = encode_date("2023-01-23 10:00:00Z")  ## without T
    assert ("2023-01-23T10:00:00" == value_out)
    assert (datatype == XSD.dateTime)

    value_out, datatype = encode_date("2023-01-23T10:00:00Z")  ## with T
    assert ("2023-01-23T10:00:00" == value_out)
    assert (datatype == XSD.dateTime)

    value_out, datatype = encode_date("2023-01-24 10:00:00")
    assert ("2023-01-24T10:00:00" == value_out)
    assert (datatype == XSD.dateTime)

    value_out, datatype = encode_date("2023-01-24")
    assert ('2023-01-24' == value_out)
    assert (datatype == XSD.date)

    value_out, datatype = encode_date("20231002")
    assert ('2023-10-02' == value_out)
    assert (datatype == XSD.date)

    ## negative test cases
    value_out, datatype = encode_date("2023-41-24 10:00:00")
    assert (value_out is None)
    assert (datatype is None)

    value_out, datatype = encode_date("2023-41-24")
    assert (value_out is None)
    assert (datatype is None)

    value_out, datatype = encode_date("20234124")
    assert (value_out is None)
    assert (datatype is None)

    value_out, datatype = encode_date("2023T4124-04Z")
    assert (value_out is None)
    assert (datatype is None)