import json

import pytest
from fastapi import HTTPException
from rdflib import Graph, Literal, Namespace, URIRef

from oms_sensemaking.clients.rdf_client import RDFClient

oms = Namespace("https://oms.dodiis.ic.gov/ontology/")
acm = Namespace("https://oms.dodiis.ic.gov/ontology/acm/")

@pytest.fixture
def rdf_client():
    return RDFClient()

def get_predicate(key):
    if key.startswith("acm_"):
        return acm[key[len("acm_"):]]
    return URIRef(key)

def add_triples(g, subj, obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            add_triples(g, subj, v, prefix=prefix + k + "_")
    elif isinstance(obj, list):
        predicate = get_predicate(prefix.rstrip('_'))
        for item in obj:
            g.add((subj, predicate, Literal(item)))
    elif obj is not None:
        predicate = get_predicate(prefix.rstrip('_'))
        g.add((subj, predicate, Literal(obj)))

def test_add_triples_with_scalar():
    g = Graph()
    subj = URIRef("https://example.org/node/test")
    add_triples(g, subj, "hello", prefix="simple")

    triples = list(g)
    assert len(triples) == 1
    assert (subj, URIRef("simple"), Literal("hello")) in triples

def test_add_triples_with_list():
    g = Graph()
    subj = URIRef("https://example.org/node/test")
    add_triples(g, subj, ["apple", "banana"], prefix="fruit")

    predicates = list(g.predicates(subject=subj))
    objects = [str(o) for o in g.objects(subject=subj)]

    assert URIRef("fruit") in predicates
    assert "apple" in objects and "banana" in objects

def test_add_triples_with_nested_dict():
    g = Graph()
    subj = URIRef("https://example.org/node/test")
    add_triples(g, subj, {"outer": {"inner": "deep_value"}}, prefix="data")

    expected_predicate = URIRef("dataouter_inner")
    assert (subj, expected_predicate, Literal("deep_value")) in g

def test_add_triples_with_acm_prefix():
    g = Graph()
    subj = URIRef("https://example.org/node/test")
    add_triples(g, subj, {"acm_clearance": "TopSecret"}, prefix="")

    expected_predicate = acm["clearance"]
    assert (subj, expected_predicate, Literal("TopSecret")) in g

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
