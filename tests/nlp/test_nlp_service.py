"""Tests for the NlpSensemakerController"""

from typing import Iterator
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from sqlalchemy.orm import Session

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.models.base import utcnow_with_timezone
from oms_sensemaking.nlp.nlp_service import NlpService, NlpStringReader

from .mock_corenlp_client import MockCoreNlpClient
from .mock_responses import mock_response_long_text

service = NlpService()
doc_id = str(uuid4())
source_id = str(uuid4())
sample_text = (
    "EU rejects German call to boycott British lamb. Peter Blackburn BRUSSELS 1996-08-22 "
    "The European Commission said on Thursday it disagreed with German advice to consumers "
    "to shun British lamb until scientists determine whether mad cow disease can be transmitted"
    " to sheep. Germany's representative to the European Union's veterinary committee Werner Zwingmann"
    " said on Wednesday consumers should buy sheepmeat from countries other than Britain until the "
    "scientific advice was clearer."
)
reader = NlpStringReader(text=sample_text, document_id=doc_id)

mock_corenlp_client = MockCoreNlpClient({}, SETTINGS.corenlp_host)
mock_corenlp_client.set_response(mock_response_long_text)

mock_findings = service.run_nlp(nlp_reader=reader, corenlp_client=mock_corenlp_client)


@pytest.fixture
def mock_db(db: Session) -> Iterator[Session]:
    yield db


def test_run_service(mock_db):
    result = service.run_service(
        acm=DEFAULT_ACM, nlp_reader=reader, source_id=source_id, corenlp_client=mock_corenlp_client
    )
    assert result


def test_run_nlp(mock_db):
    """Tests just running the business logic"""
    assert mock_findings["ner_entities"]
    assert mock_findings["document_entity"]
    assert mock_findings["ner_relationships"]
    assert mock_findings["document_relationships"]
    assert len(mock_findings["document_relationships"]) == len(mock_findings["ner_entities"])
    assert mock_findings["document_entity"]["document_id"] == doc_id


def test_submit_findings_to_postgis(mock_db):
    """Tests submitting mocked findings to postgis"""
    acm = DEFAULT_ACM
    execution_time = utcnow_with_timezone()

    # First check if it runs with no problems
    service.submit_findings_to_postgis(acm=acm, findings=mock_findings, execution_time=execution_time)

    # Check the db for the posted findings
    results = service.get_all_findings_from_postgis()
    for finding in results:
        assert finding.finding_data == mock_findings


def test_submit_findings_to_oms(mock_db):
    """Not implemented: tests submitting findings to OMS"""
    service.submit_findings_to_oms(findings=mock_findings, source_id=source_id)
    # TODO: Get the findings from OMS and verify that they are correct
    pytest.skip("Skipping because this function is not completed yet.")
