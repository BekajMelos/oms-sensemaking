"""Tests for the "NLP" router."""
from fastapi.testclient import TestClient
from httpx import Response
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.api.schemas.nlp import NlpRequest, NlpResponse


def test_extract_entities_and_relationships(client: TestClient):
    response: Response = client.post(
        "/nlp",
        json=NlpRequest(
            acm=DEFAULT_ACM,
            text="The quick brown fox jumps over the lazy dog."
        ).model_dump()
    )
    assert response.status_code == 200

    response: NlpResponse = NlpResponse(**response.json())
    assert response.acm == DEFAULT_ACM
    # TODO: verify the rest of the response is valid
