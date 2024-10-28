"""Tests for the "NLP" router."""

from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from oms_sdk import DEFAULT_ACM
from sqlalchemy.orm import Session

from oms_sensemaking.api.schemas.nlp import NlpRequest, NlpResponse
from oms_sensemaking.config import SETTINGS
from tests.nlp.mock_corenlp_client import MockCoreNlpClient
from tests.nlp.mock_responses import mock_response_short_text_str

test_source_id = "sensemaking-test"
test_text = "The quick brown fox jumps over the lazy dog."


@pytest.fixture
def mock_db(db: Session) -> Iterator[Session]:
    yield db


def test_extract_entities_and_relationships(client: TestClient, mock_db: Session, mocker, mock_source):
    # Creating mock corenlp client and using mocker.patch to put it in place of the real client
    mock_client = MockCoreNlpClient({}, SETTINGS.corenlp_localhost)
    mock_client.set_response(mock_response_short_text_str)
    mocker.patch("oms_sensemaking.api.routers.nlp.corenlp_client", mock_client)

    response: Response = client.post(
        "/nlp",
        json=NlpRequest(acm=DEFAULT_ACM, source_id=mock_source.id, text=test_text).model_dump(),
    )
    assert response.status_code == 200

    response: NlpResponse = NlpResponse(**response.json())
    assert response.acm == DEFAULT_ACM
    assert response.source_id == mock_source.id
    assert response.findings["document_entity"]["value"] == test_text
    assert len(response.findings["ner_entities"]) == len(response.findings["document_relationships"])


def test_invalid_source_id(client: TestClient, mock_db: Session, mocker, mock_source):
    mock_client = MockCoreNlpClient({}, SETTINGS.corenlp_localhost)
    mock_client.set_response(mock_response_short_text_str)
    mocker.patch("oms_sensemaking.api.routers.nlp.corenlp_client", mock_client)
    invalid_uuid = "5cb1dfa5-e1e8-400e-a148-d0df60e3ba9d"

    response: Response = client.post(
        "/nlp",
        json=NlpRequest(acm=DEFAULT_ACM, source_id=invalid_uuid, text=test_text).model_dump(),
    )
    assert response.status_code == 404
