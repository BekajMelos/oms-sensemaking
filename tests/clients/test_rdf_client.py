import json
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Response
from rdflib import RDF, Graph, Literal, Namespace, URIRef

from oms_sensemaking.api.schemas.rdf_format import RDFFormat
from oms_sensemaking.clients.rdf_client import RDFClient
from oms_sensemaking.core.oms_crud import OmsCrudTool

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
    relationships_obj = json.dumps({"relationships": []})
    rdf = rdf_client.json_to_rdf(make_json({str(ex["simple"]): "hello"}), relationships_obj, RDFFormat.turtle.value)
    rdf_response = Response(content=rdf, media_type="text/plain").body.decode()
    g = Graph()
    g.parse(data=rdf_response, format="turtle")
    assert (subj, URIRef(ex["simple"]), Literal("hello")) in g


def test_add_triples_with_list(rdf_client):
    relationships_obj = json.dumps({"relationships": []})
    rdf = rdf_client.json_to_rdf(
        make_json({str(ex["fruit"]): ["apple", "banana"]}), relationships_obj, RDFFormat.turtle.value
    )
    rdf_response = Response(content=rdf, media_type="text/plain").body.decode()
    g = Graph()
    g.parse(data=rdf_response, format="turtle")
    assert (subj, URIRef(ex["fruit"]), Literal("apple")) in g
    assert (subj, URIRef(ex["fruit"]), Literal("banana")) in g


def test_add_triples_with_nested_dict(rdf_client):
    relationships_obj = json.dumps({"relationships": []})
    rdf = rdf_client.json_to_rdf(
        make_json({str(ex["outer_inner"]): "deep_value"}), relationships_obj, RDFFormat.turtle.value
    )
    rdf_response = Response(content=rdf, media_type="text/plain").body.decode()
    g = Graph()
    g.parse(data=rdf_response, format="turtle")
    assert (subj, URIRef(ex["outer_inner"]), Literal("deep_value")) in g


def test_add_triples_with_acm_prefix(rdf_client):
    relationships_obj = json.dumps({"relationships": []})
    rdf = rdf_client.json_to_rdf(make_json({"acm_clearance": "TopSecret"}), relationships_obj, RDFFormat.turtle.value)
    rdf_response = Response(content=rdf, media_type="text/plain").body.decode()
    g = Graph()
    g.parse(data=rdf_response, format="turtle")
    assert (subj, URIRef(acm["clearance"]), Literal("TopSecret")) in g


def test_unsupported_format_raises_http_exception(rdf_client):
    relationships_obj = json.dumps({"relationships": []})
    with pytest.raises(HTTPException) as excinfo:
        rdf_client.json_to_rdf(json.dumps({"data": [{"guideId": "test"}]}), relationships_obj, "unsupported")
    assert excinfo.value.status_code == 400


def test_missing_data_raises_http_exception(rdf_client):
    relationships_obj = json.dumps({"relationships": []})
    with pytest.raises(HTTPException) as excinfo:
        rdf_client.json_to_rdf(json.dumps({"other": []}), relationships_obj, RDFFormat.turtle.value)
    assert excinfo.value.status_code == 400


def test_missing_guide_id_raises_http_exception(rdf_client):
    relationships_obj = json.dumps({"relationships": []})
    with pytest.raises(HTTPException) as excinfo:
        rdf_client.json_to_rdf(json.dumps({"data": [{}]}), relationships_obj, RDFFormat.turtle.value)
    assert excinfo.value.status_code == 400


def test_get_predicate_acm(rdf_client):
    acm_ns = Namespace("http://example.org/")

    pred = rdf_client.get_predicate("acm_name", acm_ns)
    assert str(pred) == "http://example.org/name"


def test_get_predicate_custom_uri(rdf_client):
    acm_ns = type("Namespace", (), {})()
    pred = rdf_client.get_predicate("custom_predicate", acm_ns)
    assert isinstance(pred, URIRef)
    assert str(pred) == "custom_predicate"


def test_add_triples_simple_literal(rdf_client):
    g = Graph()
    subj = URIRef("http://example.org/subject")
    rdf_client.add_triples(g, subj, "value", acm_ns=type("NS", (), {})())
    # should create a triple
    triples = list(g)
    assert len(triples) == 1
    assert triples[0][0] == subj
    assert isinstance(triples[0][2], Literal)


def test_add_triples_list_and_dict(rdf_client):
    g = Graph()
    subj = URIRef("http://example.org/subject")
    acm_ns = type("NS", (), {})()
    obj = {"nested": [1, 2, 3], "other": "val"}
    rdf_client.add_triples(g, subj, obj, acm_ns)
    triples = list(g)
    assert len(triples) == 4  # 3 list items + 1 string
    # check one of the list literals exists
    literals = [t[2] for t in triples]
    assert Literal(1) in literals
    assert Literal("val") in literals


def test_present_relationships_creates_triples(rdf_client):
    g = Graph()
    oms_ns = Namespace("http://example.org/oms")
    acm_ns = Namespace("http://example.org/acm")
    # fake relationship JSON
    rel_obj = json.dumps({"data": [{"id": "rel1", "name": "relationship_name", "values": [10, 20]}]})
    rdf_client.present_relationships(rel_obj, g, oms_ns, acm_ns)
    triples = list(g)
    # Check type triple for relationship exists
    type_triples = [t for t in triples if t[1] == RDF.type]
    assert any(str(t[0]).endswith("rel1") for t in type_triples)


def test_get_rdf_from_id_success(rdf_client):
    mock_crud = MagicMock(spec=OmsCrudTool)

    # mock node return
    node_data = MagicMock()
    node_data.data = [MagicMock(id="node1", guideId="g1")]
    node_data.model_dump_json.return_value = json.dumps(
        {"data": [{"id": "node1", "guideId": "g1", "name": "node_name"}]}
    )

    # mock relationships return
    rel_data = MagicMock()
    rel_data.model_dump_json.return_value = json.dumps({"data": [{"id": "rel1", "name": "rel_name"}]})

    mock_crud.get_nodes.return_value = node_data
    mock_crud.get_relationships.return_value = rel_data

    # patch json_to_rdf to avoid actual RDF generation
    rdf_client.json_to_rdf = MagicMock(return_value="RDF_STRING")

    result = rdf_client.get_rdf_from_id("g1", RDFFormat.turtle, mock_crud)
    assert result == "RDF_STRING"
    mock_crud.get_nodes.assert_called_once()
    mock_crud.get_relationships.assert_called_once()
    rdf_client.json_to_rdf.assert_called_once()


def test_get_rdf_from_id_handles_exception(rdf_client):
    mock_crud = MagicMock(spec=OmsCrudTool)
    mock_crud.get_nodes.side_effect = ValueError("Boom")
    result = rdf_client.get_rdf_from_id("g1", RDFFormat.turtle, mock_crud)
    assert result is None
