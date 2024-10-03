"""Tests for the "NLP" router."""

from fastapi.testclient import TestClient
from httpx import Response
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.api.schemas.nlp import NlpRequest, NlpResponse

test_source_id = "sensemaking-test"
test_text = "The quick brown fox jumps over the lazy dog."


def test_extract_entities_and_relationships(client: TestClient):
    response: Response = client.post(
        "/nlp",
        json=NlpRequest(acm=DEFAULT_ACM, source_id=test_source_id, text=test_text).model_dump(),
    )
    assert response.status_code == 200

    response: NlpResponse = NlpResponse(**response.json())
    assert response.acm == DEFAULT_ACM
    assert response.source_id == test_source_id
    assert response.findings["document_entity"]["text"] == test_text
    assert len(response.findings["ner_entities"]) == len(response.findings["document_relationships"])
