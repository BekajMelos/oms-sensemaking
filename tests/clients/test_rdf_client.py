import json

import pytest
from fastapi import HTTPException, Response
from rdflib import Graph, Literal, Namespace, URIRef

from oms_sensemaking.api.schemas.rdf_format import RDFFormat
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
    return json.dumps({"data": [{"guideId": "test-id", **data}]})


def test_add_triples_with_scalar(rdf_client):
    rdf = rdf_client.json_to_rdf(make_json({str(ex["simple"]): "hello"}), RDFFormat.turtle.value)
    rdf_response = Response(content=rdf, media_type="text/plain").body.decode()
    g = Graph()
    g.parse(data=rdf_response, format="turtle")
    assert (subj, URIRef(ex["simple"]), Literal("hello")) in g


def test_add_triples_with_list(rdf_client):
    rdf = rdf_client.json_to_rdf(make_json({str(ex["fruit"]): ["apple", "banana"]}), RDFFormat.turtle.value)
    rdf_response = Response(content=rdf, media_type="text/plain").body.decode()
    g = Graph()
    g.parse(data=rdf_response, format="turtle")
    assert (subj, URIRef(ex["fruit"]), Literal("apple")) in g
    assert (subj, URIRef(ex["fruit"]), Literal("banana")) in g


def test_add_triples_with_nested_dict(rdf_client):
    rdf = rdf_client.json_to_rdf(make_json({str(ex["outer_inner"]): "deep_value"}), RDFFormat.turtle.value)
    rdf_response = Response(content=rdf, media_type="text/plain").body.decode()
    g = Graph()
    g.parse(data=rdf_response, format="turtle")
    assert (subj, URIRef(ex["outer_inner"]), Literal("deep_value")) in g


def test_add_triples_with_acm_prefix(rdf_client):
    rdf = rdf_client.json_to_rdf(make_json({"acm_clearance": "TopSecret"}), RDFFormat.turtle.value)
    rdf_response = Response(content=rdf, media_type="text/plain").body.decode()
    g = Graph()
    g.parse(data=rdf_response, format="turtle")
    assert (subj, URIRef(acm["clearance"]), Literal("TopSecret")) in g


def test_unsupported_format_raises_http_exception(rdf_client):
    with pytest.raises(HTTPException) as excinfo:
        rdf_client.json_to_rdf(json.dumps({"data": [{"guideId": "test"}]}), "unsupported")
    assert excinfo.value.status_code == 400


def test_missing_data_raises_http_exception(rdf_client):
    with pytest.raises(HTTPException) as excinfo:
        rdf_client.json_to_rdf(json.dumps({"other": []}), RDFFormat.turtle.value)
    assert excinfo.value.status_code == 400


def test_missing_guide_id_raises_http_exception(rdf_client):
    with pytest.raises(HTTPException) as excinfo:
        rdf_client.json_to_rdf(json.dumps({"data": [{}]}), RDFFormat.turtle.value)
    assert excinfo.value.status_code == 400
