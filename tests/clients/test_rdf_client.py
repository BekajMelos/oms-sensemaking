import json

import pytest
from fastapi import HTTPException
from rdflib import Graph, Literal, Namespace, URIRef

from oms_sensemaking.clients.rdf_client import RDFClient

ex = Namespace("https://example.org/")
oms = Namespace("https://oms.dodiis.ic.gov/ontology/")
acm = Namespace("https://oms.dodiis.ic.gov/ontology/acm/")
subj = URIRef(oms["guideId/test-id"])

@pytest.fixture
def rdf_client():
    return RDFClient()

def make_json(data):
    """Helper to construct valid JSON input for RDF conversion."""
    return json.dumps({
        "data": [{
            "guideId": "test-id",
            **data
        }]
    })

def test_add_triples_with_scalar(rdf_client):
    rdf = rdf_client.json_to_rdf(make_json({str(ex["simple"]): "hello"}), "turtle").body.decode()
    g = Graph()
    g.parse(data=rdf, format="turtle")
    print(g.serialize(format="turtle"))
    assert (subj, URIRef(ex["simple"]), Literal("hello")) in g

def test_add_triples_with_list(rdf_client):
    rdf = rdf_client.json_to_rdf(make_json({str(ex["fruit"]): ["apple", "banana"]}), "turtle").body.decode()
    g = Graph()
    g.parse(data=rdf, format="turtle")
    assert (subj, URIRef(ex["fruit"]), Literal("apple")) in g
    assert (subj, URIRef(ex["fruit"]), Literal("banana")) in g

def test_add_triples_with_nested_dict(rdf_client):
    rdf = rdf_client.json_to_rdf(make_json({str(ex["outer_inner"]): "deep_value"}), "turtle").body.decode()
    g = Graph()
    g.parse(data=rdf, format="turtle")
    assert (subj, URIRef(ex["outer_inner"]), Literal("deep_value")) in g

def test_add_triples_with_acm_prefix(rdf_client):
    rdf = rdf_client.json_to_rdf(make_json({"acm_clearance": "TopSecret"}), "turtle").body.decode()
    g = Graph()
    g.parse(data=rdf, format="turtle")
    assert (subj, URIRef(acm["clearance"]), Literal("TopSecret")) in g

def test_unsupported_format_raises_http_exception(rdf_client):
    with pytest.raises(HTTPException) as excinfo:
        rdf_client.json_to_rdf(json.dumps({
            "data": [{"guideId": "test"}]
        }), "unsupported")
    assert excinfo.value.status_code == 400

def test_missing_data_raises_http_exception(rdf_client):
    with pytest.raises(HTTPException) as excinfo:
        rdf_client.json_to_rdf(json.dumps({"other": []}), "turtle")
    assert excinfo.value.status_code == 400

def test_missing_guide_id_raises_http_exception(rdf_client):
    with pytest.raises(HTTPException) as excinfo:
        rdf_client.json_to_rdf(json.dumps({"data": [{}]}), "turtle")
    assert excinfo.value.status_code == 400
