"""Tests for the NlpSensemakerController"""

from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM

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

mock_client = MockCoreNlpClient({}, SETTINGS.corenlp_host)
mock_client.set_response(mock_response_long_text)

findings = service.run_nlp(acm=DEFAULT_ACM, nlp_reader=reader, source_id=source_id, corenlp_client=mock_client)


def test_run_nlp():
    """Tests just running the business logic"""
    assert findings["ner_entities"]
    assert findings["document_entity"]
    assert findings["ner_relationships"]
    assert findings["document_relationships"]
    assert len(findings["document_relationships"]) == len(findings["ner_entities"])
    assert findings["document_entity"]["document_id"] == doc_id


@pytest.mark.integration
def test_submit_findings_to_postgis():
    """Tests submitting findings to postgis"""
    acm = DEFAULT_ACM
    execution_time = utcnow_with_timezone()
    result = service.submit_findings_to_postgis(acm=acm, findings=findings, execution_time=execution_time)
    assert result


def test_submit_findings_to_oms():
    """Not implemented: tests submitting findings to OMS"""
    assert True
